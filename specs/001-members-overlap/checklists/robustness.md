# Robustness & Edge Cases Requirements Checklist: Pilottelega

**Purpose**: Valider la **qualité des exigences** de robustesse (erreurs, cas limites,
volumes, récupération) — complétude et mesurabilité.
**Created**: 2026-06-09
**Feature**: [spec.md](../spec.md)

## Exception Flow Coverage

- [ ] CHK001 Les exigences définissent-elles le comportement en cas d'**interruption réseau** pendant la récupération (groupe en erreur, autres préservés) ? [Exception Flow, Spec §FR-007/017, §Edge Cases]
- [ ] CHK002 Le traitement d'une **session expirée/révoquée** en cours d'usage est-il spécifié ? [Recovery, Spec §Edge Cases]
- [ ] CHK003 Les exigences couvrent-elles les erreurs d'authentification (mauvais code, mauvais mot de passe 2FA) avec message clair et reprise ? [Exception Flow, Spec §FR-017]
- [ ] CHK004 Le comportement hors connexion (réseau Telegram indisponible) est-il défini sans plantage ? [Edge Case, Spec §Constraints]

## Edge Case Coverage — Données

- [ ] CHK005 La **déduplication** d'un même groupe saisi deux fois est-elle exigée explicitement ? [Edge Case, Spec §FR-015]
- [ ] CHK006 Le cas « 0 / 1 groupe » est-il spécifié pour l'analyse (tous les membres uniques) ? [Edge Case, Spec §Edge Cases]
- [ ] CHK007 Le cas « aucun membre commun » (vue multi-groupes vide) est-il une exigence vérifiable ? [Coverage, Spec §US3]
- [ ] CHK008 L'identification stable d'un membre via `user_id` (indépendante du `@username`) est-elle exigée sans ambiguïté ? [Clarity, Spec §FR-012]

## Non-Functional / Volume

- [ ] CHK009 Les exigences précisent-elles un **ordre de grandeur** de volume supporté (nb de groupes / membres) ? [Clarity, Spec §Assumptions]
- [ ] CHK010 Le comportement attendu sur un **groupe très volumineux** (réactivité + progression) est-il spécifié comme exigence ? [Coverage, Spec §Edge Cases]
- [ ] CHK011 La contrainte « traitement en mémoire, aucune persistance des membres » est-elle formulée comme exigence vérifiable ? [Completeness, Spec §FR-018]

## Error Handling Quality

- [ ] CHK012 Chaque mode d'échec a-t-il une exigence de message utilisateur **clair et actionnable** (pas seulement « erreur ») ? [Clarity, Spec §FR-017]
- [ ] CHK013 Les exigences imposent-elles l'usage de `logging` (et non `print`) pour tracer erreurs/événements sans exposer de secret ? [Completeness, Constitution §Standards]
- [ ] CHK014 L'isolement des échecs entre groupes (l'erreur de l'un n'arrête pas les autres) est-il exigé explicitement ? [Consistency, Spec §FR-007]

## Traceability & Assumptions

- [ ] CHK015 Les hypothèses de robustesse (réseau requis, mono-utilisateur local, lecture seule) sont-elles documentées et vérifiables ? [Assumption, Spec §Assumptions]

## Notes

- Items = qualité des **exigences** de robustesse, pas exécution de tests.
- Croiser avec les tests prévus T011/T017 (statuts d'accès) et T016/T023 (cas limites parsing/analyse).
