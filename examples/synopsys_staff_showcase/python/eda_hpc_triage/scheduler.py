"""Deterministic distributed scheduling for EDA issue ownership."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from eda_hpc_triage.models import ClusterReport, LogRecord, WorkerNode, WorkerResult
from eda_hpc_triage.signatures import build_signature


DEFAULT_WORKERS = (
    WorkerNode(
        id="cec-silicon-debug-us",
        region="us-west",
        capacity=4,
        specialty=("tool-crash", "design-database"),
    ),
    WorkerNode(
        id="cec-timing-platform",
        region="us-west",
        capacity=3,
        specialty=("timing-closure",),
    ),
    WorkerNode(
        id="cec-infra-follow-sun",
        region="global",
        capacity=5,
        specialty=("license-infra", "storage-io"),
    ),
)

SUGGESTED_ACTIONS = {
    "timing-closure": (
        "Collect violating path group, clock constraints, and recent ECO deltas; "
        "route to timing owner with reproducible seed."
    ),
    "tool-crash": (
        "Freeze tool build, capture core file metadata, symbolized stack, and "
        "minimal failing testcase before rerunning."
    ),
    "license-infra": (
        "Check license server health, checkout saturation, and token pools before "
        "retrying job arrays."
    ),
    "storage-io": (
        "Validate mount health, NFS error counters, and workspace permissions on "
        "affected nodes."
    ),
    "design-database": (
        "Quarantine checkpoint, compare schema version, and restore from last "
        "known-good database snapshot."
    ),
    "unknown": (
        "Assign to first-response triage with raw log, command line, and runtime "
        "environment."
    ),
}

REPRODUCER_HINTS = {
    "timing-closure": "rerun signoff with failing corner and -keep_path_report",
    "tool-crash": "rerun under gdb or lldb with debug symbols and core dumps enabled",
    "license-infra": "run license checkout probe from same host and container image",
    "storage-io": "run filesystem probe from impacted node before cleanup",
    "design-database": "open checkpoint read-only and export schema audit",
    "unknown": "capture command, environment, input manifest, and last 200 log lines",
}


class RendezvousScheduler:
    """Weighted rendezvous hashing for stable distributed ownership.

    This keeps most assignments stable when workers are added or removed, which is
    useful for long-running EDA support queues where ownership churn is costly.
    """

    def __init__(self, workers: Iterable[WorkerNode]) -> None:
        """Initialize the scheduler with at least one worker."""

        self.workers = tuple(workers)
        if not self.workers:
            raise ValueError("at least one worker is required")

    def assign(self, signature_id: str, category: str) -> WorkerNode:
        """Assign a signature to the best worker."""

        return max(
            self.workers,
            key=lambda worker: _weighted_score(signature_id, category, worker),
        )


def build_report(
    records: Iterable[LogRecord],
    ignored_lines: int = 0,
    workers: Iterable[WorkerNode] = DEFAULT_WORKERS,
) -> ClusterReport:
    """Group parsed events into deterministic distributed triage assignments."""

    grouped: dict[str, list[LogRecord]] = defaultdict(list)
    signatures = {}

    record_count = 0
    for record in records:
        record_count += 1
        signature = build_signature(record)
        signatures[signature.id] = signature
        grouped[signature.id].append(record)

    scheduler = RendezvousScheduler(workers)
    assignments: list[WorkerResult] = []
    for signature_id, signature_records in grouped.items():
        signature = signatures[signature_id]
        category = signature.category
        owner = scheduler.assign(signature.id, category)
        assignments.append(
            WorkerResult(
                signature=signature,
                owner=owner,
                records=tuple(signature_records),
                suggested_action=SUGGESTED_ACTIONS[category],
                reproducer_hint=REPRODUCER_HINTS[category],
            )
        )

    assignments.sort(
        key=lambda assignment: (
            -assignment.signature.priority,
            -assignment.blast_radius,
            assignment.signature.id,
        )
    )
    return ClusterReport(
        assignments=tuple(assignments),
        total_records=record_count,
        ignored_lines=ignored_lines,
    )


def load_workers(path: Path) -> tuple[WorkerNode, ...]:
    """Load worker topology from a JSON file."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        WorkerNode(
            id=item["id"],
            region=item["region"],
            capacity=int(item.get("capacity", 1)),
            specialty=tuple(item.get("specialty", ())),
        )
        for item in data["workers"]
    )


def _weighted_score(signature_id: str, category: str, worker: WorkerNode) -> int:
    digest = hashlib.blake2b(
        f"{signature_id}|{worker.id}".encode("utf-8"),
        digest_size=8,
    ).digest()
    base_score = int.from_bytes(digest, byteorder="big")
    specialty_multiplier = 3 if category in worker.specialty else 1
    return base_score * worker.normalized_capacity() * specialty_multiplier
