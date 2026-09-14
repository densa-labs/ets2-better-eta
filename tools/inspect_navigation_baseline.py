#!/usr/bin/env python3
"""Inspect navigation fields reachable from an extracted ETS2 map_data.sii."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path


EXPECTED_FIELDS = (
    "navigation_time_narrow_road_max_speed_usage",
    "navigation_time_road_max_speed_usage",
    "navigation_time_city_or_slowtime_speed_penalty",
    "navigation_time_semaphore_wait_duration",
    "navigation_time_stop_wait_duration",
    "navigation_time_turn_own_side_duration",
    "navigation_time_turn_oposite_side_duration",
)

INCLUDE_RE = re.compile(r'^\s*@include\s+"([^"]+)"')
FIELD_RE = re.compile(r"^\s*(navigation[A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")


@dataclass(frozen=True)
class Field:
    name: str
    value: str
    source: Path
    line: int


@dataclass(frozen=True)
class Include:
    source: Path
    line: int
    target_text: str
    target: Path | None
    status: str


@dataclass
class Inspection:
    root: Path
    entry: Path
    files: list[Path]
    hashes: dict[Path, str]
    fields: list[Field]
    includes: list[Include]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_comments(lines: list[str]) -> list[str]:
    """Remove //, #, and block comments while respecting quoted strings."""
    cleaned: list[str] = []
    in_block = False
    for line in lines:
        output: list[str] = []
        index = 0
        quoted = False
        while index < len(line):
            pair = line[index : index + 2]
            if in_block:
                if pair == "*/":
                    in_block = False
                    index += 2
                else:
                    index += 1
                continue
            if not quoted and pair == "/*":
                in_block = True
                index += 2
                continue
            if not quoted and pair == "//":
                break
            if not quoted and line[index] == "#":
                break
            if line[index] == '"' and (index == 0 or line[index - 1] != "\\"):
                quoted = not quoted
            output.append(line[index])
            index += 1
        cleaned.append("".join(output))
    return cleaned


def locate_entry(input_path: Path) -> tuple[Path, Path]:
    supplied = input_path.resolve()
    if supplied.is_file():
        root = supplied.parent.parent if supplied.parent.name == "def" else supplied.parent
        return root, supplied
    if not supplied.is_dir():
        raise ValueError(f"input does not exist: {input_path}")
    candidates = (supplied / "def" / "map_data.sii", supplied / "map_data.sii")
    for candidate in candidates:
        if candidate.is_file():
            root = supplied.parent if supplied.name == "def" else supplied
            return root, candidate.resolve()
    raise ValueError(f"no def/map_data.sii or map_data.sii beneath: {input_path}")


def resolve_include(root: Path, source: Path, target_text: str) -> tuple[Path | None, str]:
    if target_text.startswith("/"):
        candidate = root / target_text.lstrip("/")
    else:
        candidate = source.parent / target_text
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, "OUTSIDE_ROOT"
    if not resolved.is_file():
        return resolved, "MISSING"
    return resolved, "FOUND"


def inspect(input_path: Path) -> Inspection:
    root, entry = locate_entry(input_path)
    root = root.resolve()
    files: list[Path] = []
    hashes: dict[Path, str] = {}
    fields: list[Field] = []
    includes: list[Include] = []
    visited: set[Path] = set()
    active: set[Path] = set()

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in visited:
            return
        visited.add(path)
        active.add(path)
        files.append(path)
        hashes[path] = sha256(path)
        raw_lines = path.read_text(encoding="utf-8-sig").splitlines()
        for line_number, line in enumerate(strip_comments(raw_lines), start=1):
            include_match = INCLUDE_RE.match(line)
            if include_match:
                target_text = include_match.group(1)
                target, status = resolve_include(root, path, target_text)
                if target is not None and target in active:
                    status = "CYCLE"
                includes.append(Include(path, line_number, target_text, target, status))
                if status == "FOUND" and target is not None:
                    visit(target)
                continue
            field_match = FIELD_RE.match(line)
            if field_match:
                fields.append(
                    Field(field_match.group(1), field_match.group(2), path, line_number)
                )
        active.remove(path)

    visit(entry)
    return Inspection(root, entry, files, hashes, fields, includes)


def relative(path: Path | None, root: Path) -> str:
    if path is None:
        return "-"
    return path.relative_to(root).as_posix()


def render(result: Inspection) -> str:
    lines = [
        "ETS2 navigation baseline inspection",
        f"input_root: {result.root}",
        f"entry_file: {relative(result.entry, result.root)}",
        "",
        "INSPECTED FILES (SHA-256)",
    ]
    for path in result.files:
        lines.append(f"{relative(path, result.root)}  {result.hashes[path]}")

    lines.extend(("", "REACHABLE @INCLUDES"))
    if not result.includes:
        lines.append("(none)")
    for include in result.includes:
        target = relative(include.target, result.root) if include.target else "-"
        lines.append(
            f"{relative(include.source, result.root)}:{include.line}  "
            f'"{include.target_text}" -> {target}  [{include.status}]'
        )

    lines.extend(("", "ALL navigation* FIELDS"))
    if not result.fields:
        lines.append("(none)")
    for field in result.fields:
        lines.append(
            f"{field.name}: {field.value}  "
            f"[{relative(field.source, result.root)}:{field.line}]"
        )

    time_fields = [field for field in result.fields if field.name.startswith("navigation_time_")]
    lines.extend(("", "ALL navigation_time_* FIELDS"))
    if not time_fields:
        lines.append("(none)")
    for field in time_fields:
        lines.append(
            f"{field.name}: {field.value}  "
            f"[{relative(field.source, result.root)}:{field.line}]"
        )

    by_name: dict[str, list[Field]] = {}
    for field in time_fields:
        by_name.setdefault(field.name, []).append(field)
    lines.extend(("", "EXPECTED BETTER ETA CANDIDATES"))
    for name in EXPECTED_FIELDS:
        matches = by_name.get(name, [])
        if not matches:
            lines.append(f"{name}: MISSING")
        for field in matches:
            lines.append(
                f"{name}: {field.value}  "
                f"[{relative(field.source, result.root)}:{field.line}]"
            )

    extras = sorted(set(by_name) - set(EXPECTED_FIELDS))
    lines.extend(("", "ADDITIONAL navigation_time_* FIELDS"))
    lines.extend(extras or ["(none)"])
    missing = [name for name in EXPECTED_FIELDS if name not in by_name]
    lines.extend(("", "MISSING EXPECTED FIELDS"))
    lines.extend(missing or ["(none)"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect navigation definitions reachable from ETS2 map_data.sii."
    )
    parser.add_argument("input", type=Path, help="extracted definition tree or map_data.sii")
    parser.add_argument("--output", type=Path, help="write report to this path")
    args = parser.parse_args(argv)
    try:
        report = render(inspect(args.input))
        if args.output:
            args.output.write_text(report, encoding="utf-8")
        else:
            sys.stdout.write(report)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
