"""Shared data models for the Silicon Signal Triage showcase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LogRecord:
    """A normalized event emitted by an EDA regression or signoff job."""

    timestamp: str
    node: str
    tool: str
    job: str
    severity: str
    code: str
    message: str
    raw: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""

        return {
            'timestamp': self.timestamp,
            'node': self.node,
            'tool': self.tool,
            'job': self.job,
            'severity': self.severity,
            'code': self.code,
            'message': self.message,
        }


@dataclass(frozen=True)
class IssueSignature:
    """A stable grouping key for recurring EDA failures."""

    id: str
    category: str
    tool: str
    code: str
    fingerprint: str
    priority: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            'id': self.id,
            'category': self.category,
            'tool': self.tool,
            'code': self.code,
            'fingerprint': self.fingerprint,
            'priority': self.priority,
            'rationale': self.rationale,
        }


@dataclass(frozen=True)
class WorkerNode:
    """A triage worker in a distributed engineering support cluster."""

    id: str
    region: str
    capacity: int = 1
    specialty: tuple[str, ...] = ()

    def normalized_capacity(self) -> int:
        """Return a safe capacity value for weighted scheduling."""

        return max(1, self.capacity)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            'id': self.id,
            'region': self.region,
            'capacity': self.capacity,
            'specialty': list(self.specialty),
        }


@dataclass(frozen=True)
class WorkerResult:
    """A triaged issue assignment and its operational guidance."""

    signature: IssueSignature
    owner: WorkerNode
    records: tuple[LogRecord, ...]
    suggested_action: str
    reproducer_hint: str

    @property
    def blast_radius(self) -> int:
        """Count distinct jobs affected by this signature."""

        return len({record.job for record in self.records})

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            'signature': self.signature.to_dict(),
            'owner': self.owner.to_dict(),
            'records': [record.to_dict() for record in self.records],
            'suggested_action': self.suggested_action,
            'reproducer_hint': self.reproducer_hint,
            'blast_radius': self.blast_radius,
        }


@dataclass(frozen=True)
class ClusterReport:
    """A complete triage pass across one or more EDA logs."""

    assignments: tuple[WorkerResult, ...]
    total_records: int
    ignored_lines: int = 0

    @property
    def top_issue(self) -> WorkerResult | None:
        """Return the highest priority assignment, if any."""

        if not self.assignments:
            return None
        return self.assignments[0]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            'total_records': self.total_records,
            'ignored_lines': self.ignored_lines,
            'assignment_count': len(self.assignments),
            'assignments': [
                assignment.to_dict() for assignment in self.assignments
            ],
        }
