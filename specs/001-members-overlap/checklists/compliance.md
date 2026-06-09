# Compliance & Privacy Requirements Checklist: Pilottelega

**Purpose**: Valider la **qualité des exigences** de conformité (Telegram/RGPD) et de
confidentialité — complétude, clarté, mesurabilité — avant l'implémentation.
**Created**: 2026-06-09
**Feature**: [spec.md](../spec.md) · Constitution Principe II

## Requirement Completeness

- [ ] CHK001 Les exigences précisent-elles **où** et **sous quelle forme** les identifiants (`api_id`/`api_hash`) et la session sont stockés localement ? [Completeness, Spec §FR-003/004]
- [ ] CHK002 Existe-t-il une exigence définissant ce qui doit **ne jamais** sortir du poste (secrets, session) et vers qui ? [Completeness, Spec §FR-004, §SC-006]
- [ ] CHK003 Les exigences couvrent-elles la **suppression/réinitialisation** des identifiants/session (déconnexion, session révoquée) ? [Gap]
- [ ] CHK004 La base légale RGPD (gestion de ses propres communautés) est-elle formulée comme une exigence vérifiable, et non seulement comme un principe ? [Completeness, Spec §FR-019]
- [ ] CHK005 Une exigence définit-elle le comportement attendu lorsqu'un groupe restreint l'accès (membres masqués / admin requis) sans contournement ? [Completeness, Spec §FR-010/011]

## Requirement Clarity & Measurability

- [ ] CHK006 « Jamais embarqués dans l'exe » est-il rendu **objectivement vérifiable** (critère d'inspection du build) ? [Measurability, Spec §SC-006]
- [ ] CHK007 « Légitimement lire » (FR-008) est-il défini avec des critères clairs (rôle/visibilité par groupe) plutôt qu'une formule vague ? [Clarity, Spec §FR-008]
- [ ] CHK008 Les quatre valeurs de statut d'accès (FULL/PARTIAL_HIDDEN/ADMIN_REQUIRED/ERROR) sont-elles définies avec des conditions de déclenchement non ambiguës ? [Clarity, Spec §FR-010]

## Requirement Consistency

- [ ] CHK009 Les exigences de stockage local (spec) sont-elles cohérentes avec le principe « jamais transmis à un tiers » (constitution §II) ? [Consistency]
- [ ] CHK010 L'exigence « lecture seule sur Telegram » est-elle cohérente partout (aucune exigence n'implique une écriture/modification) ? [Consistency, Spec §Assumptions]

## Edge Cases & Exception Coverage

- [ ] CHK011 Une exigence couvre-t-elle la **session expirée/révoquée** (détection + retour onboarding) ? [Edge Case, Spec §Edge Cases]
- [ ] CHK012 Le comportement est-il spécifié si les identifiants saisis sont **invalides** ou laissés vides ? [Edge Case, Spec §Edge Cases]
- [ ] CHK013 Les exigences précisent-elles que les secrets ne doivent **jamais** apparaître dans les journaux (`logging`) ? [Gap]

## Traceability

- [ ] CHK014 Chaque exigence de confidentialité est-elle reliée à un critère de succès mesurable (SC) ou à un principe de la constitution ? [Traceability]
- [ ] CHK015 Le périmètre post-MVP (chiffrement du stockage local) est-il explicitement marqué hors périmètre pour éviter toute ambiguïté de conformité ? [Clarity, Spec §Assumptions]

## Notes

- Cocher `[x]` quand l'exigence correspondante est jugée complète/claire.
- Gaps notables identifiés en analyse : FR-018 (en mémoire, implicite) et FR-019 (conformité, couverture douce).
