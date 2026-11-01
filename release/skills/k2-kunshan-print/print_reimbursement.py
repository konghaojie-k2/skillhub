#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
k2-kunshan-print Skill
昆山出差报销自动化处理 v2.0

基于实际填报经验改进：
1. 以实际发票/车票日期构建日期列，而非出差申请日期
2. 补贴按实际首末程交通工具时间计算（12:00分界）
3. 支持图片 OCR 读取出差申请
4. 住宿读取价税合计
5. 区分火车票退票与正常车票
6. 动态识别出发/到达站点
7. 项目信息支持手动覆盖
"""

import os
import sys
import re
import pdfplumber
import openpyxl
import requests
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 配置
DEFAULT_FOLDER = r"C:\Users\17625\Desktop\新建文件夹"
PRINTER_NAME = "NPI9D671C (HP LaserJet Pro MFP M226dw)"
SKILL_DIR = Path(__file__).parent
TEMPLATE_PATH = SKILL_DIR / "attachments" / "差旅费报销单模板.xlsx"

# Ollama OCR 配置
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_VISION_MODEL = "glm-ocr:bf16"

# 可选公司列表
COMPANIES = {
    'kunshan': '昆山工业大数据创新中心有限公司',
    'suzhou': '昆仑智汇数据科技（苏州）有限公司',
    'default': '昆山工业大数据创新中心有限公司'
}

# 自然语言公司识别关键词
COMPANY_KEYWORDS = {
    'kunshan': ['昆山', '大数据', '创新中心'],
    'suzhou': ['苏州', '智汇', '昆仑']
}

# 补贴标准
SUBSIDY_HALF_DAY = 90
SUBSIDY_FULL_DAY = 180

# Excel 起始列（D=4, E=5, F=6...）
START_COL = 4


class Invoice:
    """发票信息类"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.date: Optional[datetime] = None
        self.amount: float = 0.0
        self.type: str = ""  # train, taxi, hotel, other
        self.info: Dict = {}

    def __repr__(self):
        return f"Invoice({self.file_name}, {self.date}, {self.amount}, {self.type})"


class TravelApplication:
    """出差申请类"""
    def __init__(self):
        self.destination: str = ""
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.days: float = 0.0
        self.project: str = ""
        self.applicant: str = ""

    def __repr__(self):
        return f"TravelApp({self.destination}, {self.start_date}, {self.end_date}, {self.days}天)"


def parse_company_from_text(text: str) -> str:
    """从自然语言文本中解析公司选择"""
    if not text:
        return 'default'
    text_lower = text.lower()
    for keyword in COMPANY_KEYWORDS['suzhou']:
        if keyword in text_lower:
            return 'suzhou'
    for keyword in COMPANY_KEYWORDS['kunshan']:
        if keyword in text_lower:
            return 'kunshan'
    return 'default'


def extract_destination_from_text(text: str) -> str:
    """从出差申请文本中提取目的地"""
    dest_patterns = [
        r'出差地点\s*[：:]\s*(\w+)',
        r'目的地\s*[：:]\s*(\w+)',
        r'前往\s*(\w+)\s*出差',
        r'(\w+)\s*出差申请',
    ]
    for pattern in dest_patterns:
        match = re.search(pattern, text)
        if match:
            destination = match.group(1)
            destination = re.sub(r'市$', '', destination)
            return destination
    return ''


def extract_dates_from_text(text: str) -> Tuple[Optional[datetime], Optional[datetime], float]:
    """从出差申请文本中提取日期和天数"""
    start_date = None
    end_date = None
    days = 0.0

    start_match = re.search(r'开始时间\s*[：:]\s*(\d{4}[-/年]\d{2}[-/月]\d{2}[-日]?)', text)
    if start_match:
        date_str = re.sub(r'[年/]', '-', start_match.group(1)).replace('日', '')
        try:
            start_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass

    end_match = re.search(r'结束时间\s*[：:]\s*(\d{4}[-/年]\d{2}[-/月]\d{2}[-日]?)', text)
    if end_match:
        date_str = re.sub(r'[年/]', '-', end_match.group(1)).replace('日', '')
        try:
            end_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass

    days_match = re.search(r'时长\s*[（(]?天\s*[)）]?\s*[：:]\s*([\d.]+)', text)
    if days_match:
        days = float(days_match.group(1))
    else:
        if start_date and end_date:
            days = (end_date - start_date).days + 1

    return start_date, end_date, days


def extract_project_from_text(text: str) -> str:
    """提取项目编号与名称"""
    match = re.search(r'项目编号与名称\s*[：:]\s*([^\n]+)', text)
    if match:
        return match.group(1).strip()
    match = re.search(r'项目[编号名称]*\s*[：:]\s*([^\n]+)', text)
    if match:
        return match.group(1).strip()
    return ''


