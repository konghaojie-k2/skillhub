#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoResearch - 基于量化评估的自动化优化框架

核心思想：
1. 量化评估 - 用数字衡量当前状态
2. 自动优化 - 尝试改进，根据评估结果决策
3. 回滚机制 - 如果改进失败则自动恢复
4. 持续迭代 - 循环直到达到目标

Usage:
    from autoresearch import AutoResearch

    ar = AutoResearch(
        evaluate_cmd="uv run validate.py",
        score_pattern=r'score: (\d+)',
        target_score=100,
        backup_files=['README.md']
    )

    ar.run()
"""

import re
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional, List


@dataclass
class ResearchResult:
    """单次实验结果"""
    score: float
    improved: bool
    iteration: int
    details: str = ""


class AutoResearch:
    """
    自动研究/优化框架

    基于量化评估的自动化迭代优化，核心循环：
    1. 评估当前状态
    2. 尝试改进（由用户提供的 experiment_func 实现）
    3. 再次评估
    4. 如果改进则保留，否则回滚
    5. 重复直到达到目标或最大迭代次数
    """

    def __init__(
        self,
        evaluate_func: Optional[Callable[[], float]] = None,
        evaluate_cmd: Optional[str] = None,
        score_pattern: Optional[str] = None,
        target_score: float = 100.0,
        max_iterations: int = 100,
        backup_files: Optional[List[str]] = None,
        backup_dir: str = ".research_backups",
        experiment_func: Optional[Callable[[], bool]] = None,
        score_direction: str = "maximize"
    ):
        self.evaluate_func = evaluate_func
        self.evaluate_cmd = evaluate_cmd
        self.score_pattern = score_pattern
        self.target_score = target_score
        self.max_iterations = max_iterations
        self.backup_files = backup_files or []
        self.backup_dir = Path(backup_dir)
        self.experiment_func = experiment_func
        self.score_direction = score_direction

        self.iteration = 0
        self.best_score = float('-inf') if score_direction == "maximize" else float('inf')
        self.history = []

        self.backup_dir.mkdir(exist_ok=True)

    def _get_score_from_output(self, output: str) -> float:
        if not self.score_pattern:
            numbers = re.findall(r'\d+\.?\d*', output)
            if numbers:
                return float(numbers[-1])
            raise ValueError(f"No score found in output: {output}")

        match = re.search(self.score_pattern, output)
        if match:
            return float(match.group(1))
        raise ValueError(f"Score pattern not found in output: {output}")

    def evaluate(self) -> float:
        if self.evaluate_func:
            return self.evaluate_func()

        if self.evaluate_cmd:
            result = subprocess.run(
                self.evaluate_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            output = result.stdout + result.stderr
            return self._get_score_from_output(output)

        raise ValueError("Either evaluate_func or evaluate_cmd must be provided")

    def backup(self):
        for file_path in self.backup_files:
            src = Path(file_path)
            if src.exists():
                dst = self.backup_dir / f"{src.name}.backup"
                shutil.copy2(src, dst)

    def restore(self):
        for file_path in self.backup_files:
            src = self.backup_dir / f"{Path(file_path).name}.backup"
            dst = Path(file_path)
            if src.exists():
                shutil.copy2(src, dst)

    def is_improvement(self, new_score: float, old_score: float) -> bool:
        if self.score_direction == "maximize":
            return new_score > old_score
        else:
            return new_score < old_score

    def should_stop(self, score: float) -> bool:
        if self.score_direction == "maximize":
            return score >= self.target_score
        else:
            return score <= self.target_score

    def run_once(self) -> ResearchResult:
        self.iteration += 1
        print(f"\n{'='*60}")
        print(f"Iteration {self.iteration}/{self.max_iterations}")
        print(f"{'='*60}")

        try:
            before_score = self.evaluate()
        except Exception as e:
            print(f"[ERROR] Failed to evaluate: {e}")
            return ResearchResult(0, False, self.iteration, str(e))

        print(f"Before: score={before_score}")

        self.backup()

        success = False
        if self.experiment_func:
            try:
                success = self.experiment_func()
            except Exception as e:
                print(f"[ERROR] Experiment failed: {e}")
                success = False
        else:
            result = subprocess.run(
                "uv run experiment.py",
                shell=True,
                capture_output=True,
                text=True
            )
            success = result.returncode == 0

        try:
            after_score = self.evaluate()
        except Exception as e:
            print(f"[ERROR] Failed to evaluate after: {e}")
            self.restore()
            return ResearchResult(before_score, False, self.iteration, str(e))

        print(f"After:  score={after_score}")

        improved = self.is_improvement(after_score, before_score)

        if improved:
            print(f"[OK] Improvement! {before_score} -> {after_score}")
            self.best_score = after_score
            self.backup()
        elif after_score == before_score:
            print(f"[=] No change.")
        else:
            print(f"[FAIL] Regression! Reverting...")
            self.restore()

        result = ResearchResult(
            score=after_score if improved else before_score,
            improved=improved,
            iteration=self.iteration,
            details=f"{before_score} -> {after_score}"
        )
        self.history.append(result)

        return result

    def run(self) -> List[ResearchResult]:
        print(f"\n{'='*60}")
        print("AutoResearch Starting")
        print(f"{'='*60}")
        print(f"Target: {self.target_score}, Max iterations: {self.max_iterations}")

        try:
            initial_score = self.evaluate()
            print(f"Initial score: {initial_score}")
            self.best_score = initial_score
        except Exception as e:
            print(f"[ERROR] Initial evaluation failed: {e}")
            return []

        if self.should_stop(initial_score):
            print(f"[COMPLETE] Already at target: {initial_score}")
            return [ResearchResult(initial_score, True, 0, "initial")]

        for _ in range(self.max_iterations):
            result = self.run_once()

            if self.should_stop(result.score):
                print(f"\n[COMPLETE] Target reached! Final: {result.score}")
                break

        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"Iterations: {self.iteration}, Best: {self.best_score}")
        print(f"Improvements: {sum(1 for r in self.history if r.improved)}")

        return self.history


def quick_research(
    target_score: float = 100.0,
    max_iterations: int = 50,
    score_pattern: str = r'score:\s*(\d+)',
    backup_files: Optional[List[str]] = None
) -> List[ResearchResult]:
    if backup_files is None:
        backup_files = ['README.md']

    ar = AutoResearch(
        evaluate_cmd="uv run experiment.py",
        score_pattern=score_pattern,
        target_score=target_score,
        max_iterations=max_iterations,
        backup_files=backup_files
    )

    return ar.run()


if __name__ == "__main__":
    print("AutoResearch Framework")
    print("Import and use: from autoresearch import AutoResearch, quick_research")