#!/usr/bin/env python3
"""Validate the repository's classical rule-set files."""

from __future__ import annotations

import ipaddress
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE_FILES = (ROOT / "Directlist.list", ROOT / "GFWlist.list")
RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
}
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
METADATA_RE = re.compile(
    r"^# (DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6|IP-ASN|TOTAL): (\d+)$"
)


def validate_rule(rule_type: str, value: str, options: list[str]) -> str | None:
    if value != value.lower():
        return "规则值必须使用小写"
    if value != value.strip() or any(char.isspace() for char in value):
        return "规则值不能包含空白字符"

    if rule_type in {"DOMAIN", "DOMAIN-SUFFIX"} and not DOMAIN_RE.fullmatch(value):
        return "域名格式无效"
    if rule_type == "DOMAIN-KEYWORD" and not value:
        return "关键字不能为空"
    if rule_type in {"IP-CIDR", "IP-CIDR6"}:
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            return "CIDR 格式无效"
        expected_version = 4 if rule_type == "IP-CIDR" else 6
        if network.version != expected_version:
            return f"地址版本与 {rule_type} 不符"
    if rule_type == "IP-ASN" and (not value.isdigit() or int(value) < 1):
        return "ASN 必须是正整数"
    if any(option != "no-resolve" for option in options):
        return "仅支持 no-resolve 选项"
    if options and rule_type not in {"IP-CIDR", "IP-CIDR6", "IP-ASN"}:
        return "域名类规则不能使用附加选项"
    return None


def parse_file(path: Path) -> tuple[list[tuple[str, str]], dict[str, int], list[str]]:
    rules: list[tuple[str, str]] = []
    declared: dict[str, int] = {}
    errors: list[str] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            match = METADATA_RE.fullmatch(line)
            if match:
                declared[match.group(1)] = int(match.group(2))
            continue

        parts = line.split(",")
        if len(parts) < 2:
            errors.append(f"{path.name}:{line_number}: 缺少规则值")
            continue

        rule_type, value, *options = parts
        if rule_type not in RULE_TYPES:
            errors.append(f"{path.name}:{line_number}: 不支持的规则类型 {rule_type!r}")
            continue

        error = validate_rule(rule_type, value, options)
        if error:
            errors.append(f"{path.name}:{line_number}: {error}: {line!r}")
        rules.append((rule_type, value))

    counts = Counter(rule_type for rule_type, _ in rules)
    expected = {rule_type: counts[rule_type] for rule_type in RULE_TYPES}
    expected["TOTAL"] = len(rules)
    for key, actual in sorted(expected.items()):
        if key in declared and declared[key] != actual:
            errors.append(
                f"{path.name}: 元数据 {key}={declared[key]}，实际为 {actual}"
            )

    duplicates = [rule for rule, count in Counter(rules).items() if count > 1]
    for rule_type, value in sorted(duplicates):
        errors.append(f"{path.name}: 重复规则 {rule_type},{value}")

    return rules, declared, errors


def main() -> int:
    all_errors: list[str] = []
    parsed: dict[Path, list[tuple[str, str]]] = {}

    for path in RULE_FILES:
        if not path.is_file():
            all_errors.append(f"缺少规则文件: {path.name}")
            continue
        rules, _, errors = parse_file(path)
        parsed[path] = rules
        all_errors.extend(errors)

    if len(parsed) == len(RULE_FILES):
        direct_targets = {value for _, value in parsed[RULE_FILES[0]]}
        proxy_targets = {value for _, value in parsed[RULE_FILES[1]]}
        for value in sorted(direct_targets & proxy_targets):
            all_errors.append(f"直连和代理列表存在冲突: {value}")

    if all_errors:
        print("规则校验失败：", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    total = sum(len(rules) for rules in parsed.values())
    print(f"规则校验通过：{len(parsed)} 个文件，共 {total} 条生效规则。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
