---
name: torch-uv-install
description: Install PyTorch (CPU or CUDA) in Python projects managed by uv. Use when the user needs to install torch, torchvision, or torchaudio — especially CUDA versions on Windows. Covers uv pip install, local wheel caching, offline install, GPU detection, CUDA version matching, and verification.
---

# PyTorch 安装指南（uv 环境）

## 安装优先级（按顺序执行）

```
1. 检测 GPU 型号 → 确定 CUDA 版本
2. 搜索 uv 全局缓存 → 是否已有匹配版本？
   ├─ 有 → 直接从缓存安装（秒装）
   └─ 无 → 继续下一步
3. 搜索本地 wheel 目录 → 是否已有下载好的 wheel？
   ├─ 有 → uv pip install --find-links /path --no-index
   └─ 无 → 继续下一步
4. 联网下载安装
   ├─ 普通显卡 → uv pip install torch --index-url https://download.pytorch.org/whl/cuXXX
   └─ RTX 50xx / Blackwell → uv pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128
5. 配置 pyproject.toml（声明 torch 专用索引，避免 uv sync 解析到 CPU 版）
6. 验证安装
```

---

## 第一步：检测 GPU 型号 & 确定 CUDA 版本

### Windows

```powershell
# 查看 GPU 型号
nvidia-smi

# 或查看驱动支持的 CUDA 版本（Driver Version 对应 CUDA 版本）
# https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html
```

**根据 GPU 型号判断 CUDA 版本**：

| GPU 架构 | 支持 CUDA 版本 | 推荐 torch 索引 |
|---------|---------------|----------------|
| RTX 50xx (Blackwell) | CUDA 12.8+ | `cu128` |
| RTX 40xx (Ada) | CUDA 11.8+ / 12.x | `cu121` 或 `cu124` |
| RTX 30xx (Ampere) | CUDA 11.1+ / 12.x | `cu121` 或 `cu124` |
| RTX 20xx (Turing) | CUDA 10.0+ / 12.x | `cu121` |
| GTX 10xx (Pascal) | CUDA 8.0+ / 12.x | `cu121` |
| 无 NVIDIA GPU | — | `cpu` |

**通用规则**：
- **CUDA 12.1** (`cu121`)：兼容性最好，绝大多数显卡支持
- **CUDA 12.4** (`cu124`)：较新，需驱动 >= 535
- **CUDA 12.8** (`cu128`)：RTX 50xx (Blackwell, sm_120) 必需，需驱动 >= 570
- **CUDA 11.8** (`cu118`)：老旧显卡备用
- **CPU** (`cpu`)：无 NVIDIA 显卡时用

**如果不知道选哪个，先用 `cu121`**。

---

## 第二步：搜索 uv 缓存

```bash
# 查看 uv 缓存位置
uv cache dir
# 输出: C:\Users\xxx\AppData\Local\uv\cache

# uv 会自动从缓存安装，不需要手动操作
# 只要之前下载过，再次安装时会秒装
```

---

## 第三步：搜索本地 wheel

```bash
# 检查常见本地 wheel 目录
ls C:/torch_wheels/
ls D:/torch_wheels/
ls ~/torch_wheels/

# 如果有，直接安装
uv pip install torch torchvision --find-links C:/torch_wheels --no-index
```

---

## 第四步：联网下载安装

### 标准 uv 安装（有网络）

```bash
cd "项目根目录"

# CUDA 12.1（最通用，推荐）
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# CUDA 12.4（较新，需驱动 >= 535）
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# CUDA 12.8（RTX 50xx / Blackwell 必需，需驱动 >= 570）
uv pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128

# CUDA 11.8（老旧显卡备用）
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CPU 版本（无显卡）
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### RTX 50xx / Blackwell 特殊说明

- **RTX 50xx 是 sm_120 架构**，`cu124` 不支持，必须装 `cu128`
- 目前 PyTorch stable 版通常不包含 `cu128`，需要装 **nightly**：

```bash
uv pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128
```

- 如果 `uv pip install` 在解析跨平台依赖（如 Linux-only 的 triton）时失败，可改用 `.venv` 内的 `pip` 直接装：

```bash
# Windows
uv pip install pip
.venv/Scripts/python -m pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128 --force-reinstall

# Linux/macOS
uv pip install pip
.venv/bin/python -m pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128 --force-reinstall
```

### .venv 无 pip 时的安装

uv 创建的 .venv 默认没有 pip，如需使用 pip 直接安装（例如 RTX 50xx 装 nightly cu128 时），需先安装 pip：

```bash
# Windows
uv pip install pip
.venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Linux/macOS
uv pip install pip
.venv/bin/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

