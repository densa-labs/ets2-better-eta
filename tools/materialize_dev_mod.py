#!/usr/bin/env python3
"""Materialize a narrow Better ETA development probe from stock map_data.sii."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = REPOSITORY_ROOT / "build"
KNOWN_160_MAP_DATA_SHA256 = "9433ef7c8d120509ee641f6d1643966ddc99effe1f237ec9c6b34025bdb72473"
UNIT_RE = re.compile(r"(?m)^\s*map_data\s*:\s*\.map\.data\s*\{")
FIELD_NAME_RE = re.compile(r"navigation_time_[A-Za-z0-9_]+")
VALUE_RE = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
PROFILE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class MaterializationError(ValueError):
    """Raised when an input cannot be safely materialized."""


@dataclass(frozen=True)
class Assignment:
    field: str
    value: str


@dataclass(frozen=True)
class Experiment:
    profile: str
    display_name: str
    expected_source_sha256: str
    assignments: tuple[Assignment, ...]


@dataclass(frozen=True)
class Materialization:
    source_hash: str
    output_path: Path
    output_hash: str
    assignments: tuple[Assignment, ...]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_experiment(path: Path) -> Experiment:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MaterializationError(f"cannot read experiment {path}: {error}") from error

    if not isinstance(raw, dict):
        raise MaterializationError("experiment root must be an object")
    required = {"profile", "display_name", "expected_source_sha256", "assignments"}
    if set(raw) != required:
        raise MaterializationError(
            f"experiment keys must be exactly: {', '.join(sorted(required))}"
        )
    profile = raw["profile"]
    display_name = raw["display_name"]
    expected_hash = raw["expected_source_sha256"]
    assignment_items = raw["assignments"]
    if not isinstance(profile, str) or not PROFILE_RE.fullmatch(profile):
        raise MaterializationError("profile must be a lowercase hyphenated identifier")
    if not isinstance(display_name, str) or not display_name.strip():
        raise MaterializationError("display_name must be a non-empty string")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise MaterializationError("expected_source_sha256 must be 64 lowercase hex characters")
    if not isinstance(assignment_items, list) or not assignment_items:
        raise MaterializationError("assignments must be a non-empty array")

    assignments: list[Assignment] = []
    seen: set[str] = set()
    for item in assignment_items:
        if not isinstance(item, dict) or set(item) != {"field", "value"}:
            raise MaterializationError("each assignment must contain only field and value")
        field = item["field"]
        value = item["value"]
        if not isinstance(field, str) or not FIELD_NAME_RE.fullmatch(field):
            raise MaterializationError(f"invalid navigation_time_ field: {field!r}")
        if field in seen:
            raise MaterializationError(f"duplicate experiment assignment: {field}")
        if not isinstance(value, str) or not VALUE_RE.fullmatch(value):
            raise MaterializationError(f"value for {field} must be a non-negative decimal string")
        try:
            if Decimal(value) <= 0:
                raise MaterializationError(f"value for {field} must be greater than zero")
        except InvalidOperation as error:
            raise MaterializationError(f"invalid decimal value for {field}: {value}") from error
        seen.add(field)
        assignments.append(Assignment(field, value))
    return Experiment(profile, display_name, expected_hash, tuple(assignments))


def code_without_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    in_block = False
    in_line = False
    quoted = False
    while index < len(text):
        pair = text[index : index + 2]
        char = text[index]
        if in_line:
            if char in "\r\n":
                in_line = False
                output.append(char)
            else:
                output.append(" ")
            index += 1
            continue
        if in_block:
            if pair == "*/":
                output.extend((" ", " "))
                in_block = False
                index += 2
            else:
                output.append(char if char in "\r\n" else " ")
                index += 1
            continue
        if not quoted and pair == "/*":
            output.extend((" ", " "))
            in_block = True
            index += 2
            continue
        if not quoted and pair == "//":
            output.extend((" ", " "))
            in_line = True
            index += 2
            continue
        if not quoted and char == "#":
            output.append(" ")
            in_line = True
            index += 1
            continue
        if char == '"' and (index == 0 or text[index - 1] != "\\"):
            quoted = not quoted
        output.append(char)
        index += 1
    return "".join(output)


def find_unit_close(text: str, opening_brace: int) -> int:
    code = code_without_comments(text)
    depth = 0
    quoted = False
    for index in range(opening_brace, len(code)):
        char = code[index]
        if char == '"' and (index == 0 or code[index - 1] != "\\"):
            quoted = not quoted
        if quoted:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise MaterializationError("map_data unit has no matching closing brace")


def insert_assignments(source: bytes, experiment: Experiment) -> bytes:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MaterializationError("source must be UTF-8 text") from error
    code = code_without_comments(text)
    matches = list(UNIT_RE.finditer(code))
    if len(matches) != 1:
        raise MaterializationError(f"expected exactly one map_data : .map.data unit, found {len(matches)}")

    for assignment in experiment.assignments:
        existing = re.compile(rf"(?m)^\s*{re.escape(assignment.field)}\s*:")
        if existing.search(code):
            raise MaterializationError(f"source already assigns {assignment.field}")

    opening_brace = matches[0].end() - 1
    closing_brace = find_unit_close(text, opening_brace)
    line_start = max(text.rfind("\n", 0, closing_brace), text.rfind("\r", 0, closing_brace)) + 1
    if text[line_start:closing_brace].strip():
        raise MaterializationError("map_data closing brace must be on its own line")
    newline = "\r\n" if "\r\n" in text else "\n"
    block = [f"\t# Better ETA experimental profile: {experiment.profile}"]
    block.extend(f"\t{item.field}: {item.value}" for item in experiment.assignments)
    insertion = newline.join(block) + newline
    return (text[:line_start] + insertion + text[line_start:]).encode("utf-8")


def manifest(experiment: Experiment) -> bytes:
    content = f'''SiiNunit
{{
mod_package : .b_eta_m2
{{
    package_version: "m2-experiment"
    display_name: "{experiment.display_name}"
    author: "Densa Labs"
    category[]: "other"
    compatible_versions[]: "1.60.*"
    description_file: "description.txt"
}}
}}
'''
    return content.encode("utf-8")


def description(experiment: Experiment) -> bytes:
    assignments = "\n".join(f"{item.field}: {item.value}" for item in experiment.assignments)
    return (
        "Better ETA Milestone 2 causal experiment only.\n"
        "Not a production configuration and not a claim about vanilla defaults.\n\n"
        f"{assignments}\n"
    ).encode("utf-8")


def materialize(
    source_path: Path,
    experiment_path: Path,
    output_root: Path,
    *,
    allow_unexpected_source: bool = False,
) -> Materialization:
    experiment = load_experiment(experiment_path)
    try:
        source = source_path.read_bytes()
    except OSError as error:
        raise MaterializationError(f"cannot read source {source_path}: {error}") from error
    source_hash = sha256_bytes(source)
    if source_hash != experiment.expected_source_sha256 and not allow_unexpected_source:
        raise MaterializationError(
            "unexpected stock source SHA-256: "
            f"expected {experiment.expected_source_sha256}, got {source_hash}; "
            "use --allow-unexpected-source only for deliberate development"
        )

    generated = insert_assignments(source, experiment)
    profile_root = output_root / experiment.profile
    output_path = profile_root / "def" / "map_data.sii"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(generated)
    (profile_root / "manifest.sii").write_bytes(manifest(experiment))
    (profile_root / "description.txt").write_bytes(description(experiment))
    return Materialization(
        source_hash,
        output_path,
        sha256_bytes(generated),
        experiment.assignments,
    )


def require_build_output(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(BUILD_ROOT.resolve())
    except ValueError as error:
        raise MaterializationError(f"output must be inside ignored build directory: {BUILD_ROOT}") from error
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="authoritative stock map_data.sii")
    parser.add_argument("experiment", type=Path, help="tracked experimental JSON delta")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=BUILD_ROOT / "dev-mod",
        help="generated root inside build/ (default: build/dev-mod)",
    )
    parser.add_argument(
        "--allow-unexpected-source",
        action="store_true",
        help="permit a source hash mismatch for deliberate development only",
    )
    args = parser.parse_args(argv)
    try:
        result = materialize(
            args.source,
            args.experiment,
            require_build_output(args.output_root),
            allow_unexpected_source=args.allow_unexpected_source,
        )
    except MaterializationError as error:
        parser.error(str(error))
    print(f"source_sha256: {result.source_hash}")
    for assignment in result.assignments:
        print(f"applied: {assignment.field}={assignment.value}")
    print(f"output_path: {result.output_path}")
    print(f"output_sha256: {result.output_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
