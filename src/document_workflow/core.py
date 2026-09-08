"""Text extraction and keyword classification."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json"}


class RulesError(ValueError):
    """Raised when a rules file is invalid."""


@dataclass(frozen=True)
class CategoryRule:
    name: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class Rules:
    categories: tuple[CategoryRule, ...]
    fallback: str


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _is_safe_category(value: str) -> bool:
    return (
        bool(value.strip())
        and value not in {".", ".."}
        and Path(value).name == value
        and "/" not in value
        and "\\" not in value
    )


def extract_text(path: Path) -> str:
    """Extract normalized text from a supported UTF-8 document."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix or '<none>'}")
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as stream:
            text = " ".join(cell for row in csv.reader(stream) for cell in row)
    elif suffix == ".json":
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = path.read_text(encoding="utf-8")
    return _normalize(text)


def load_rules(path: Path) -> Rules:
    """Load validated keyword rules from JSON."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        fallback = value["fallback"]
        categories = value["categories"]
        if not isinstance(fallback, str) or not _is_safe_category(fallback):
            raise TypeError
        parsed = []
        for item in categories:
            name = item["name"]
            keywords = item["keywords"]
            if not isinstance(name, str) or not _is_safe_category(name):
                raise TypeError
            if not isinstance(keywords, list) or not all(
                isinstance(keyword, str) and keyword.strip() for keyword in keywords
            ):
                raise TypeError
            parsed.append(CategoryRule(name.strip(), tuple(keyword.strip().lower() for keyword in keywords)))
        return Rules(tuple(parsed), fallback.strip())
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RulesError(f"Invalid rules file: {path}") from error


def classify_text(text: str, rules: Rules) -> str:
    """Return the first category whose keyword occurs in normalized text."""
    lowered = re.sub(r"\s+", " ", text.lower())
    for category in rules.categories:
        if any(keyword in lowered for keyword in category.keywords):
            return category.name
    return rules.fallback
