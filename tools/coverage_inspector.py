"""Inspect coverageデータを解析し、シンボル単位で未実行行を表示するユーティリティ。

使用方法:
    - `make coverage-report` で HTML の生成後、本スクリプトを通じて未実行行を一覧化できます。
    - 直接実行する場合は `uv run python tools/coverage_inspector.py` を利用してください。

coverage データ (.coverage) が存在しない場合は、先に `make coverage` または
`make coverage-renew` を実行してレポートを生成してください。
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import coverage
from coverage.exceptions import CoverageException

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = Path("/app")
DATA_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".coverage")
if not DATA_FILE.is_absolute():
    DATA_FILE = PROJECT_ROOT / DATA_FILE


class SymbolSpan(ast.NodeVisitor):
    """Collect symbol spans in a module."""

    def __init__(self) -> None:
        self._spans: List[Tuple[int, int, str]] = []
        self._stack: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # type: ignore[override]
        self._handle_symbol(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # type: ignore[override]
        self._handle_symbol(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # type: ignore[override]
        self._handle_symbol(node)

    def generic_visit(self, node: ast.AST) -> None:
        super().generic_visit(node)

    def _handle_symbol(self, node: ast.AST) -> None:
        name = getattr(node, "name", None)
        if not name:
            return
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        if start is None or end is None:
            return
        symbol_name = ".".join(self._stack + [name]) or name
        self._spans.append((start, end, symbol_name))
        self._stack.append(name)
        super().generic_visit(node)
        self._stack.pop()

    @property
    def spans(self) -> List[Tuple[int, int, str]]:
        return self._spans


def symbol_map_for_file(path: Path) -> List[Tuple[int, int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    collector = SymbolSpan()
    collector.visit(tree)
    # Sort by span size ascending to match closest scope first
    return sorted(collector.spans, key=lambda span: (span[1] - span[0], span[0]))


def find_symbol(spans: List[Tuple[int, int, str]], line: int) -> str:
    for start, end, name in spans:
        if start <= line <= end:
            return name
    return "<module>"


def build_report(cov: coverage.Coverage, filenames: Iterable[str]) -> Dict[str, Dict[str, List[int]]]:
    report: Dict[str, Dict[str, List[int]]] = {}
    for filename in sorted(filenames):
        path = Path(filename)
        if "site-packages" in path.parts:
            continue
        if path.suffix != ".py":
            continue
        if not path.exists():
            continue
        if not is_project_file(path):
            continue
        if path.is_relative_to(BACKEND_ROOT):
            rel = Path("backend") / path.relative_to(BACKEND_ROOT)
        else:
            rel = path.relative_to(PROJECT_ROOT)
        try:
            _filename, _statements, _executed, missing, _excluded = cov.analysis2(filename)
        except CoverageException:
            continue
        missing_lines = sorted(missing)
        if not missing_lines:
            continue
        spans = symbol_map_for_file(path)
        symbol_lines: Dict[str, List[int]] = defaultdict(list)
        for line in missing_lines:
            symbol = find_symbol(spans, line)
            symbol_lines[symbol].append(line)
        report[str(rel)] = {sym: lines for sym, lines in symbol_lines.items()}
    return report


def is_project_file(path: Path) -> bool:
    return path.is_relative_to(PROJECT_ROOT) or path.is_relative_to(BACKEND_ROOT)


def print_report(report: Dict[str, Dict[str, List[int]]]) -> None:
    if not report:
        print("All measured lines are covered.")
        return
    for file, symbols in report.items():
        print(f"File: {file}")
        for symbol, lines in sorted(symbols.items()):
            joined = ", ".join(str(line) for line in lines)
            print(f"  - {symbol}: missing lines {joined}")
        print()


def main() -> int:
    if not DATA_FILE.exists():
        print("No .coverage data found. Run `make coverage` or `make coverage-renew` first.")
        return 1
    cov = coverage.Coverage(data_file=str(DATA_FILE))
    cov.load()
    data = cov.get_data()
    report = build_report(cov, data.measured_files())
    print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
