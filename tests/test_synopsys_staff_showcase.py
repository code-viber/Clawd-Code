from pathlib import Path
import sys


SHOWCASE_PYTHON = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "synopsys_staff_showcase"
    / "python"
)
sys.path.insert(0, str(SHOWCASE_PYTHON))

from eda_hpc_triage.parser import parse_log_lines
from eda_hpc_triage.scheduler import DEFAULT_WORKERS, RendezvousScheduler, build_report
from eda_hpc_triage.signatures import build_signature, normalize_message


def test_parse_log_lines_keeps_good_records_and_ignores_bad_lines():
    records, ignored = parse_log_lines(
        [
            "[2026-05-07T04:12:01Z] node=linux-eda-17 tool=prime_time "
            'job=cpu_top severity=ERROR code=TIM-120 message="negative slack '
            '-0.18 ns on path U_TOP/u_cpu/u_alu"',
            "legacy line without structured fields",
        ]
    )

    assert len(records) == 1
    assert records[0].severity == "ERROR"
    assert records[0].tool == "prime_time"
    assert ignored == ["legacy line without structured fields"]


def test_normalize_message_removes_numeric_noise_for_stable_signatures():
    first = normalize_message("negative slack -0.18 ns on path U_TOP/u_cpu/u_alu")
    second = normalize_message("negative slack -0.21 ns on path U_TOP/u_cpu/u_alu")

    assert first == second
    assert "<num>" in first


def test_build_report_groups_related_failures_and_ranks_crashes_first():
    records, ignored = parse_log_lines(
        [
            "[2026-05-07T04:12:01Z] node=linux-eda-17 tool=prime_time "
            'job=cpu_top_ss severity=ERROR code=TIM-120 message="negative '
            'slack -0.18 ns on path U_TOP/u_cpu/u_alu"',
            "[2026-05-07T04:12:08Z] node=linux-eda-21 tool=prime_time "
            'job=cpu_top_ff severity=ERROR code=TIM-120 message="negative '
            'slack -0.21 ns on path U_TOP/u_cpu/u_alu"',
            "[2026-05-07T04:13:11Z] node=linux-eda-09 tool=vcs "
            'job=soc_reset severity=FATAL code=SEG-011 message="segmentation '
            'fault after elaboration core dumped pid 84421"',
        ]
    )

    report = build_report(records, ignored_lines=len(ignored))

    assert report.total_records == 3
    assert report.ignored_lines == 0
    assert len(report.assignments) == 2
    assert report.top_issue is not None
    assert report.top_issue.signature.category == "tool-crash"
    timing_assignment = [
        assignment
        for assignment in report.assignments
        if assignment.signature.category == "timing-closure"
    ][0]
    assert timing_assignment.blast_radius == 2


def test_rendezvous_scheduler_is_deterministic_for_same_signature():
    records, _ = parse_log_lines(
        [
            "[2026-05-07T04:13:11Z] node=linux-eda-09 tool=vcs "
            'job=soc_reset severity=FATAL code=SEG-011 message="segmentation '
            'fault after elaboration core dumped pid 84421"',
        ]
    )
    signature = build_signature(records[0])
    scheduler = RendezvousScheduler(DEFAULT_WORKERS)

    first_owner = scheduler.assign(signature.id, signature.category)
    second_owner = scheduler.assign(signature.id, signature.category)

    assert first_owner == second_owner
    assert "tool-crash" in first_owner.specialty
