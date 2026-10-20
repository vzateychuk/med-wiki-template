#!/usr/bin/env python3
"""CLI для naming tool. Только генерация имён — 5 подкоманд, вывод = одна строка."""
import argparse
import os
import sys
from naming_logic import (
    format_raw_docs_name,
    format_raw_images_name,
    format_raw_articles_name,
    format_wiki_note_name,
    format_wiki_symptom_name,
    check_name,
    REGEX,
)

def main():
    parser = argparse.ArgumentParser(description="medwiki naming tool — simple formatter")
    sub = parser.add_subparsers(dest="action", required=True)
    
    # raw-docs
    gen = sub.add_parser("raw-docs", help="Generate raw/docs filename")
    gen.add_argument("--type", required=True, choices=[
        "consultation", "lab-panel", "discharge", "ultrasound", "mri",
        "ct", "xray", "ecg", "histology", "endoscopy"
    ])
    gen.add_argument("--date", required=True, help="YYYY-MM-DD")
    gen.add_argument("--disambiguator", default="", help="Collision suffix: '2', 'cardiologist', etc.")
    
    gen.add_argument("--check-exists", metavar="DIR", default="",
                     help="Dir to check (raw/docs). If the name is already taken: exit 4, no new name")

    # check (lint): проверка имён файлов в папке
    chk = sub.add_parser("check", help="Check existing file names in a directory (lint)")
    chk.add_argument("--layer", required=True, choices=list(REGEX))
    chk.add_argument("--dir", required=True)

    # raw-images
    img = sub.add_parser("raw-images", help="Generate raw/images filename")
    img.add_argument("--type", required=True, choices=[
        "consultation", "lab-panel", "discharge", "ultrasound", "mri",
        "ct", "xray", "ecg", "histology", "endoscopy"
    ])
    img.add_argument("--date", required=True, help="YYYY-MM-DD")
    img.add_argument("--disambiguator", default="")
    img.add_argument("--page", type=int, default=1, help="Page number (1, 2, ...)")
    img.add_argument("--ext", default="jpg", help="Extension: jpg, png, pdf...")
    
    # raw-articles
    art = sub.add_parser("raw-articles", help="Generate raw/articles filename")
    art.add_argument("--date", required=True, help="YYYY-MM-DD")
    art.add_argument("--slug", required=True, help="Article slug (kebab-case)")
    
    # wiki-note
    note = sub.add_parser("wiki-note", help="Generate wiki/notes filename")
    note.add_argument("--date", required=True, help="YYYY-MM-DD")
    note.add_argument("--slug", required=True, help="Note slug (kebab-case)")
    
    # wiki-symptom (сущность без даты)
    sym = sub.add_parser("wiki-symptom", help="Generate wiki/symptoms filename")
    sym.add_argument("--slug", required=True, help="Symptom slug (kebab-case)")
    
    args = parser.parse_args()
    
    try:
        if args.action == "raw-docs":
            name = format_raw_docs_name(args.type, args.date, args.disambiguator)
            if args.check_exists and os.path.exists(os.path.join(args.check_exists, name)):
                print(f"ALREADY EXISTS: {name}. Document is probably already loaded: "
                      "ask the user, do not create a new name.", file=sys.stderr)
                sys.exit(4)
            print(name)
        elif args.action == "check":
            bad = 0
            for fn in sorted(os.listdir(args.dir)):
                if fn.startswith(".") or fn == "_index.md" or not os.path.isfile(os.path.join(args.dir, fn)):
                    continue
                err = check_name(args.layer, fn)
                if err:
                    bad += 1
                    print(f"{fn}: {err}")
            sys.exit(1 if bad else 0)
        elif args.action == "raw-images":
            name = format_raw_images_name(args.type, args.date, args.disambiguator, args.page, args.ext)
            print(name)
        elif args.action == "raw-articles":
            name = format_raw_articles_name(args.date, args.slug)
            print(name)
        elif args.action == "wiki-note":
            name = format_wiki_note_name(args.date, args.slug)
            print(name)
        elif args.action == "wiki-symptom":
            name = format_wiki_symptom_name(args.slug)
            print(name)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()