#!/usr/bin/env python3
"""Резолвер названия показателя лаборатории → канонический slug.

Использование:
  python resolve_metric_slug.py "Тиреотропный гормон (ТТГ)"
  python resolve_metric_slug.py --list
  python resolve_metric_slug.py --self-check

Выход (stdout), одна строка JSON (удобно агенту разобрать):
  {"slug":"tsh","title":"...","value_kind":"numeric","match":"synonym"}
  {"slug":null,"title":null,"value_kind":null,"match":"none","normalized":"..."}

Словарь (канон): schema/metric-synonyms.yaml

Только точное совпадение после normalize. Частичное («contains») запрещено:
оно склеивало разные показатели (АЧТВ и АЧТВ Ratio, гемоглобин и MCH).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]  # med-wiki/
SYNONYMS_PATH = ROOT / "schema" / "metric-synonyms.yaml"


def normalize(text: str) -> str:
    s = text.strip().lower().replace("ё", "е")
    s = re.sub(r"[\"'`]", "", s)
    s = re.sub(r"[()\[\]{},;:]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_entries(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Synonyms file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("metrics") or [])


def build_index(entries: list[dict]) -> dict[str, dict]:
    """Нормализованный ключ → meta. Дубль ключа на разные slug — ошибка словаря."""
    index: dict[str, dict] = {}
    for e in entries:
        slug = e["slug"]
        meta = {
            "slug": slug,
            "title": e.get("title") or slug,
            "value_kind": e.get("value_kind") or "numeric",
        }
        keys = [e.get("title") or "", slug] + list(e.get("synonyms") or [])
        for k in keys:
            if not k:
                continue
            nk = normalize(str(k))
            if nk in index and index[nk]["slug"] != slug:
                raise ValueError(
                    f"Synonym key collision in dictionary: {nk!r} → "
                    f"{index[nk]['slug']!r} and {slug!r}"
                )
            index[nk] = meta
    return index


def resolve(name: str, index: dict[str, dict]) -> dict:
    key = normalize(name)
    if key in index:
        hit = dict(index[key])
        hit["match"] = "synonym"
        return hit
    return {
        "slug": None,
        "title": None,
        "value_kind": None,
        "match": "none",
        "normalized": key,
    }


def self_check(entries: list[dict], index: dict[str, dict]) -> int:
    """Проверки словаря. Возвращает число ошибок (0 = ок)."""
    errors = 0
    # 1) ключ из 1 символа — почти наверняка мусор; длина 2 при exact допустима (ТГ, ЩФ)
    for e in entries:
        for syn in [e.get("title") or ""] + list(e.get("synonyms") or []):
            if not syn:
                continue
            nk = normalize(str(syn))
            if len(nk) < 1:
                print(f"ERROR: empty key for slug {e['slug']}", file=sys.stderr)
                errors += 1
            elif len(nk) == 1:
                print(f"ERROR: key too short ({nk!r}) for slug {e['slug']}", file=sys.stderr)
                errors += 1

    # 2) Ratio / % / абс. не должны делить slug с «базовым» без суффикса в slug
    risky_tokens = ("ratio", "%", "процент", "абсолют")
    for e in entries:
        slug = e["slug"]
        for syn in e.get("synonyms") or []:
            nk = normalize(str(syn))
            has_mod = any(t in nk for t in risky_tokens)
            slug_has_mod = any(
                t in slug for t in ("ratio", "pct", "abs", "percent")
            )
            if has_mod and not slug_has_mod:
                # исключение: «NEUT %» уже на neutrophils-pct
                if slug.endswith("-pct") or slug.endswith("-abs"):
                    continue
                print(
                    f"WARN: modifier in synonym {syn!r} but slug {slug!r} "
                    f"has no ratio/pct/abs — check split",
                    file=sys.stderr,
                )
    # 3) build_index already raises on exact collisions
    print(f"self-check: {len(entries)} entries, {len(index)} keys, errors={errors}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve lab metric name to slug")
    parser.add_argument("name", nargs="?", help="Indicator name as in the document")
    parser.add_argument("--list", action="store_true", help="Print all known slugs")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Validate synonym dictionary (exact collisions, short keys)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=SYNONYMS_PATH,
        help="Path to metric-synonyms.yaml",
    )
    args = parser.parse_args()

    entries = load_entries(args.file)
    index = build_index(entries)

    if args.list:
        for e in entries:
            print(f"{e['slug']}\t{e.get('title', '')}")
        return

    if args.self_check:
        sys.exit(1 if self_check(entries, index) else 0)

    if not args.name:
        parser.error("name required unless --list or --self-check")

    print(json.dumps(resolve(args.name, index), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
