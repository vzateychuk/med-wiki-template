#!/usr/bin/env python3
"""Чистая логика именования — только форматирование строк. Никакой ФС, никаких коллизий."""
import re

SUFFIX_MAP = {
    "consultation": "consultation",
    "lab-panel": "lab-panel",
    "discharge": "discharge",
    "ultrasound": "ultrasound",
    "mri": "mri",
    "ct": "ct",
    "xray": "xray",
    "ecg": "ecg",
    "histology": "histology",
    "endoscopy": "endoscopy",
}

# Закрытый словарь специальностей для consultation: одно каноническое имя на специальность.
# Новую специальность добавляй сюда (по просьбе пользователя), не придумывай на месте.
SPECIALTIES = {
    "allergist", "angiosurgeon", "cardiologist", "dentist", "dermatologist",
    "endocrinologist", "gastroenterologist", "gynecologist", "hematologist",
    "lor", "mammologist", "nephrologist", "neurologist", "oncologist",
    "ophthalmologist", "orthopedist", "psychiatrist", "pulmonologist",
    "rheumatologist", "surgeon", "therapist", "traumatologist", "urologist",
}

_TYPES_RE = "|".join(sorted(SUFFIX_MAP, key=len, reverse=True))

# Для lint / самопроверки. Тип стоит сразу после даты: `<дата>_<тип>[-<disambiguator>]`.
REGEX = {
    "raw_docs": rf"^\d{{4}}-\d{{2}}-\d{{2}}_({_TYPES_RE})(-[a-z0-9]+)*\.md$",
    "raw_images": rf"^\d{{4}}-\d{{2}}-\d{{2}}_({_TYPES_RE})(-[a-z0-9]+)*-p\d+\.[a-z0-9]+$",
    "raw_articles": r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.md$",
    "wiki_notes": r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.md$",
    "wiki_entities": r"^[a-z0-9]+(-[a-z0-9]+)*\.md$",  # diagnoses, metrics, symptoms, references
}


def _validate_date(date: str) -> None:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")


def _validate_slug(slug: str, field: str = "slug") -> None:
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        raise ValueError(
            f"Invalid {field}: {slug}. Expected kebab-case (lowercase, digits, single hyphens)."
        )


def _validate_disambiguator(disambiguator: str) -> None:
    if disambiguator == "":
        return
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", disambiguator):
        raise ValueError(
            f"Invalid disambiguator: {disambiguator}. Expected kebab-case or a number like 2."
        )


def _validate_consultation_disambiguator(disambiguator: str) -> None:
    """consultation: пусто, число (2, 3…) или специальности из SPECIALTIES (одна или несколько, + необязательное число в конце)."""
    if disambiguator == "":
        return
    parts = disambiguator.split("-")
    if parts and parts[-1].isdigit():
        parts = parts[:-1]
    bad = [p for p in parts if p not in SPECIALTIES]
    if bad or (not parts and not disambiguator.isdigit()):
        raise ValueError(
            f"Unknown specialty in disambiguator: {disambiguator}. "
            f"Allowed: {sorted(SPECIALTIES)} (or a number like 2). "
            "New specialty: add it to SPECIALTIES in naming_logic.py at the user's request."
        )


def format_raw_docs_name(doc_type: str, date: str, disambiguator: str = "") -> str:
    if doc_type not in SUFFIX_MAP:
        raise ValueError(f"Unknown doc_type: {doc_type}. Allowed: {list(SUFFIX_MAP.keys())}")

    _validate_date(date)
    _validate_disambiguator(disambiguator)
    if doc_type == "consultation":
        _validate_consultation_disambiguator(disambiguator)

    suffix = SUFFIX_MAP[doc_type]
    base = f"{date}_{suffix}"
    if disambiguator:
        base = f"{base}-{disambiguator}"
    return f"{base}.md"


def format_raw_images_name(
    doc_type: str, date: str, disambiguator: str = "", page: int = 1, ext: str = "jpg"
) -> str:
    if page < 1:
        raise ValueError(f"Invalid page: {page}. Expected >= 1")
    ext_clean = ext.lstrip(".").lower()
    if not re.match(r"^[a-z0-9]+$", ext_clean):
        raise ValueError(f"Invalid ext: {ext}")
    docs_name = format_raw_docs_name(doc_type, date, disambiguator)
    stem = docs_name[:-3]
    return f"{stem}-p{page}.{ext_clean}"


def format_raw_articles_name(date: str, slug: str) -> str:
    _validate_date(date)
    _validate_slug(slug)
    return f"{date}-{slug}.md"


def format_wiki_note_name(date: str, slug: str) -> str:
    return format_raw_articles_name(date, slug)


def format_wiki_symptom_name(slug: str) -> str:
    """Жалоба — сущность без даты в имени (как диагноз), дата — в тексте страницы."""
    _validate_slug(slug)
    return f"{slug}.md"


def check_name(layer: str, name: str) -> str | None:
    """Проверка существующего имени для lint. None — имя верное, иначе текст ошибки."""
    if layer not in REGEX:
        raise ValueError(f"Unknown layer: {layer}. Allowed: {list(REGEX)}")
    if not re.match(REGEX[layer], name):
        return "не по формату (тип документа сразу после даты: <дата>_<тип>[-<уточнение>])" if layer in ("raw_docs", "raw_images") else "не по формату"
    if layer in ("raw_docs", "raw_images"):
        stem = name.split("_", 1)[1]
        doc_type = next(t for t in sorted(SUFFIX_MAP, key=len, reverse=True) if stem.startswith(t))
        rest = stem[len(doc_type):]
        rest = re.sub(r"\.[a-z0-9]+$", "", rest)
        rest = re.sub(r"-p\d+$", "", rest) if layer == "raw_images" else rest
        disamb = rest.lstrip("-")
        if doc_type == "consultation":
            try:
                _validate_consultation_disambiguator(disamb)
            except ValueError as e:
                return str(e)
    return None


if __name__ == "__main__":
    print("Self-test:")
    print(format_raw_docs_name("lab-panel", "2025-11-22", ""))
    print(format_raw_docs_name("lab-panel", "2025-11-22", "2"))
    print(format_raw_docs_name("consultation", "2025-11-22", "cardiologist"))
    print(format_raw_docs_name("endoscopy", "2025-11-22", "gastro"))
    print(format_raw_docs_name("ct", "2025-02-22", "lumbar"))
    print(format_raw_docs_name("xray", "2025-06-05", "knee"))
    print(format_raw_images_name("lab-panel", "2025-11-22", "", 1, "jpg"))
    print(format_raw_articles_name("2026-06-22", "vitamin-d-overview"))
    print(format_wiki_symptom_name("chest-pain-left-arm"))