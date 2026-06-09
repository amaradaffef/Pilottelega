# Feature Specification: Pilottelega — Membres & recoupement de groupes Telegram

**Feature Branch**: `001-members-overlap`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "Application desktop Windows « Pilottelega » qui récupère les membres des groupes Telegram accessibles à l'utilisateur et analyse leurs recoupements entre plusieurs groupes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Premier lancement : connexion sécurisée à Telegram (Priority: P1)

Au tout premier lancement, l'utilisateur est guidé pour relier l'application à son
compte Telegram. Un écran d'onboarding lui explique qu'un identifiant d'accès
personnel et gratuit est nécessaire, fournit un lien vers la page officielle de
génération, puis lui demande de saisir cet identifiant, son numéro de téléphone, le
code reçu et, le cas échéant, son mot de passe à double facteur. Une fois connecté,
la session est mémorisée localement : les lancements suivants ouvrent directement
l'application sans redemander ces informations.

**Why this priority**: Sans connexion au compte, aucune donnée ne peut être lue.
C'est le socle prérequis de toute la valeur de l'application et le point le plus
sensible (vie privée, identifiants).

**Independent Test**: Sur une machine vierge, lancer l'application, suivre
l'onboarding jusqu'à la connexion réussie, fermer puis rouvrir : la deuxième
ouverture ne redemande rien et affiche l'écran principal.

**Acceptance Scenarios**:

1. **Given** une première installation sans session enregistrée, **When** l'utilisateur ouvre l'application, **Then** l'écran d'onboarding s'affiche avec l'explication et le lien vers la page de génération de l'identifiant d'accès.
2. **Given** l'écran d'onboarding, **When** l'utilisateur saisit un identifiant d'accès valide, son numéro, le code reçu (et le mot de passe 2FA si activé), **Then** la connexion réussit et la session est enregistrée localement.
3. **Given** une session déjà enregistrée, **When** l'utilisateur rouvre l'application, **Then** l'écran principal s'ouvre directement sans nouvelle saisie.
4. **Given** un identifiant d'accès, un code ou un mot de passe incorrect, **When** l'utilisateur valide, **Then** un message d'erreur clair s'affiche et la saisie peut être corrigée sans planter l'application.

---

### User Story 2 - Saisir des groupes et récupérer leurs membres (Priority: P2)

