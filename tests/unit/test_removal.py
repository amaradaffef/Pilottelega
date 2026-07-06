"""Tests unitaires de la planification des retraits (logique pure)."""

from __future__ import annotations

from pilottelega.core.models import AccessStatus, Member, TargetGroup
from pilottelega.core.removal import (
    RemovalFilter,
    parse_protected,
    plan_deleted_removal,
    plan_list_removal,
    plan_mass_removal,
    plan_user_removal,
)


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


# ----- Comptes protégés ("mes comptes") --------------------------------------------------


def test_parse_protected_ids_and_usernames():
    ids, usernames = parse_protected("@Moi, autre 12345 t.me/perso https://t.me/@Encore")
    assert ids == frozenset({12345})
    assert usernames == frozenset({"moi", "autre", "perso", "encore"})


def test_parse_protected_empty():
    assert parse_protected("   ") == (frozenset(), frozenset())


def test_protected_username_never_removed_mass():
    me, other = Member(1, "Me"), Member(2, "other")
    groups = [_grp("alpha", [me, other]), _grp("bravo", [me, other])]
    filter_ = RemovalFilter.from_raw("@me")  # casse ignorée
    plan = plan_mass_removal(groups, "@alpha", filter_)
    # « me » est protégé → seul « other » est retiré de bravo.
    assert {(r.group_identifier, r.user_id) for r in plan} == {("@bravo", 2)}


def test_protected_id_never_removed_user_mode():
    me = Member(42, "me")
    groups = [_grp("alpha", [me]), _grp("bravo", [me])]
    filter_ = RemovalFilter.from_raw("42")
    assert plan_user_removal(groups, 42, ["@bravo"], filter_) == []


def test_connected_account_never_removed():
    me, other = Member(1, "aiproseo"), Member(2, "other")
    groups = [_grp("alpha", [me, other]), _grp("bravo", [me, other])]
    filter_ = RemovalFilter(self_user_id=1)  # compte connecté = id 1
    # On ne peut pas se retirer soi-même : seul « other » part de bravo.
    assert {
        (r.group_identifier, r.user_id) for r in plan_mass_removal(groups, "@alpha", filter_)
    } == {("@bravo", 2)}
    assert plan_user_removal(groups, 1, ["@bravo"], filter_) == []


# ----- Comptes supprimés (fantômes) ------------------------------------------------------


def test_plan_deleted_removal_targets_only_deleted_of_group():
    alive = Member(1, "alive")
    ghost1 = Member(2, "", is_deleted=True)
    ghost2 = Member(3, "", is_deleted=True)
    other_ghost = Member(4, "", is_deleted=True)
    groups = [
        _grp("chat2", [alive, ghost1, ghost2]),
        _grp("chat1", [other_ghost]),  # autre groupe : non concerné
    ]
    plan = plan_deleted_removal(groups, "@chat2")
    assert {(r.group_identifier, r.user_id) for r in plan} == {("@chat2", 2), ("@chat2", 3)}


def test_plan_deleted_removal_empty_when_no_ghost():
    groups = [_grp("chat2", [Member(1, "alive")])]
    assert plan_deleted_removal(groups, "@chat2") == []


# ----- Retrait par liste explicite -------------------------------------------------------


def test_plan_list_removal_matches_username_and_id():
    a = Member(1, "alpha")
    bot = Member(2, "spambot", is_bot=True)
    ghost = Member(3, "other")
    groups = [_grp("chat", [a, bot, ghost])]
    ids, usernames = parse_protected("@SpamBot, 1")  # par pseudo (casse ignorée) + par id
    plan = plan_list_removal(groups, "@chat", ids, usernames)
    # alpha (id 1) et spambot (@spambot) ciblés ; les bots listés SONT retirés.
    assert {(r.group_identifier, r.user_id) for r in plan} == {("@chat", 1), ("@chat", 2)}


def test_plan_list_removal_skips_protected_and_self():
    keep = Member(1, "keepme")
    me = Member(2, "myself")
    groups = [_grp("chat", [keep, me])]
    ids, usernames = parse_protected("@keepme @myself")
    filter_ = RemovalFilter(protected_usernames=frozenset({"keepme"}), self_user_id=2)
    # keepme est protégé, myself est le compte connecté → aucun retrait.
    assert plan_list_removal(groups, "@chat", ids, usernames, filter_) == []


def test_plan_list_removal_ignores_accounts_not_in_group():
    a = Member(1, "alpha")
    groups = [_grp("chat", [a])]
    ids, usernames = parse_protected("@ghost 999")  # absents du groupe
    assert plan_list_removal(groups, "@chat", ids, usernames) == []


# ----- Exclusion des bots ----------------------------------------------------------------


def test_bots_excluded_from_mass_removal():
    human, bot = Member(1, "human"), Member(2, "bot", is_bot=True)
    groups = [_grp("alpha", [human, bot]), _grp("bravo", [human, bot])]
    plan = plan_mass_removal(groups, "@alpha", RemovalFilter(exclude_bots=True))
    assert {(r.group_identifier, r.user_id) for r in plan} == {("@bravo", 1)}


def test_bots_kept_when_exclude_disabled():
    bot = Member(2, "bot", is_bot=True)
    groups = [_grp("alpha", [bot]), _grp("bravo", [bot])]
    plan = plan_mass_removal(groups, "@alpha", RemovalFilter(exclude_bots=False))
    assert {(r.group_identifier, r.user_id) for r in plan} == {("@bravo", 2)}


def test_bot_excluded_from_user_mode():
    bot = Member(2, "bot", is_bot=True)
    groups = [_grp("alpha", [bot]), _grp("bravo", [bot])]
    assert plan_user_removal(groups, 2, ["@bravo"], RemovalFilter(exclude_bots=True)) == []
