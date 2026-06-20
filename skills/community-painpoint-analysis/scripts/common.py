from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

SOURCE_COLUMNS = [
    "site",
    "post_id",
    "board_code",
    "board_name",
    "category_name",
    "title",
    "author",
    "posted_at",
    "url",
    "view_count",
    "like_count",
    "dislike_count",
    "comment_count",
    "matched_queries",
    "matched_search_urls",
    "search_pages",
    "search_excerpt",
    "body_text",
    "comments_text",
    "comments_json",
    "crawl_status",
    "crawl_error",
]

CHUNK_COLUMNS = [
    "record_id",
    "source_file",
    "source_row_number",
    *SOURCE_COLUMNS,
]

LABEL_COLUMNS = [
    "record_id",
    "is_relevant",
    "irrelevant_reason",
    "user_context",
    "journey_stage",
    "jtbd",
    "primary_pain_point",
    "secondary_pain_point",
    "sentiment",
    "severity",
    "segment_candidate",
    "evidence_quote",
    "confidence",
    "needs_review",
]

SENTIMENT_VALUES = {"부정", "중립", "긍정", "혼합"}
SEVERITY_VALUES = {"낮음", "중간", "높음"}
CONFIDENCE_VALUES = {"낮음", "중간", "높음"}
IRRELEVANT_REASON_VALUES = {
    "promotional_or_deal",
    "news_or_investor",
    "generic_chatter",
    "non_consumer_context",
    "insufficient_signal",
}

MERGED_COLUMNS = [
    "record_id",
    "source_file",
    "source_row_number",
    "site",
    "post_id",
    "title",
    "posted_at",
    "url",
    "matched_queries",
    *[column for column in LABEL_COLUMNS if column != "record_id"],
]

TEXT_COLUMNS = ["title", "search_excerpt", "body_text", "comments_text"]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}: malformed CSV row at line {row_number}")
            rows.append({key: value or "" for key, value in row.items()})
        return list(reader.fieldnames or []), rows


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def has_meaningful_text(row: dict[str, str]) -> bool:
    return any(normalize_space(row.get(column, "")) for column in TEXT_COLUMNS)


def content_fingerprint(row: dict[str, str]) -> str:
    text = normalize_space(" ".join(row.get(column, "") for column in TEXT_COLUMNS)).lower()
    if not text:
        return ""
    return hashlib.sha1(text[:1000].encode("utf-8")).hexdigest()[:12]


def stable_key(row: dict[str, str], source_file: Path, source_row_number: int) -> str:
    site = normalize_space(row.get("site", ""))
    post_id = normalize_space(row.get("post_id", ""))
    board_code = normalize_space(row.get("board_code", ""))
    url = normalize_space(row.get("url", ""))
    if site and post_id:
        parts = [site]
        if board_code:
            parts.append(board_code)
        parts.append(post_id)
        key = ":".join(parts)
        if url:
            return f"{key}:url:{url}"
        return key
    if url:
        return f"url:{url}"
    return f"source:{source_file.as_posix()}:{source_row_number}"


def stable_record_id(key: str) -> str:
    return "rec_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def missing_columns(header: list[str], required: list[str]) -> list[str]:
    present = set(header)
    return [column for column in required if column not in present]


def parse_bool(value: str) -> bool | None:
    normalized = normalize_space(value).lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return None
