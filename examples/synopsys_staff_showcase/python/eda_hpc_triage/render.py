"""Human-readable report rendering."""

from __future__ import annotations

from eda_hpc_triage.models import ClusterReport


def format_report(report: ClusterReport) -> str:
    """Render a concise incident report for terminal use."""

    lines = [
        "Silicon Signal Triage Report",
        "=" * 29,
        f"Parsed records: {report.total_records}",
        f"Ignored lines: {report.ignored_lines}",
        f"Unique signatures: {len(report.assignments)}",
    ]

    if report.top_issue is None:
        lines.append("No actionable EDA issues were detected.")
        return "\n".join(lines)

    lines.append("")
    for index, assignment in enumerate(report.assignments, start=1):
        signature = assignment.signature
        lines.extend(
            [
                f"{index}. {signature.category} ({signature.id})",
                f"   priority: {signature.priority}",
                f"   owner: {assignment.owner.id} [{assignment.owner.region}]",
                f"   affected jobs: {assignment.blast_radius}",
                f"   records: {len(assignment.records)}",
                f"   tool/code: {signature.tool}/{signature.code}",
                f"   rationale: {signature.rationale}",
                f"   action: {assignment.suggested_action}",
                f"   reproducer: {assignment.reproducer_hint}",
            ]
        )

    return "\n".join(lines)
