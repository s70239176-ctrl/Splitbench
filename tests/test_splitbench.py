"""Portable assertions for Splitbench's deterministic accounting rules.

Run full direct-mode tests after installing GenLayer Test. These checks keep the
critical bps and source-level protocol guards testable in this empty workspace.
"""

from pathlib import Path


def payout(total: int, awarded_bps: int) -> int:
    return total * awarded_bps // 10_000


def test_partial_payout_exact_units():
    # total=10000, a 4000-bps milestone awarded 2500 bps pays 2500.
    assert payout(10_000, 2_500) == 2_500


def test_partial_payout_wei_scale():
    assert payout(10**18, 2_500) == 250_000_000_000_000_000


def test_contract_has_required_deterministic_guards():
    source = Path("contracts/splitbench.py").read_text(encoding="utf-8")
    assert 'milestone weights must sum to 10000' in source
    assert 'only provider can submit' in source
    assert 'settle requires matching attested finalized adjudicate tx' in source
    assert 'deadline has not passed' in source
    assert 'AGENT jobs require both agent ids' in source
    assert 'run_nondet_unsafe(jury, validator)' in source
    assert '@gl.public.write.payable' in source
