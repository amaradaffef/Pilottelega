# UX & Flow Requirements Checklist: Pilottelega

**Purpose**: Valider la **qualité des exigences** d'expérience utilisateur (onboarding,
récupération, analyse, réactivité) — complétude, clarté, cohérence.
**Created**: 2026-06-09
**Feature**: [spec.md](../spec.md)

## Requirement Completeness — Onboarding (US1)

- [ ] CHK001 Le contenu attendu de l'écran d'onboarding (explication, lien, champs, code, 2FA) est-il entièrement spécifié ? [Completeness, Spec §FR-001/002]
- [ ] CHK002 L'enchaînement des étapes de login (code → 2FA conditionnelle) est-il défini sans ambiguïté ? [Clarity, Spec §US1, data-model §State transitions]
- [ ] CHK003 L'exigence de **non-ressaisie** au 2ᵉ lancement est-elle formulée de façon mesurable ? [Measurability, Spec §SC-002]

## Requirement Completeness — Récupération & onglets (US2)

- [ ] CHK004 Les formes de liens acceptées (`@nom`, `t.me/...`, id, invite) sont-elles toutes énumérées dans les exigences ? [Completeness, Spec §FR-006]
- [ ] CHK005 L'affichage d'un membre sans `@username` (libellé de repli) est-il spécifié ? [Edge Case, Spec §FR-012, data-model §Member]
- [ ] CHK006 La présentation du **statut d'accès** par onglet est-elle définie pour chacune des 4 valeurs ? [Completeness, Spec §FR-010]

## Requirement Completeness — Analyse (US3)

- [ ] CHK007 Le contenu des deux vues d'analyse (un seul groupe / multi-groupes + liste `@groupes`) est-il spécifié sans ambiguïté ? [Clarity, Spec §FR-013/014]
- [ ] CHK008 Le comportement de rafraîchissement de l'onglet Analyse après de nouvelles récupérations est-il défini ? [Gap, Spec §US3]

## Requirement Clarity — Réactivité

- [ ] CHK009 « L'interface reste réactive / aucun gel » est-il quantifié (seuil de latence perceptible) dans les exigences ? [Ambiguity, Spec §SC-005]
- [ ] CHK010 Les exigences imposent-elles un **indicateur de progression** pendant les opérations réseau ? [Completeness, Spec §FR-016]

## Requirement Consistency

- [ ] CHK011 La terminologie d'affichage des groupes (`@handle` / titre / identifiant) est-elle cohérente entre spec, data-model et contracts ? [Consistency]
- [ ] CHK012 Les exigences d'états d'erreur sont-elles cohérentes entre onboarding, récupération et analyse ? [Consistency, Spec §FR-017]

## Scenario Coverage

- [ ] CHK013 Les exigences couvrent-elles l'état « aucun groupe » / « un seul groupe » côté UI Analyse ? [Coverage, Spec §Edge Cases]
- [ ] CHK014 Le retour visuel pour une **ligne de lien invalide** (sans interrompre le lot) est-il spécifié ? [Coverage, Spec §FR-007]
- [ ] CHK015 Les états de chargement asynchrone (pendant fetch) sont-ils définis comme exigence et non laissés implicites ? [Gap]

## Notes

- Checklist orientée **qualité des exigences UX**, pas test d'interface.
- CHK009 partiellement mitigé par plan.md (~100 ms) ; vérifier que la spec elle-même reste explicite.
