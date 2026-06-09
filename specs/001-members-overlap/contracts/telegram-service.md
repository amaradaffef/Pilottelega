# Contract: TelegramService (core/telegram_service.py)

Façade **async** au-dessus de Telethon. Aucune dépendance Qt. Consommée par l'UI via qasync.
C'est la frontière entre l'application et le réseau Telegram.

## Responsabilités

- Gérer le cycle de connexion (login code + 2FA) et la persistance de session locale.
- Récupérer les membres d'un groupe et en déduire le `AccessStatus`.
- Ne jamais contourner une restriction d'accès (Principe II) — uniquement rapporter le statut.

## Interface (signatures logiques)

```text
class TelegramService:
    def __init__(self, api_id: int, api_hash: str, session_path: str) -> None

    async def is_authorized() -> bool
        # True si une session locale valide existe (FR-005)

    async def start_login(phone: str) -> None
        # Envoie le code de connexion. Transition ONBOARDING → CODE_SENT.

    async def submit_code(code: str) -> LoginStep
        # LoginStep ∈ {CONNECTED, PASSWORD_REQUIRED}. Erreur → exception → ERROR (FR-017).

    async def submit_password(password: str) -> None
        # Valide le mot de passe 2FA. Transition → CONNECTED. Sauve la session localement (FR-003).

    async def fetch_group(identifier: str) -> TargetGroup
        # Résout le groupe et itère ses membres.
        # Renseigne access_status (FULL / PARTIAL_HIDDEN / ADMIN_REQUIRED / ERROR) + members.
        # N'élève pas d'exception en cas d'accès refusé : encode le statut (FR-008/010/011).

    async def logout() -> None
        # Optionnel post-MVP ; supprime la session locale.
```

## Mapping erreurs → AccessStatus (research D6)

| Condition Telethon | AccessStatus |
|---|---|
| Itération complète réussie | `FULL` |
| `ChatAdminRequiredError` | `ADMIN_REQUIRED` |
| Groupe à membres masqués / liste tronquée | `PARTIAL_HIDDEN` |
| `FloodWaitError`, réseau, résolution échouée, autre | `ERROR` (+ `error_message`) |

## Garanties

- **Réactivité** : toutes les méthodes sont `async` ; l'appelant (UI) les `await` via qasync
  sans bloquer le thread graphique (Principe III).
- **Isolation des échecs** : `fetch_group` d'un groupe n'affecte pas les autres (FR-007).
- **Confidentialité** : `api_hash` et le fichier session restent locaux (FR-004, SC-006).

## Tests (integration, avec mocks Telethon)

- `is_authorized` reflète l'existence/validité de la session.
- `submit_code` route correctement vers PASSWORD_REQUIRED quand la 2FA est active.
- `fetch_group` produit chaque `AccessStatus` selon l'exception simulée.
