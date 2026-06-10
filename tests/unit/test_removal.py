"""Tests unitaires de la planification des retraits (logique pure)."""

from __future__ import annotations

from pilottelega.core.models import AccessStatus, Member, TargetGroup
from pilottelega.core.removal import plan_mass_removal, plan_user_removal


def _grp(handle, members):
    return TargetGroup(
        raw_input=f"@{handle}",
        identifier=f"@{handle}",
        handle=handle,
        access_status=AccessStatus.FULL,
        members=members,
    )


def test_plan_mass_removal_keeps_chosen_group():
    a, b, c = Member(1, "a"), Member(2, "b"), Member(3, "c")
    groups = [_grp("alpha", [a, b]), _grp("bravo", [a, c]), _grp("charlie", [a])]
    plan = plan_mass_removal(groups, "@alpha")
    # a est dans alpha+bravo+charlie → on le retire de bravo et charlie (garde alpha).
    assert {(r.group_identifier, r.user_id) for r in plan} == {("@bravo", 1), ("@charlie", 1)}


def test_plan_mass_skips_member_absent_from_keep():
    a = Member(1, "a")
    groups = [_grp("bravo", [a]), _grp("charlie", [a])]  # a n'est pas dans @alpha
    assert plan_mass_removal(groups, "@alpha") == []


def test_plan_mass_ignores_single_group_members():
    a, b = Member(1, "a"), Member(2, "b")
    assert plan_mass_removal([_grp("alpha", [a, b])], "@alpha") == []


def test_plan_user_removal_only_real_groups():
    a = Member(1, "a")
    groups = [_grp("alpha", [a]), _grp("bravo", [a])]
    plan = plan_user_removal(groups, 1, ["@bravo", "@unknown"])
    assert [(r.group_identifier, r.user_id) for r in plan] == [("@bravo", 1)]


def test_plan_user_removal_unknown_user():
    a = Member(1, "a")
    assert plan_user_removal([_grp("alpha", [a])], 999, ["@alpha"]) == []
