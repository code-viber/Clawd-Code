"""Small profiling helpers for local performance experiments."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Iterable

from eda_hpc_triage.models import ClusterReport
from eda_hpc_triage.parser import parse_log_lines
from eda_hpc_triage.scheduler import build_report


@dataclass(frozen=True)
class PipelineTiming:
    """Timing data for one triage pipeline run."""

    parse_seconds: float
    triage_seconds: float
    report: ClusterReport

    @property
    def total_seconds(self) -> float:
        """Return total measured runtime."""

        return self.parse_seconds + self.triage_seconds


def time_pipeline(lines: Iterable[str]) -> PipelineTiming:
    """Measure parser and triage latency using a monotonic clock."""

    snapshot = tuple(lines)

    parse_start = perf_counter()
    records, ignored = parse_log_lines(snapshot)
    parse_seconds = perf_counter() - parse_start

    triage_start = perf_counter()
    report = build_report(records, ignored_lines=len(ignored))
    triage_seconds = perf_counter() - triage_start

    return PipelineTiming(
        parse_seconds=parse_seconds,
        triage_seconds=triage_seconds,
        report=report,
    )
