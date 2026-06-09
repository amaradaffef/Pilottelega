"""Tests unitaires du recoupement (T023 / US3). Logique pure, sans réseau ni Qt."""

from __future__ import annotations

from pilottelega.core.analysis import compute_overlap
from pilottelega.core.models import AccessStatus, Member, TargetGroup


def _group(handle: str, members: list[Member]) -> TargetGroup:
    return TargetGroup(
        raw_input=f"@{handle}",
        identifier=f"@{handle}",
        handle=handle,
        access_status=AccessStatus.FULL,
        members=members,
    )


def test_common_member_in_multi_group():
    alice = Member(1, "alice")
    bob = Member(2, "bob")
    carol = Member(3, "carol")
    g1 = _group("alpha", [alice, bob])
    g2 = _group("bravo", [bob, carol])

    result = compute_overlap([g1, g2])

    multi = {m.user_id: groups for m, groups in result.multi_group}
    assert multi == {2: ["@alpha", "@bravo"]}  # bob présent dans les deux
    single_ids = {m.user_id for m, _ in result.single_group}
    assert single_ids == {1, 3}


def test_no_common_member():
    g1 = _group("alpha", [Member(1, "alice")])
    g2 = _group("bravo", [Member(2, "bob")])
    result = compute_overlap([g1, g2])
    assert result.multi_group == []
    assert {m.user_id for m, _ in result.single_group} == {1, 2}


def test_single_group_all_unique():
    g1 = _group("alpha", [Member(1), Member(2), Member(3)])
    result = compute_overlap([g1])
    assert result.multi_group == []
    assert len(result.single_group) == 3


def test_empty_input():
    result = compute_overlap([])
    assert result.single_group == []
    assert result.multi_group == []


def test_same_member_twice_in_one_group_not_overlap():
    alice = Member(1, "alice")
    g1 = _group("alpha", [alice, alice])
    result = compute_overlap([g1])
    assert result.multi_group == []
    assert len(result.single_group) == 1
