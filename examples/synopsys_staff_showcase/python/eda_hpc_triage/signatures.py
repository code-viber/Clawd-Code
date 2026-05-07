"""Failure classification and signature generation."""

from __future__ import annotations

import hashlib
import re

from eda_hpc_triage.models import IssueSignature, LogRecord


NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
PATH_RE = re.compile(r"\b(?:/[A-Za-z0-9_.:-]+){2,}\b")
SPACE_RE = re.compile(r"\s+")

CATEGORY_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "timing-closure",
        ("slack", "setup", "hold", "tim-", "clock"),
        "Timing keywords indicate a signoff-quality closure issue.",
    ),
    (
        "tool-crash",
        ("segmentation", "segfault", "core dumped", "fatal signal", "crash"),
        "Crash markers require rapid containment and reproducer capture.",
    ),
    (
        "license-infra",
        ("license", "lmgrd", "checkout", "lic-"),
        "License checkout failures usually affect broad engineering velocity.",
    ),
    (
        "storage-io",
        ("nfs", "stale file", "permission denied", "io-", "filesystem"),
        "Shared storage and filesystem issues can fan out across job farms.",
    ),
    (
        "design-database",
        ("corrupt", "schema", "db-", "database", "checkpoint"),
        "Database integrity issues need controlled recovery and audit trails.",
    ),
)

SEVERITY_WEIGHTS = {
    "CRITICAL": 100,
    "FATAL": 95,
    "ERROR": 80,
    "WARN": 40,
    "WARNING": 40,
    "INFO": 10,
}

CATEGORY_BOOSTS = {
    "tool-crash": 12,
    "timing-closure": 10,
    "license-infra": 8,
    "design-database": 8,
    "storage-io": 6,
    "unknown": 0,
}


def build_signature(record: LogRecord) -> IssueSignature:
    """Create a deterministic failure signature for one log record."""

    category, rationale = classify(record)
    fingerprint = normalize_message(record.message)
    digest = hashlib.blake2b(
        f"{record.tool}|{record.code}|{category}|{fingerprint}".encode("utf-8"),
        digest_size=8,
    ).hexdigest()

    return IssueSignature(
        id=f"{category}:{digest}",
        category=category,
        tool=record.tool,
        code=record.code,
        fingerprint=fingerprint,
        priority=priority_for(record, category),
        rationale=rationale,
    )


def classify(record: LogRecord) -> tuple[str, str]:
    """Classify an EDA event into an operational category."""

    haystack = f"{record.code} {record.message}".lower()
    for category, needles, rationale in CATEGORY_RULES:
        if any(needle in haystack for needle in needles):
            return category, rationale
    return "unknown", "No known category matched; route to first-response triage."


def normalize_message(message: str) -> str:
    """Normalize variable values while preserving debugging context."""

    lowered = message.lower()
    without_paths = PATH_RE.sub("<path>", lowered)
    without_numbers = NUMBER_RE.sub("<num>", without_paths)
    collapsed = SPACE_RE.sub(" ", without_numbers).strip()
    tokens = collapsed.split(" ")
    return " ".join(tokens[:16])


def priority_for(record: LogRecord, category: str) -> int:
    """Score an event for triage ordering."""

    severity = SEVERITY_WEIGHTS.get(record.severity.upper(), 10)
    boost = CATEGORY_BOOSTS.get(category, 0)
    return severity + boost