需要 cu128 时，将上面命令中的索引换成 `https://download.pytorch.org/whl/nightly/cu128` 并加上 `--pre`。

---

## 第五步：配置 pyproject.toml（可选但推荐）

如果项目使用 `uv` 管理依赖，建议在 `pyproject.toml` 中声明 torch 专用索引，避免后续 `uv sync` 时从默认 PyPI 解析到 CPU 版本。

### 标准 CUDA 版本

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu121"

[tool.uv.sources]
torch = { index = "pytorch" }
torchvision = { index = "pytorch" }
```

### RTX 50xx / Blackwell（cu128 nightly）

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/nightly/cu128"

[tool.uv.sources]
torch = { index = "pytorch" }
torchvision = { index = "pytorch" }
```

### 注意事项

- `pyproject.toml` 中的索引配置**只影响依赖解析源**，不代表安装命令
- 对于 RTX 50xx，如果 `uv sync` 因跨平台依赖（如 Linux-only 的 triton）解析失败，建议直接用 `pip install` 安装 torch，而不是强行走 `uv sync`

---

## 第六步：验证安装

```bash
.venv/Scripts/python -c "
import torch
print('PyTorch 版本:', torch.__version__)
print('CUDA 可用:', torch.cuda.is_available())
print('CUDA 版本:', torch.version.cuda if torch.cuda.is_available() else 'N/A')
print('GPU 数量:', torch.cuda.device_count() if torch.cuda.is_available() else 0)
"
```

---

## 本地缓存 & 多项目共享

### uv 全局缓存（自动）

uv 缓存目录：`%LOCALAPPDATA%\uv\cache`

- 已下载的包**自动共享**给所有项目
- 重建 .venv 时直接从缓存读取，不需要重新下载
- **不需要额外操作**

### 显式备份 wheel（可选）

```bash
# 下载到固定目录（一次）
uv pip download torch torchvision --index-url https://download.pytorch.org/whl/cu121 -d C:/torch_wheels

# RTX 50xx / Blackwell 用 nightly cu128
uv pip download --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128 -d C:/torch_wheels

# 以后任何项目都从本地安装
uv pip install torch torchvision --find-links C:/torch_wheels --no-index
```

---

## 离线安装

```bash
# 1. 提前在有网机器下载
uv pip download torch torchvision --index-url https://download.pytorch.org/whl/cu121 -d ./torch_wheels

# RTX 50xx / Blackwell
uv pip download --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128 -d ./torch_wheels

# 2. 拷贝到离线机器

# 3. 离线安装
uv pip install torch torchvision --find-links ./torch_wheels --no-index
```

---

## Windows 注意事项

- **命令连接符**：用 `;` 不用 `&&`
  - ✅ `cd "项目"; uv pip install torch`
  - ❌ `cd "项目" && uv pip install torch`

- **路径**：用双引号包裹含空格的路径
  - ✅ `cd "C:\My Project"`

- **Nightly 版本大**：约 2.7GB，下载需耐心

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `No module named pip` | .venv 没有 pip | `uv pip install pip` |
| CUDA 不可用 | 驱动版本不匹配 / 装错 CUDA 版本 | 用 `nvidia-smi` 查驱动，对照 CUDA 版本表 |
| RTX 50xx 上 CUDA 不可用 | 装了 `cu124`，但 sm_120 需要 `cu128` | 换 `nightly/cu128` 版本 |
| `uv sync` 解析 torch 失败 | uv lock 跨平台依赖（如 Linux-only triton）冲突 | 用 `pip install` 直接装 torch，不通过 `uv sync` |
| 下载慢 | 官方源在国外 | 用清华 PyPI 镜像装依赖，torch 用官方源 |
| 缓存被清理 | uv cache clean | 用 `uv pip download` 备份 wheel |
| 不知道装哪个 CUDA 版本 | GPU 型号不明 | 先用 `cu121`（最通用），RTX 50xx 用 `cu128` |

---

## 快速决策表

| 用户情况 | 推荐命令 |
|---------|---------|
| 有 NVIDIA GPU，不知道型号 | `uv pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| RTX 40xx/30xx，驱动较新 | `uv pip install torch --index-url https://download.pytorch.org/whl/cu124` |
| RTX 50xx / Blackwell | `uv pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128` |
| 无 NVIDIA GPU | `uv pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| 无网络，有本地 wheel | `uv pip install torch --find-links /path --no-index` |
| .venv 没有 pip | 先 `uv pip install pip`，再用 pip 装 |
| `uv sync` 解析 torch 失败 | 改用 `.venv/Scripts/python -m pip install` 直接装 |
