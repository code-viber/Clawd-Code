"""Parsers for structured EDA job logs."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Iterable

from eda_hpc_triage.models import LogRecord


REQUIRED_FIELDS = frozenset({"node", "tool", "job", "severity", "code", "message"})


def parse_log_lines(lines: Iterable[str]) -> tuple[list[LogRecord], list[str]]:
    """Parse EDA log lines into records.

    Expected input format:

        [timestamp] node=... tool=... job=... severity=... code=... message="..."

    Args:
        lines: Raw lines from one or more logs.

    Returns:
        A tuple of parsed records and ignored raw lines.
    """

    records: list[LogRecord] = []
    ignored: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        timestamp, payload = _split_timestamp(line)
        if timestamp is None:
            ignored.append(line)
            continue

        fields = _parse_key_values(payload)
        if not REQUIRED_FIELDS.issubset(fields):
            ignored.append(line)
            continue

        records.append(
            LogRecord(
                timestamp=timestamp,
                node=fields["node"],
                tool=fields["tool"],
                job=fields["job"],
                severity=fields["severity"].upper(),
                code=fields["code"],
                message=fields["message"],
                raw=line,
            )
        )

    return records, ignored


def parse_log_file(path: Path) -> tuple[list[LogRecord], list[str]]:
    """Parse a UTF-8 log file from disk."""

    return parse_log_lines(path.read_text(encoding="utf-8").splitlines())


def _split_timestamp(line: str) -> tuple[str | None, str]:
    if not line.startswith("["):
        return None, line

    close_index = line.find("]")
    if close_index < 0:
        return None, line

    timestamp = line[1:close_index].strip()
    payload = line[close_index + 1 :].strip()
    if not timestamp or not payload:
        return None, line
    return timestamp, payload


def _parse_key_values(payload: str) -> dict[str, str]:
    try:
        parts = shlex.split(payload)
    except ValueError:
        return {}

    fields: dict[str, str] = {}
    for part in parts:
        key, separator, value = part.partition("=")
        if separator and key:
            fields[key] = value
    return fields