def ocr_image(file_path: str) -> str:
    """使用本地 Ollama GLM OCR 识别图片"""
    try:
        with open(file_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "model": OLLAMA_VISION_MODEL,
            "prompt": "请识别图片中的所有文字，保持原始排版，直接输出纯文本，不要任何解释。",
            "images": [image_b64],
            "stream": False
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        text = resp.json().get("response", "")
        return text
    except Exception as e:
        print(f"  [WARN] Ollama OCR 失败：{e}")
        return ""


def read_travel_application(folder: str) -> TravelApplication:
    """读取出差申请文件（支持 PDF 和图片 OCR）"""
    print("\n" + "=" * 60)
    print("读取出差申请")
    print("=" * 60)

    app = TravelApplication()

    for file_name in os.listdir(folder):
        if any(k in file_name for k in ['出差', '申请', '审批']) and file_name.endswith(('.pdf', '.png', '.jpg', '.jpeg')):
            file_path = os.path.join(folder, file_name)
            print(f"\n文件：{file_name}")

            try:
                text = ""
                if file_name.endswith('.pdf'):
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                else:
                    text = ocr_image(file_path)
                    if text:
                        print(f"  [OK] OCR 识别成功")
                    else:
                        print(f"  [WARN] OCR 未识别到文字（请确保 Ollama 已启动且模型 {OLLAMA_VISION_MODEL} 可用）")

                if text:
                    dest = extract_destination_from_text(text)
                    if dest:
                        app.destination = dest
                        print(f"  目的地：{dest}")

                    start, end, days = extract_dates_from_text(text)
                    if start:
                        app.start_date = start
                        print(f"  开始日期：{start.strftime('%Y-%m-%d')}")
                    if end:
                        app.end_date = end
                        print(f"  结束日期：{end.strftime('%Y-%m-%d')}")
                    if days > 0:
                        app.days = days
                        print(f"  天数：{days}天")

                    project = extract_project_from_text(text)
                    if project:
                        app.project = project
                        print(f"  项目：{app.project}")

            except Exception as e:
                print(f"  读取失败：{e}")

    if not app.destination:
        print("\n[INFO] 未从出差申请中提取到目的地，将使用火车票信息")

    return app


def check_necessary_files(folder: str) -> Dict[str, bool]:
    """检查必要文件是否齐全"""
    print("\n" + "=" * 60)
    print("检查必要文件")
    print("=" * 60)

    files = os.listdir(folder)

    pdf_files = [f for f in files if f.endswith('.pdf')]
    xlsx_files = [f for f in files if f.endswith('.xlsx') and '报销' in f]

    result = {
        'has_invoice': len(pdf_files) > 0,
        'has_travel_application': any('出差' in f or '申请' in f for f in files),
        'has_template': TEMPLATE_PATH.exists(),
        'pdf_count': len(pdf_files),
        'xlsx_count': len(xlsx_files)
    }

    print(f"\nPDF 文件：{len(pdf_files)} 个")
    print(f"Excel 文件：{len(xlsx_files)} 个")
    status = '[OK]' if result['has_template'] else '[MISSING]'
    print(f"报销单模板：{status}")

    if not result['has_invoice']:
        print("\n[WARN] 未找到 PDF 发票文件！")
    if not result['has_template']:
        print(f"\n[WARN] 报销单模板不存在：{TEMPLATE_PATH}")

    return result


def read_invoice_info(folder: str) -> List[Invoice]:
    """读取所有发票信息"""
    print("\n" + "=" * 60)
    print("读取发票信息")
    print("=" * 60)

    invoices = []

    for file_name in os.listdir(folder):
        if not file_name.endswith('.pdf'):
            continue

        file_path = os.path.join(folder, file_name)
        invoice = Invoice(file_path)

        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    # 识别火车票
                    if '铁路' in text or ('车票' in text and any(c in text for c in ['G', 'D', 'C', 'K', 'T', 'Z']) and '站' in text):
                        invoice.type = 'train'

                        # 提取日期和时间
                        date_time_match = re.search(r'(\d{4}年\d{2}月\d{2}日)\s+(\d{2}:\d{2})', text)
                        if date_time_match:
                            date_str = date_time_match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                            try:
                                invoice.date = datetime.strptime(date_str, '%Y-%m-%d')
                                invoice.info['time_str'] = date_time_match.group(2)
                            except:
                                pass
                        else:
                            date_match = re.search(r'(\d{4}年\d{2}月\d{2}日)', text)
                            if date_match:
                                date_str = date_match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                                try:
                                    invoice.date = datetime.strptime(date_str, '%Y-%m-%d')
                                except:
                                    pass

                        # 识别退票
                        if '退票' in text or '退票费' in text:
                            invoice.info['is_refund'] = True

                        # 提取站点
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if re.match(r'^\S+?\s+[GDKTCZ]\d+\s+\S+$', line.strip()):
                                parts = line.strip().split()
                                if len(parts) >= 3:
                                    invoice.info['departure'] = parts[0]
                                    invoice.info['arrival'] = parts[2]
                                    break

                        # 提取金额
                        amount_match = re.search(r'[￥¥](\d+\.?\d*)', text)
                        if amount_match:
                            invoice.amount = float(amount_match.group(1))

                        print(f"[OK] {file_name}")
                        tag = "【退票】" if invoice.info.get('is_refund') else ""
                        print(f"     类型：{invoice.type}{tag}, 日期：{invoice.date}, 金额：{invoice.amount}, "
                              f"站点：{invoice.info.get('departure', '')}-{invoice.info.get('arrival', '')}, "
                              f"时间：{invoice.info.get('time_str', '')}")

                    # 识别滴滴相关文件（行程单 或 电子发票）
                    elif '滴滴' in text:
                        invoice.type = 'taxi'

                        # 行程报销单
                        if '行程单' in text or '行程报销单' in text:
                            total_match = re.search(r'合计\s*(\d+\.?\d*)\s*元', text)
                            if total_match:
                                invoice.amount = float(total_match.group(1))
                            # 提取日期：优先"行程起止日期：YYYY-MM-DD 至 YYYY-MM-DD"里的开始日期
                            trip_range_match = re.search(r'行程起止日期\s*[：:]\s*(\d{4}-\d{2}-\d{2})\s*至\s*(\d{4}-\d{2}-\d{2})', text)
                            if trip_range_match:
                                try:
                                    invoice.date = datetime.strptime(trip_range_match.group(1), '%Y-%m-%d')
                                except:
                                    pass
                            else:
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                                if date_match:
                                    try:
                                        invoice.date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                    except:
                                        pass

                        # 滴滴电子发票
                        elif '发票号码' in text or '电子发票' in text or '增值税电子普通发票' in text:
                            amount_match = re.search(r'[￥¥](\d+\.?\d*)', text)
                            if amount_match:
                                invoice.amount = float(amount_match.group(1))
                            # 优先提取服务/行程日期
                            date_match = re.search(r'(?:服务日期|行程日期|乘车日期|预约时间)\s*[：:]\s*(\d{4}-\d{2}-\d{2})', text)
                            if not date_match:
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                            if date_match:
                                try:
                                    invoice.date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                except:
                                    pass
                            # 标记为电子发票，金额计算时去重
                            invoice.info['is_einvoice'] = True

                        print(f"[OK] {file_name}")
                        tag = "[电子发票]" if invoice.info.get('is_einvoice') else ""
                        print(f"     类型：{invoice.type}{tag}, 日期：{invoice.date}, 金额：{invoice.amount}")

                    # 识别住宿发票/结账单
                    elif any(k in text for k in ['住宿', '酒店', '结账单', '汉庭', '假日']):
                        invoice.type = 'hotel'

                        # 提取金额：优先价税合计（小写）
                        amount_match = re.search(r'（小写）\s*[￥¥](\d+\.?\d*)', text)
                        if not amount_match:
                            amount_match = re.search(r'价税合计.*?[￥¥](\d+\.?\d*)', text, re.DOTALL)
                        if not amount_match:
                            amount_match = re.search(r'消费合计\s+(\d+\.?\d*)', text)
                        if not amount_match:
                            amount_match = re.search(r'付款合计\s+(\d+\.?\d*)', text)
                        if not amount_match:
                            amount_match = re.search(r'[￥¥](\d+\.?\d*)', text)
                        if amount_match:
                            invoice.amount = float(amount_match.group(1))

                        # 提取日期：优先入住日期
                        checkin_match = re.search(r'入住日期\s*[：:]\s*(\d{4}-\d{2}-\d{2})', text)
                        if checkin_match:
                            try:
                                invoice.date = datetime.strptime(checkin_match.group(1), '%Y-%m-%d')
                                checkout_match = re.search(r'离店日期\s*[：:]\s*(\d{4}-\d{2}-\d{2})', text)
                                if checkout_match:
                                    invoice.info['checkout_date'] = datetime.strptime(checkout_match.group(1), '%Y-%m-%d')
                            except:
                                pass
                        else:
                            # 对于没有明确入住日期的文件（如纯电子发票），尝试找住宿服务日期
                            service_match = re.search(r'(?:住宿服务|入住|离店).*?(\d{4}-\d{2}-\d{2})', text)
                            if service_match:
                                try:
                                    invoice.date = datetime.strptime(service_match.group(1), '%Y-%m-%d')
                                except:
                                    pass
                            # 不再从电子发票中随意提取开票日期，避免与结账单日期不一致导致重复计算

                        print(f"[OK] {file_name}")
                        checkout_str = invoice.info.get('checkout_date', '')
                        if checkout_str:
                            checkout_str = f", 离店：{checkout_str.strftime('%Y-%m-%d')}"
                        print(f"     类型：{invoice.type}, 日期：{invoice.date}, 金额：{invoice.amount}{checkout_str}")

                    if invoice.type and (invoice.amount > 0 or invoice.info.get('is_refund')):
                        invoices.append(invoice)
                        break

        except Exception as e:
            print(f"[ERROR] 读取失败 {file_name}: {e}")

    # 住宿标记：给有 checkout_date 的标记为 primary（金额计算优先使用）
    hotel_invoices = [inv for inv in invoices if inv.type == 'hotel']
    if hotel_invoices:
        for inv in hotel_invoices:
            if inv.info.get('checkout_date'):
                inv.info['is_primary'] = True

    return invoices


def read_didi_trips(folder: str) -> Tuple[Dict[str, float], Dict[str, List[Tuple[str, float]]]]:
    """读取滴滴行程单明细，按日期汇总并保留时间信息"""
    print("\n" + "=" * 60)
    print("读取滴滴行程明细")
    print("=" * 60)

    trips_by_date = {}
    trips_detail = {}

    for file_name in os.listdir(folder):
        if '滴滴' in file_name and '行程报销单' in file_name and file_name.endswith('.pdf'):
            file_path = os.path.join(folder, file_name)
            print(f"\n文件：{file_name}")

            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            lines = text.split('\n')
                            for line in lines:
                                match = re.search(r'(\d{2}-\d{2})\s+(\d{2}:\d{2})', line)
                                # 金额可能是行尾最后一个数字，不一定带"元"字
                                amount_match = re.search(r'(\d+\.?\d*)\s*$', line)

                                if match and amount_match:
                                    date_str = match.group(1)
                                    time_str = match.group(2)
                                    amount = float(amount_match.group(1))
                                    full_date = f"2026-{date_str}"

                                    trips_by_date[full_date] = trips_by_date.get(full_date, 0) + amount
                                    trips_detail.setdefault(full_date, []).append((time_str, amount))

                                    print(f"  {full_date} {time_str}: {amount:.2f}元")

            except Exception as e:
                print(f"  读取失败：{e}")

    print(f"\n按日期汇总：")
    for date in sorted(trips_by_date.keys()):
        print(f"  {date}: {trips_by_date[date]:.2f}元")

    return trips_by_date, trips_detail


def fill_reimbursement_form(folder: str, invoices: List[Invoice], subsidy: float,
                            travel_app: TravelApplication,
                            didi_trips: Optional[Dict[str, float]] = None,
                            didi_detail: Optional[Dict[str, List[Tuple[str, float]]]] = None,
                            company: str = 'kunshan',
                            project_override: Optional[str] = None):
    """填写报销单（以实际发票日期为准）"""
    print("\n" + "=" * 60)
    print("填写报销单")
    print("=" * 60)

    if not TEMPLATE_PATH.exists():
        print(f"[ERROR] 模板不存在：{TEMPLATE_PATH}")
        return None

    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    sheet = wb.active

    company_name = COMPANIES.get(company, COMPANIES['default'])
    print(f"  选择公司：{company_name}")

    # ========== 1. 收集所有日期并构建日期列 ==========
    all_dates_set = set()
    date_to_trains = {}
    date_to_taxi = {}

    for inv in invoices:
        if inv.date:
            all_dates_set.add(inv.date)
            if inv.type == 'train' and not inv.info.get('is_refund'):
                date_to_trains.setdefault(inv.date, []).append(inv)
            # taxi 金额不再从 invoices 累加（避免电子发票和行程单重复），只使用 didi_trips 明细


    didi_trips = didi_trips or {}
    didi_detail = didi_detail or {}
    for date_str, amount in didi_trips.items():
        trip_date = datetime.strptime(date_str, '%Y-%m-%d')
        all_dates_set.add(trip_date)
        date_to_taxi[trip_date] = date_to_taxi.get(trip_date, 0) + amount

    # 如果没有滴滴行程单明细，fallback 使用 taxi PDF 的金额（按日期去重）
    if not date_to_taxi:
        # 优先使用行程报销单（有明确日期），避免与电子发票重复
        non_einvoice_taxis = [inv for inv in invoices if inv.type == 'taxi' and inv.date and not inv.info.get('is_einvoice')]
        if non_einvoice_taxis:
            for inv in non_einvoice_taxis:
                date_to_taxi[inv.date] = date_to_taxi.get(inv.date, 0) + inv.amount
        else:
            # 没有行程报销单时，使用电子发票
            for inv in invoices:
                if inv.type == 'taxi' and inv.date and inv.info.get('is_einvoice'):
                    date_to_taxi[inv.date] = date_to_taxi.get(inv.date, 0) + inv.amount

    sorted_dates = sorted(all_dates_set)
    if not sorted_dates:
        print("[ERROR] 未能从发票中提取到有效日期")
        return None

    print(f"  发票日期范围：{sorted_dates[0].strftime('%Y-%m-%d')} ~ {sorted_dates[-1].strftime('%Y-%m-%d')}")
    print(f"  共 {len(sorted_dates)} 个日期列")

    max_cols = 3  # 模板固定 3 列（D, E, F）
    if len(sorted_dates) > max_cols:
        print(f"[WARN] 日期列超出模板限制（{max_cols}列），多余日期将合并到最后一列")

    # ========== 2. 确定实际出差范围（用于补贴计算） ==========
    actual_start = None
    actual_start_time = None
    actual_end = None
    actual_end_time = None

    normal_trains = [inv for inv in invoices if inv.type == 'train' and not inv.info.get('is_refund') and inv.date]
    normal_trains.sort(key=lambda x: x.date)

    if normal_trains:
        actual_start = normal_trains[0].date
        actual_start_time = normal_trains[0].info.get('time_str')
        actual_end = normal_trains[-1].date
        actual_end_time = normal_trains[-1].info.get('time_str')

    for date_str, details in didi_detail.items():
        d = datetime.strptime(date_str, '%Y-%m-%d')
        times = [t for t, _ in details]
        if times:
            earliest_time = min(times)
            latest_time = max(times)
            if actual_start is None or d < actual_start:
                actual_start = d
                actual_start_time = earliest_time
            if actual_end is None or d > actual_end:
                actual_end = d
                actual_end_time = latest_time
            if d == actual_start and (not actual_start_time or earliest_time < actual_start_time):
                actual_start_time = earliest_time
            if d == actual_end and (not actual_end_time or latest_time > actual_end_time):
                actual_end_time = latest_time

    for inv in invoices:
        if inv.type == 'hotel' and inv.info.get('checkout_date'):
            checkout = inv.info['checkout_date']
            if actual_end is None or checkout > actual_end:
                actual_end = checkout

    if actual_start and actual_end:
        print(f"  实际出差范围：{actual_start.strftime('%Y-%m-%d')} ~ {actual_end.strftime('%Y-%m-%d')}")
        print(f"  首程时间：{actual_start_time or '未知'}, 末程时间：{actual_end_time or '未知'}")

    # ========== 3. 计算补贴 ==========
    subsidy_map = {}
    for d in sorted_dates:
        if actual_start is None or actual_end is None:
            subsidy_map[d] = SUBSIDY_FULL_DAY
            continue

        if d < actual_start or d > actual_end:
            subsidy_map[d] = 0
        elif d == actual_start == actual_end:
            if actual_start_time and actual_start_time >= '12:00':
                subsidy_map[d] = SUBSIDY_HALF_DAY
            else:
                subsidy_map[d] = SUBSIDY_FULL_DAY
        elif d == actual_start:
            if actual_start_time and actual_start_time >= '12:00':
                subsidy_map[d] = SUBSIDY_HALF_DAY
            else:
                subsidy_map[d] = SUBSIDY_FULL_DAY
        elif d == actual_end:
            if actual_end_time and actual_end_time > '12:00':
                subsidy_map[d] = SUBSIDY_FULL_DAY
            else:
                subsidy_map[d] = SUBSIDY_HALF_DAY
        else:
            subsidy_map[d] = SUBSIDY_FULL_DAY

    # ========== 4. 提取出发/到达站点 ==========
    first_train = normal_trains[0] if normal_trains else None
    last_train = normal_trains[-1] if normal_trains else None

    departure_start = first_train.info.get('departure', '苏州') if first_train else '苏州'
    arrival_start = first_train.info.get('arrival', '合肥') if first_train else '合肥'
    departure_end = last_train.info.get('departure', arrival_start) if last_train else arrival_start
    arrival_end = last_train.info.get('arrival', departure_start) if last_train else departure_start

    # ========== 5. 清空并填写基本信息 ==========
    date_cols = [START_COL + i for i in range(max_cols)]
    for col in date_cols:
        sheet.cell(row=17, column=col, value=None)
        for r in range(18, 29):
            sheet.cell(row=r, column=col, value=None)

    sheet.cell(row=4, column=4, value=company_name)
    sheet.cell(row=6, column=6, value=datetime.now())
    sheet.cell(row=10, column=2, value='AI Demura')

    project_name = project_override or travel_app.project or 'PU2026FL 冯亮公共售前'
    sheet.cell(row=14, column=7, value=project_name)
    sheet.cell(row=14, column=11, value=len(invoices) + 1)
    print(f"  + 填写基本信息（公司：{company_name}，项目：{project_name}）")

    # ========== 6. 填写日期列 ==========
    for i, d in enumerate(sorted_dates[:max_cols]):
        col = date_cols[i]
        sheet.cell(row=17, column=col, value=d)
    print("  + 填写日期")

    # ========== 7. 填写出发/到达地点 ==========
    for i, d in enumerate(sorted_dates[:max_cols]):
        col = date_cols[i]
        if first_train and d == first_train.date:
            sheet.cell(row=18, column=col, value=departure_start)
            sheet.cell(row=19, column=col, value=arrival_start)
        if last_train and d == last_train.date and len(normal_trains) > 1:
            sheet.cell(row=18, column=col, value=departure_end)
            sheet.cell(row=19, column=col, value=arrival_end)
    print(f"  + 填写出发/到达地点（{departure_start} -> {arrival_start}，返程 {departure_end} -> {arrival_end}）")

    # ========== 8. 按日期填写各项费用 ==========
    def get_col_for_date(d: datetime) -> int:
        if d in sorted_dates[:max_cols]:
            return date_cols[sorted_dates[:max_cols].index(d)]
        return date_cols[-1]

    # 火车票
    train_row = 21
    sheet.cell(row=train_row, column=2, value='火车票')
    for d in sorted_dates:
        trains = date_to_trains.get(d, [])
        if not trains:
            continue
        col = get_col_for_date(d)
        total = sum(inv.amount for inv in trains)
        current = sheet.cell(row=train_row, column=col).value or 0
        sheet.cell(row=train_row, column=col, value=current + total)
        print(f"  + 火车票 ({d.strftime('%m-%d')}): {total:.2f}元")

    # 退票费（填在其他费用行）
    refund_row = 25
    sheet.cell(row=refund_row, column=2, value='退票费')
    refund_invoices = [inv for inv in invoices if inv.type == 'train' and inv.info.get('is_refund')]
    for inv in refund_invoices:
        if inv.date:
            col = get_col_for_date(inv.date)
            current = sheet.cell(row=refund_row, column=col).value or 0
            sheet.cell(row=refund_row, column=col, value=current + inv.amount)
            print(f"  + 退票费 ({inv.date.strftime('%m-%d')}): {inv.amount:.2f}元")
    if refund_invoices:
        sheet.cell(row=refund_row, column=3, value='退票费')

    # 打车费
    taxi_row = 22
    sheet.cell(row=taxi_row, column=2, value='打车费')
    for d, amount in date_to_taxi.items():
        col = get_col_for_date(d)
        current = sheet.cell(row=taxi_row, column=col).value or 0
        sheet.cell(row=taxi_row, column=col, value=current + amount)
        print(f"  + 打车费 ({d.strftime('%m-%d')}): {amount:.2f}元")

    # 住宿费（填在最后一天的列）
    hotel_row = 23
    sheet.cell(row=hotel_row, column=2, value='住宿费')
    hotel_invoices = [inv for inv in invoices if inv.type == 'hotel']
    # 金额计算：优先使用 primary 住宿单据（结账单/入住单），避免电子发票重复计算
    primary_hotels = [inv for inv in hotel_invoices if inv.info.get('is_primary')]
    hotel_total = sum(inv.amount for inv in primary_hotels) if primary_hotels else sum(inv.amount for inv in hotel_invoices)
    if hotel_total > 0:
        last_col = date_cols[min(len(sorted_dates), max_cols) - 1]
        sheet.cell(row=hotel_row, column=last_col, value=hotel_total)
        print(f"  + 住宿费 ({hotel_total:.2f}元，填在最后日期列)")

    # 出差补助
    subsidy_row = 24
    sheet.cell(row=subsidy_row, column=2, value='出差补助')
    actual_subsidy = 0
    for i, d in enumerate(sorted_dates[:max_cols]):
        col = date_cols[i]
        val = subsidy_map.get(d, 0)
        sheet.cell(row=subsidy_row, column=col, value=val)
        actual_subsidy += val

    overflow_dates = sorted_dates[max_cols:]
    for d in overflow_dates:
        val = subsidy_map.get(d, 0)
        last_col = date_cols[-1]
        current = sheet.cell(row=subsidy_row, column=last_col).value or 0
        sheet.cell(row=subsidy_row, column=last_col, value=current + val)
        actual_subsidy += val

    print(f"  + 出差补助：{actual_subsidy}元")

    # ========== 9. 自动校验 ==========
    validate_reimbursement_form(
        sheet, invoices, date_cols, sorted_dates, subsidy_map,
        actual_start, actual_end, actual_start_time, actual_end_time,
        date_to_taxi, hotel_total, company_name, project_name
    )

    # ========== 10. 保存 ==========
    output_path = os.path.join(folder, f"差旅费报销单_{company_name}_{datetime.now().strftime('%Y%m%d')}_最终版.xlsx")
    wb.save(output_path)

    train_total = sum(inv.amount for inv in invoices if inv.type == 'train' and not inv.info.get('is_refund'))
    refund_total = sum(inv.amount for inv in invoices if inv.type == 'train' and inv.info.get('is_refund'))
    taxi_total = sum(date_to_taxi.values())
    grand_total = train_total + refund_total + taxi_total + hotel_total + actual_subsidy

    print(f"\n[OK] 报销单已保存：{output_path}")
    print(f"  火车票：{train_total:.2f} 元")
    if refund_total > 0:
        print(f"  退票费：{refund_total:.2f} 元")
    print(f"  打车费：{taxi_total:.2f} 元")
    print(f"  住宿费：{hotel_total:.2f} 元")
    print(f"  出差补助：{actual_subsidy:.2f} 元")
    print(f"  合计：{grand_total:.2f} 元")

    return output_path


def validate_reimbursement_form(sheet, invoices: List[Invoice], date_cols: List[int],
                                sorted_dates: List[datetime], subsidy_map: Dict[datetime, int],
                                actual_start: Optional[datetime], actual_end: Optional[datetime],
                                actual_start_time: Optional[str], actual_end_time: Optional[str],
                                date_to_taxi: Dict[datetime, float], hotel_total: float,
                                company_name: str, project_name: str):
    """自动校验报销单填写结果与原始发票数据的一致性"""
    print("\n" + "=" * 60)
    print("自动校验报销单")
    print("=" * 60)

    issues = []
    warnings = []
    ok_items = []

    def read_cell(row, col):
        v = sheet.cell(row=row, column=col).value
        if isinstance(v, datetime):
            return v.date() if hasattr(v, 'date') else v
        return v

    def num_val(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        return 0

    # ---- 1. 基本信息校验 ----
    if not company_name or company_name not in COMPANIES.values():
        issues.append("公司名称为空或不合法")
    else:
        ok_items.append(f"公司名称：{company_name}")

    if not project_name or project_name == 'PU2026FL 冯亮公共售前':
        warnings.append("项目信息可能为默认值，请核对是否为正确项目")
    else:
        ok_items.append(f"项目信息：{project_name}")

    purpose = read_cell(10, 2)
    if not purpose:
        warnings.append("B10 出差目的为空")
    else:
        ok_items.append(f"出差目的：{purpose}")

    # ---- 2. 日期列校验 ----
    excel_dates = []
    for col in date_cols:
        v = read_cell(17, col)
        if isinstance(v, datetime):
            excel_dates.append(v.date() if hasattr(v, 'date') else v)
        else:
            excel_dates.append(v)

    expected_dates = [d.date() if hasattr(d, 'date') else d for d in sorted_dates[:len(date_cols)]]
    if excel_dates[:len(expected_dates)] != expected_dates:
        issues.append(f"日期列不匹配：Excel={excel_dates[:len(expected_dates)]}，期望={expected_dates}")
    else:
        ok_items.append("日期列与实际发票日期一致")

    # ---- 3. 火车票校验 ----
    expected_train = sum(inv.amount for inv in invoices if inv.type == 'train' and not inv.info.get('is_refund'))
    excel_train = sum(num_val(read_cell(21, col)) for col in date_cols)
    if abs(excel_train - expected_train) > 0.01:
        issues.append(f"火车票金额不匹配：Excel={excel_train:.2f}，发票={expected_train:.2f}")
    else:
        ok_items.append("火车票金额正确")

    # 退票费校验
    expected_refund = sum(inv.amount for inv in invoices if inv.type == 'train' and inv.info.get('is_refund'))
    excel_refund = sum(num_val(read_cell(25, col)) for col in date_cols)
    if abs(excel_refund - expected_refund) > 0.01:
        issues.append(f"退票费金额不匹配：Excel={excel_refund:.2f}，发票={expected_refund:.2f}")
    else:
        ok_items.append("退票费金额正确且已单独列示")

    # 检查退票费是否混入火车票
    all_train_invoices = [inv for inv in invoices if inv.type == 'train']
    for inv in all_train_invoices:
        if inv.info.get('is_refund') and inv.date:
            for col in date_cols:
                d = read_cell(17, col)
                if d and hasattr(d, 'month') and d.month == inv.date.month and d.day == inv.date.day:
                    train_val = num_val(read_cell(21, col))
                    if abs(train_val - inv.amount) < 0.01 and not num_val(read_cell(25, col)):
                        issues.append(f"{inv.date.strftime('%m-%d')} 退票费 {inv.amount:.2f} 元可能混入了火车票")

    # ---- 4. 打车费校验 ----
    expected_taxi = sum(date_to_taxi.values())
    excel_taxi = sum(num_val(read_cell(22, col)) for col in date_cols)
    if abs(excel_taxi - expected_taxi) > 0.01:
        issues.append(f"打车费金额不匹配：Excel={excel_taxi:.2f}，发票={expected_taxi:.2f}")
    else:
        ok_items.append("打车费金额正确")

    # ---- 5. 住宿费校验 ----
    if hotel_total > 0:
        excel_hotel = sum(num_val(read_cell(23, col)) for col in date_cols)
        if abs(excel_hotel - hotel_total) > 0.01:
            issues.append(f"住宿费金额不匹配：Excel={excel_hotel:.2f}，发票={hotel_total:.2f}")
        else:
            last_filled_col = None
            for col in reversed(date_cols):
                if num_val(read_cell(23, col)) > 0:
                    last_filled_col = col
                    break
            if last_filled_col != date_cols[min(len(sorted_dates), len(date_cols)) - 1]:
                warnings.append("住宿费未填在最后一列日期")
            else:
                ok_items.append("住宿费金额正确且位置正确")

    # ---- 6. 补贴逻辑校验 ----
    subsidy_errors = False
    for i, d in enumerate(sorted_dates[:len(date_cols)]):
        col = date_cols[i]
        expected = subsidy_map.get(d, 0)
        actual = num_val(read_cell(24, col))
        if abs(actual - expected) > 0.01:
            issues.append(f"{d.strftime('%m-%d')} 补贴错误：Excel={actual}，应为 {expected}")
            subsidy_errors = True
    if not subsidy_errors:
        ok_items.append("补贴计算正确")

    # 异常检测：没有交通工具但有补贴的日期
    for i, d in enumerate(sorted_dates[:len(date_cols)]):
        col = date_cols[i]
        has_transport = False
        for row in [20, 21, 22]:
            if num_val(read_cell(row, col)) > 0:
                has_transport = True
                break
        sub = num_val(read_cell(24, col))
        if sub > 0 and not has_transport:
            # 排除中间正常休息日（跨多天出差时中间可能无交通但有补贴）
            if d == actual_start or d == actual_end:
                warnings.append(f"{d.strftime('%m-%d')} 是起止日但无交通工具记录，请确认是否漏填")
            else:
                issues.append(f"{d.strftime('%m-%d')} 有补贴 {sub} 元但无交通工具记录，可能为退票日误填补贴")

    # 首末程时间补贴规则复核
    if actual_start and actual_start_time:
        start_sub = subsidy_map.get(actual_start, 0)
        if actual_start_time >= '12:00' and start_sub != SUBSIDY_HALF_DAY:
            issues.append(f"首日出发时间 {actual_start_time} 晚于12:00，补贴应为 {SUBSIDY_HALF_DAY} 元")
        elif actual_start_time < '12:00' and start_sub != SUBSIDY_FULL_DAY:
            issues.append(f"首日出发时间 {actual_start_time} 早于12:00，补贴应为 {SUBSIDY_FULL_DAY} 元")

    if actual_end and actual_end_time:
        end_sub = subsidy_map.get(actual_end, 0)
        if actual_end_time > '12:00' and end_sub != SUBSIDY_FULL_DAY:
            issues.append(f"末日返程时间 {actual_end_time} 晚于12:00，补贴应为 {SUBSIDY_FULL_DAY} 元")
        elif actual_end_time <= '12:00' and end_sub != SUBSIDY_HALF_DAY:
            issues.append(f"末日返程时间 {actual_end_time} 早于等于12:00，补贴应为 {SUBSIDY_HALF_DAY} 元")

    # ---- 7. 发票张数校验 ----
    expected_count = len(invoices) + 1  # +1 是报销单本身？旧逻辑如此
    excel_count = read_cell(14, 11)
    if excel_count != expected_count:
        warnings.append(f"发票张数可能不匹配：Excel={excel_count}，实际发票数={len(invoices)}")
    else:
        ok_items.append("发票张数正确")

    # ---- 8. 合计公式校验（横向） ----
    for row in range(20, 29):
        row_sum = sum(num_val(read_cell(row, col)) for col in date_cols)
        k_val = read_cell(row, date_cols[-1] + 1)
        if k_val is not None and isinstance(k_val, (int, float)) and abs(k_val - row_sum) > 0.01:
            issues.append(f"第{row}行横向合计错误：K列={k_val}，实际={row_sum:.2f}")

    # ---- 输出报告 ----
    for item in ok_items:
        print(f"  [OK] {item}")
    for w in warnings:
        print(f"  [WARN] {w}")
    for e in issues:
        print(f"  [ERROR] {e}")

    if issues:
        print(f"\n[ALERT] 校验发现 {len(issues)} 个严重问题，请检查修正后再提交！")
    elif warnings:
        print(f"\n[ALERT] 校验发现 {len(warnings)} 个警告，建议核对后提交。")
    else:
        print("\n[OK] 自动校验通过，报销单数据一致。")


def set_default_printer():
    """设置 HP 物理打印机为默认"""
    print("\n" + "=" * 60)
    print("设置默认打印机")
    print("=" * 60)

    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Windows", 0, winreg.KEY_SET_VALUE)

        from subprocess import check_output
        printer_info = check_output(
            f"powershell -Command \"Get-Printer -Name '{PRINTER_NAME}' | Select-Object -ExpandProperty PortName\"",
            shell=True, encoding='utf-8'
        ).strip()

        device_value = f"{PRINTER_NAME},{printer_info}"
        winreg.SetValueEx(key, "Device", 0, winreg.REG_SZ, device_value)
        winreg.CloseKey(key)

        print(f"[OK] 已设置默认打印机：{PRINTER_NAME}")
        return True
    except Exception as e:
        print(f"[ERROR] 设置失败：{e}")
        return False


def sort_invoices(invoices: List[Invoice]) -> List[Invoice]:
    """按发票时间排序"""
    print("\n" + "=" * 60)
    print("优化打印顺序")
    print("=" * 60)

    trains = [inv for inv in invoices if inv.type == 'train']
    taxis = [inv for inv in invoices if inv.type == 'taxi']
    hotels = [inv for inv in invoices if inv.type == 'hotel']
    others = [inv for inv in invoices if inv.type == 'other']

    trains.sort(key=lambda x: x.date if x.date else datetime.min)
    taxis.sort(key=lambda x: x.date if x.date else datetime.min)
    hotels.sort(key=lambda x: x.date if x.date else datetime.min)
    others.sort(key=lambda x: x.date if x.date else datetime.min)

    sorted_invoices = trains + taxis + hotels + others

    print("\n打印顺序：")
    for i, inv in enumerate(sorted_invoices, 1):
        date_str = inv.date.strftime('%Y-%m-%d') if inv.date else '未知日期'
        tag = "【退票】" if inv.info.get('is_refund') else ""
        einvoice_tag = "[电子发票]" if inv.info.get('is_einvoice') else ""
        print(f"  {i}. [{inv.type}]{tag}{einvoice_tag} {inv.file_name} ({date_str})")
    print("\n最后打印：报销单 Excel")

    return sorted_invoices


def print_files(folder: str, invoices: List[Invoice], reimbursement_form: str):
    """打印所有文件"""
    print("\n" + "=" * 60)
    print("发送打印任务")
    print("=" * 60)

    try:
        from comtypes import COMError
        shell = None
        try:
            import comtypes.client
            shell = comtypes.client.CreateObject("Shell.Application")
        except (ImportError, COMError):
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")

        for inv in invoices:
            file_path = os.path.join(folder, inv.file_name)
            if os.path.exists(file_path):
                print(f"打印：{inv.file_name}...", end=' ')
                shellFolder = shell.Namespace(os.path.dirname(file_path))
                shellFile = shellFolder.ParseName(inv.file_name)
                if shellFile:
                    shellFile.InvokeVerb("Print")
                    print("[OK]")
                    import time
                    time.sleep(0.8)
                else:
                    print("[ERROR]")

        if reimbursement_form:
            print(f"打印：{os.path.basename(reimbursement_form)}...", end=' ')
            shellFolder = shell.Namespace(os.path.dirname(reimbursement_form))
            shellFile = shellFolder.ParseName(os.path.basename(reimbursement_form))
            if shellFile:
                shellFile.InvokeVerb("Print")
                print("[OK]")

        print(f"\n[OK] 已发送 {len(invoices) + 1} 个文件的打印任务")
    except Exception as e:
        print(f"[ERROR] 打印失败：{e}")


def main(folder: str = DEFAULT_FOLDER, skip_print: bool = False,
         company: str = 'kunshan', user_text: str = None,
         project_override: str = None):
    """主函数"""
    print("\n" + "=" * 60)
    print("k2-kunshan-print Skill")
    print("昆山出差报销自动化处理 v2.0")
    print("=" * 60)
    print(f"工作目录：{folder}")

    if user_text:
        print(f"\n用户描述：{user_text}")
        parsed_company = parse_company_from_text(user_text)
        if parsed_company != 'default':
            company = parsed_company

    company_name = COMPANIES.get(company, COMPANIES['default'])
    print(f"选择公司：{company_name}")

    file_check = check_necessary_files(folder)
    if not file_check['has_invoice']:
        print("\n[WARN] 缺少必要文件，请提供发票 PDF")
        return

    travel_app = read_travel_application(folder)
    invoices = read_invoice_info(folder)
    if not invoices:
        print("\n[WARN] 未能读取到有效发票信息")
        return

    didi_trips, didi_detail = read_didi_trips(folder)

    if travel_app.days > 0:
        subsidy = travel_app.days * SUBSIDY_FULL_DAY
    else:
        subsidy = 450.0

    reimbursement_form = fill_reimbursement_form(
        folder, invoices, subsidy, travel_app,
        didi_trips, didi_detail, company, project_override
    )
    if not reimbursement_form:
        print("\n[WARN] 报销单填写失败")
        return

    set_default_printer()
    sorted_invoices = sort_invoices(invoices)

    if not skip_print:
        print_files(folder, sorted_invoices, reimbursement_form)
        print("\n[SUCCESS] 打印任务已发送，请前往打印机取件！")
    else:
        print("\n[SUCCESS] 报销单已填写完成，跳过打印")
        print(f"文件位置：{reimbursement_form}")

    print("\n" + "=" * 60)
    print("处理完成")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='昆山出差报销自动化处理')
    parser.add_argument('--folder', type=str, default=DEFAULT_FOLDER, help='发票文件夹路径')
    parser.add_argument('--no-print', action='store_true', help='仅填写报销单，不打印')
    parser.add_argument('--company', type=str, default='kunshan', help='选择公司')
    parser.add_argument('--text', type=str, default=None, help='用户的自然语言描述')
    parser.add_argument('--project', type=str, default=None, help='手动指定项目编号与名称')

    args = parser.parse_args()

    main(args.folder, args.no_print, args.company, args.text, args.project)