Depuis l'écran principal, l'utilisateur colle une liste de liens de groupes (un par
ligne, sous différentes formes : `@nom`, `t.me/...`, identifiant). L'application
valide/normalise chaque entrée puis récupère la liste des membres de chaque groupe.
Un onglet par groupe affiche ses membres ainsi qu'un **statut d'accès** indiquant
dans quelle mesure la liste a pu être lue (complète, partielle car membres masqués,
ou nécessitant des droits d'administrateur).

**Why this priority**: C'est l'acquisition des données sans laquelle l'analyse de
recoupement n'a pas de matière. Le statut d'accès garantit la transparence et la
conformité (ne jamais prétendre lire ce qui n'est pas accessible).

**Independent Test**: Coller plusieurs liens de groupes accessibles, lancer la
récupération, vérifier qu'un onglet par groupe apparaît avec la liste des membres et
le statut d'accès correspondant à la réalité de chaque groupe.

**Acceptance Scenarios**:

1. **Given** l'écran principal, **When** l'utilisateur colle plusieurs liens (un par ligne) et lance la récupération, **Then** chaque lien valide devient une cible et un onglet par groupe est créé.
2. **Given** un groupe où l'utilisateur a un accès complet, **When** la récupération se termine, **Then** l'onglet affiche tous les membres avec le statut « accès complet ».
3. **Given** un groupe où les membres sont masqués ou réservés aux administrateurs, **When** la récupération se termine, **Then** l'onglet affiche les membres disponibles (éventuellement aucun) avec un statut explicite (« membres masqués » / « droits administrateur requis »).
4. **Given** une entrée invalide ou un groupe introuvable, **When** la récupération s'exécute, **Then** l'entrée est signalée comme invalide sans interrompre le traitement des autres groupes.
5. **Given** une récupération en cours, **When** elle interroge le réseau, **Then** l'interface reste réactive (pas de gel) et indique la progression.

---

### User Story 3 - Analyser les recoupements entre groupes (Priority: P3)

Un onglet « Analyse » croise les listes de membres récupérées et présente deux vues :
les membres présents dans **un seul** des groupes listés, et les membres présents
dans **plusieurs** groupes — avec, pour chacun de ces derniers, la liste des
`@groupes` où il apparaît également. C'est le cœur de la valeur du produit.

**Why this priority**: C'est le résultat final recherché par l'utilisateur. Il dépend
des deux histoires précédentes mais constitue la finalité de l'application.

**Independent Test**: Avec au moins deux groupes récupérés ayant des membres communs,
ouvrir l'onglet Analyse et vérifier qu'un membre commun apparaît dans la vue
« multi-groupes » avec la liste correcte des groupes, et qu'un membre exclusif
apparaît dans la vue « un seul groupe ».

**Acceptance Scenarios**:

1. **Given** au moins deux groupes récupérés, **When** l'utilisateur ouvre l'onglet Analyse, **Then** une vue liste les membres présents dans un seul groupe et une autre liste les membres présents dans plusieurs groupes.
2. **Given** un membre présent dans plusieurs groupes, **When** il apparaît dans la vue multi-groupes, **Then** la liste des `@groupes` où il figure est affichée à côté de lui et correspond exactement aux groupes le contenant.
3. **Given** un membre présent dans un seul groupe, **When** l'analyse s'exécute, **Then** il apparaît uniquement dans la vue « un seul groupe ».
4. **Given** des groupes sans aucun membre commun, **When** l'analyse s'exécute, **Then** la vue multi-groupes est vide et tous les membres figurent dans la vue « un seul groupe ».

---

### Edge Cases

- **Aucun groupe / un seul groupe saisi** : l'analyse de recoupement reste cohérente (avec un seul groupe, tous les membres sont « uniques »).
- **Même groupe saisi deux fois** : il est dédupliqué, pas compté comme un recoupement artificiel.
- **Groupe très volumineux** : l'interface reste réactive et signale la progression ; le périmètre MVP n'impose pas de pagination persistée.
- **Interruption réseau ou déconnexion en cours de récupération** : le groupe concerné est marqué en erreur, les autres ne sont pas perdus.
- **Membre sans `@username`** : il est tout de même identifié de façon stable et affiché via un libellé de repli (nom affiché ou identifiant).
- **Session expirée / révoquée** : l'application détecte l'échec d'authentification et propose de refaire l'onboarding.
- **Identifiant d'accès laissé vide ou mal copié** : message d'erreur clair, pas de blocage définitif.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Au premier lancement (aucune session locale), l'application MUST afficher un écran d'onboarding expliquant qu'un identifiant d'accès Telegram personnel et gratuit est requis, avec un lien vers la page officielle de génération.
- **FR-002**: L'application MUST permettre la saisie de l'identifiant d'accès, du numéro de téléphone, du code de connexion et du mot de passe à double facteur (si activé), puis établir la connexion au compte.
- **FR-003**: L'application MUST enregistrer la session **localement** sur le poste de l'utilisateur après une connexion réussie, et NE doit PAS redemander les informations aux lancements suivants tant que la session est valide.
- **FR-004**: Les identifiants d'accès et la session NE doivent JAMAIS être embarqués dans le logiciel distribué ni transmis à un tiers ; ils restent stockés uniquement en local.
- **FR-005**: L'application MUST détecter au démarrage l'existence d'une session valide : si oui → écran principal ; si non → onboarding.
- **FR-006**: L'écran principal MUST permettre de saisir/coller plusieurs liens de groupes, un par ligne, et accepter les formes courantes (`@nom`, lien `t.me`, identifiant).
- **FR-007**: L'application MUST normaliser chaque entrée en une cible exploitable et signaler les entrées invalides ou introuvables sans interrompre le traitement des autres.
- **FR-008**: L'application MUST récupérer la liste des membres de chaque groupe cible dans la limite de ce que le compte connecté peut **légitimement** lire.
- **FR-009**: L'application MUST afficher un **onglet par groupe** présentant ses membres récupérés.
- **FR-010**: Chaque onglet de groupe MUST afficher un **statut d'accès** explicite (accès complet / membres masqués / droits administrateur requis / erreur).
- **FR-011**: L'application NE doit PAS tenter de contourner une restriction d'accès imposée par Telegram ; elle se contente d'afficher le statut.
- **FR-012**: L'application MUST identifier chaque membre par un identifiant **stable** afin de reconnaître la même personne à travers plusieurs groupes, indépendamment de la présence d'un `@username`.
- **FR-013**: L'onglet Analyse MUST présenter la liste des membres présents dans **un seul** groupe.
- **FR-014**: L'onglet Analyse MUST présenter la liste des membres présents dans **plusieurs** groupes, avec pour chacun la liste des `@groupes` où il apparaît également.
- **FR-015**: L'application MUST dédupliquer les groupes saisis en double et rester correcte avec zéro, un ou plusieurs groupes.
- **FR-016**: Pendant toute opération réseau (connexion, récupération), l'interface MUST rester réactive (aucun gel) et indiquer la progression.
- **FR-017**: En cas d'erreur (entrée invalide, accès refusé, réseau, session expirée), l'application MUST afficher un message clair et permettre de poursuivre ou de recommencer sans plantage.
- **FR-018**: Le traitement MUST se faire en mémoire pour le périmètre MVP (aucune base de données ni persistance des membres entre deux sessions).
- **FR-019**: L'application MUST traiter uniquement les communautés de l'utilisateur à des fins de gestion/analyse personnelles, conformément aux CGU de Telegram et au RGPD (pas de réutilisation pour de la prospection non sollicitée).

### Key Entities *(include if feature involves data)*

- **Compte / Session** : le lien authentifié entre l'application et le compte Telegram de l'utilisateur ; attributs : identifiant d'accès personnel, numéro, état de connexion, jeton de session local. Stocké localement uniquement.
- **Groupe cible** : un groupe à analyser ; attributs : lien/identifiant d'origine normalisé, nom/`@handle`, statut d'accès, ensemble des membres récupérés.
- **Membre** : une personne appartenant à un ou plusieurs groupes ; attributs : identifiant stable, `@username` (optionnel), libellé d'affichage de repli.
- **Résultat d'analyse** : la correspondance « membre → ensemble des groupes où il apparaît », d'où dérivent la vue « un seul groupe » et la vue « multi-groupes ».

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un nouvel utilisateur réussit l'onboarding et la première connexion en moins de 5 minutes (hors temps de création de l'identifiant d'accès côté Telegram).
- **SC-002**: Au deuxième lancement, l'application ouvre l'écran principal sans aucune ressaisie dans 100 % des cas où la session reste valide.
- **SC-003**: Pour des groupes accessibles, 100 % des membres lisibles par le compte sont récupérés et affichés, et le statut d'accès affiché correspond à la réalité de chaque groupe.
- **SC-004**: L'analyse de recoupement classe correctement 100 % des membres entre « un seul groupe » et « plusieurs groupes », et la liste des groupes associés à chaque membre multi-groupes est exacte.
- **SC-005**: Pendant les opérations réseau, l'interface reste utilisable (jamais figée plus d'un court instant perceptible) et montre une progression.
- **SC-006**: Aucun identifiant d'accès ni jeton de session n'est présent dans le logiciel distribué ni envoyé hors du poste de l'utilisateur (vérifiable par inspection).

## Assumptions

- L'utilisateur dispose d'un compte Telegram et est en mesure de générer son propre identifiant d'accès personnel (gratuit) sur la page officielle.
- L'identité d'un membre à travers les groupes repose sur un identifiant de compte **stable** ; le `@username` est optionnel et peut être absent ou changer.
- Le périmètre MVP est **en mémoire** : la persistance (base locale), la segmentation par activité, le re-fetch planifié, les graphiques, le multi-comptes et le chiffrement du stockage local sont **hors périmètre** (post-MVP).
- La cible est le poste **Windows** de l'utilisateur, en usage mono-utilisateur local.
- Les volumes visés sont de l'ordre de quelques groupes à la fois ; aucune exigence de passage à l'échelle massive pour le MVP.
- L'application n'agit qu'en lecture sur les groupes et ne modifie rien côté Telegram.
