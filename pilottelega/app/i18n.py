"""Internationalisation légère (FR / EN / RU).

Système de traduction par dictionnaire : ``tr("clé")`` retourne la chaîne dans la langue
courante, avec repli sur le français puis sur la clé elle-même. Aucune dépendance externe.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "fr"

# Codes → nom natif (ordre d'affichage du sélecteur).
AVAILABLE_LANGUAGES: dict[str, str] = {
    "fr": "Français",
    "en": "English",
    "ru": "Русский",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "app.title": "Pilottelega",
        "common.language": "Langue",
        "common.export_excel": "Exporter en Excel",
        "common.excel_filter": "Fichiers Excel (*.xlsx)",
        # Onboarding
        "onboarding.title": "Pilottelega — Connexion",
        "onboarding.intro": (
            "Pour utiliser Pilottelega, vous avez besoin d'un identifiant d'accès Telegram "
            "personnel et <b>gratuit</b>.<br>Créez-le ici : "
            "<a href='{url}'>{url}</a> (section « API development tools »).<br>"
            "Vos identifiants restent <b>uniquement sur votre PC</b>."
        ),
        "onboarding.send_code": "Envoyer le code",
        "onboarding.phone": "Téléphone",
        "onboarding.code_placeholder": "Code reçu dans Telegram",
        "onboarding.password_placeholder": "Mot de passe 2FA (si activé)",
        "onboarding.connect": "Se connecter",
        "onboarding.api_id_error": "L'api_id doit être un nombre.",
        "onboarding.fill_fields": "Renseignez api_hash et le numéro de téléphone.",
        "onboarding.sending_code": "Envoi du code en cours…",
        "onboarding.send_failed": "Échec de l'envoi du code. Vérifiez vos identifiants.",
        "onboarding.code_sent": (
            "Code envoyé : saisissez-le ci-dessous (et le mot de passe 2FA si activé)."
        ),
        "onboarding.connecting": "Connexion en cours…",
        "onboarding.enter_code": "Saisissez le code reçu.",
        "onboarding.need_password": "Ce compte a la 2FA : saisissez votre mot de passe.",
        "onboarding.login_failed": "Connexion échouée. Vérifiez le code / mot de passe.",
        "onboarding.welcome": "Connexion réussie. Bienvenue !",
        # Fenêtre principale
        "main.links_label": "Collez les liens de groupes (un par ligne) :",
        "main.fetch": "Récupérer les membres",
        "main.fetch_descriptions": "Récupérer aussi les descriptions/bios (plus lent)",
        "main.thorough": "Récupération complète des membres (plus lent, gros groupes)",
        "main.protected_label": "Personnes à ne jamais retirer (cochez puis « Ajouter ») :",
        "main.protected_search": "Filtrer les membres…",
        "main.protected_add": "Ajouter les cochés →",
        "main.protected_remove": "Retirer la sélection",
        "main.exclude_bots": "Exclure les bots (des listes et des retraits)",
        "main.no_valid_links": "Aucun lien valide à récupérer.",
        "main.fetching": "Récupération de {id}…",
        "main.fetched_summary": "{count} groupe(s) récupéré(s).",
        "main.ignored_lines": " {count} ligne(s) ignorée(s) : {lines}",
        "main.analysis_tab": "Analyse",
        "main.removal_tab": "Retirer",
        "removal.mode": "Mode :",
        "removal.mode_mass": "Masse (garder un seul groupe)",
        "removal.mode_user": "Par utilisateur",
        "removal.keep_group": "Garder le groupe :",
        "removal.user": "Utilisateur :",
        "removal.remove_hint": "Cochez les groupes d'où retirer ce membre :",
        "removal.ban": "Bannir (empêcher de revenir)",
        "removal.preview": "Aperçu",
        "removal.select_all": "Tout sélectionner",
        "removal.execute": "Exécuter le retrait",
        "removal.col_member": "Membre",
        "removal.col_group": "Groupe d'où retirer",
        "removal.empty": "Rien à retirer (aperçu vide).",
        "removal.need_preview": "Faites d'abord un « Aperçu ».",
        "removal.confirm_title": "Confirmer le retrait",
        "removal.confirm_body": (
            "{count} retrait(s) vont être exécutés sur Telegram. "
            "Action réelle et difficilement réversible. Continuer ?"
        ),
        "removal.running": "Retrait en cours… {done}/{total}",
        "removal.done": "Terminé : {ok} réussi(s), {failed} échec(s).",
        "removal.admin_note": (
            "Nécessite les droits admin « exclure des utilisateurs » dans les groupes concernés."
        ),
        # Onglet de groupe
        "group.member_col": "Membre",
        "group.id_col": "ID",
        "group.status_summary": "{status} — {count} membre(s)",
        "group.status_summary_total": "{status} — {fetched}/{total} membres lus (partiel)",
        # Statuts d'accès
        "status.full": "Accès complet",
        "status.partial_hidden": "Membres masqués",
        "status.admin_required": "Droits administrateur requis",
        "status.error": "Erreur",
        # Onglet Analyse
        "analysis.single_title": "Présents dans un seul groupe",
        "analysis.multi_title": "Présents dans plusieurs groupes",
        "analysis.member_col": "Membre",
        "analysis.group_col": "Groupe",
        "analysis.groups_col": "Groupes",
        # Export
        "export.done": "Exporté : {path}",
        "export.failed": "Échec de l'export : {error}",
        "export.sheet_group": "Membres",
        "export.sheet_single": "Un seul groupe",
        "export.sheet_multi": "Multi-groupes",
        "export.sheet_all": "Tous les utilisateurs",
        "export.username_col": "Nom d'utilisateur",
    },
    "en": {
        "app.title": "Pilottelega",
        "common.language": "Language",
        "common.export_excel": "Export to Excel",
        "common.excel_filter": "Excel files (*.xlsx)",
        "onboarding.title": "Pilottelega — Sign in",
        "onboarding.intro": (
            "To use Pilottelega, you need a personal and <b>free</b> Telegram access ID.<br>"
            "Create it here: <a href='{url}'>{url}</a> (\"API development tools\" section).<br>"
            "Your credentials stay <b>only on your PC</b>."
        ),
        "onboarding.send_code": "Send code",
        "onboarding.phone": "Phone",
        "onboarding.code_placeholder": "Code received in Telegram",
        "onboarding.password_placeholder": "2FA password (if enabled)",
        "onboarding.connect": "Sign in",
        "onboarding.api_id_error": "api_id must be a number.",
        "onboarding.fill_fields": "Fill in api_hash and the phone number.",
        "onboarding.sending_code": "Sending code…",
        "onboarding.send_failed": "Failed to send the code. Check your credentials.",
        "onboarding.code_sent": "Code sent: enter it below (and the 2FA password if enabled).",
        "onboarding.connecting": "Signing in…",
        "onboarding.enter_code": "Enter the received code.",
        "onboarding.need_password": "This account uses 2FA: enter your password.",
        "onboarding.login_failed": "Sign-in failed. Check the code / password.",
        "onboarding.welcome": "Signed in successfully. Welcome!",
        "main.links_label": "Paste group links (one per line):",
        "main.fetch": "Fetch members",
        "main.fetch_descriptions": "Also fetch descriptions/bios (slower)",
        "main.thorough": "Thorough member fetch (slower, large groups)",
        "main.protected_label": "People to never remove (tick members, then 'Add'):",
        "main.protected_search": "Filter members…",
        "main.protected_add": "Add ticked →",
        "main.protected_remove": "Remove selected",
        "main.exclude_bots": "Exclude bots (from lists and removals)",
        "main.no_valid_links": "No valid link to fetch.",
        "main.fetching": "Fetching {id}…",
        "main.fetched_summary": "{count} group(s) fetched.",
        "main.ignored_lines": " {count} line(s) ignored: {lines}",
        "main.analysis_tab": "Analysis",
        "main.removal_tab": "Remove",
        "removal.mode": "Mode:",
        "removal.mode_mass": "Bulk (keep a single group)",
        "removal.mode_user": "Per user",
        "removal.keep_group": "Keep group:",
        "removal.user": "User:",
        "removal.remove_hint": "Tick the groups to remove this member from:",
        "removal.ban": "Ban (prevent rejoining)",
        "removal.preview": "Preview",
        "removal.select_all": "Select all",
        "removal.execute": "Execute removal",
        "removal.col_member": "Member",
        "removal.col_group": "Remove from group",
        "removal.empty": "Nothing to remove (empty preview).",
        "removal.need_preview": "Run a 'Preview' first.",
        "removal.confirm_title": "Confirm removal",
        "removal.confirm_body": (
            "{count} removal(s) will be executed on Telegram. "
            "Real, hard-to-undo action. Continue?"
        ),
        "removal.running": "Removing… {done}/{total}",
        "removal.done": "Done: {ok} succeeded, {failed} failed.",
        "removal.admin_note": ("Requires admin 'ban users' rights in the affected groups."),
        "group.member_col": "Member",
        "group.id_col": "ID",
        "group.status_summary": "{status} — {count} member(s)",
        "group.status_summary_total": "{status} — {fetched} / {total} members read (partial list)",
        "status.full": "Full access",
        "status.partial_hidden": "Hidden members",
        "status.admin_required": "Administrator rights required",
        "status.error": "Error",
        "analysis.single_title": "In a single group",
        "analysis.multi_title": "In several groups",
        "analysis.member_col": "Member",
        "analysis.group_col": "Group",
        "analysis.groups_col": "Groups",
        "export.done": "Exported: {path}",
        "export.failed": "Export failed: {error}",
        "export.sheet_group": "Members",
        "export.sheet_single": "Single group",
        "export.sheet_multi": "Multi-group",
        "export.sheet_all": "All users",
        "export.username_col": "Username",
    },
    "ru": {
        "app.title": "Pilottelega",
        "common.language": "Язык",
        "common.export_excel": "Экспорт в Excel",
        "common.excel_filter": "Файлы Excel (*.xlsx)",
        "onboarding.title": "Pilottelega — Вход",
        "onboarding.intro": (
            "Для работы с Pilottelega нужен личный и <b>бесплатный</b> идентификатор доступа "
            "Telegram.<br>Создайте его здесь: <a href='{url}'>{url}</a> "
            "(раздел «API development tools»).<br>"
            "Ваши данные остаются <b>только на вашем компьютере</b>."
        ),
        "onboarding.send_code": "Отправить код",
        "onboarding.phone": "Телефон",
        "onboarding.code_placeholder": "Код из Telegram",
        "onboarding.password_placeholder": "Пароль 2FA (если включён)",
        "onboarding.connect": "Войти",
        "onboarding.api_id_error": "api_id должен быть числом.",
        "onboarding.fill_fields": "Укажите api_hash и номер телефона.",
        "onboarding.sending_code": "Отправка кода…",
        "onboarding.send_failed": "Не удалось отправить код. Проверьте данные.",
        "onboarding.code_sent": "Код отправлен: введите его ниже (и пароль 2FA, если включён).",
        "onboarding.connecting": "Выполняется вход…",
        "onboarding.enter_code": "Введите полученный код.",
        "onboarding.need_password": "На аккаунте включена 2FA: введите пароль.",
        "onboarding.login_failed": "Ошибка входа. Проверьте код / пароль.",
        "onboarding.welcome": "Вход выполнен. Добро пожаловать!",
        "main.links_label": "Вставьте ссылки на группы (по одной в строке):",
        "main.fetch": "Получить участников",
        "main.fetch_descriptions": "Также получать описания/био (медленнее)",
        "main.thorough": "Полная загрузка участников (медленнее, большие группы)",
        "main.protected_label": "Люди, которых не удалять (отметьте, затем «Добавить»):",
        "main.protected_search": "Фильтр участников…",
        "main.protected_add": "Добавить отмеченных →",
        "main.protected_remove": "Удалить выбранное",
        "main.exclude_bots": "Исключить ботов (из списков и удаления)",
        "main.no_valid_links": "Нет действительных ссылок.",
        "main.fetching": "Получение {id}…",
        "main.fetched_summary": "Получено групп: {count}.",
        "main.ignored_lines": " Пропущено строк: {count}: {lines}",
        "main.analysis_tab": "Анализ",
        "main.removal_tab": "Удалить",
        "removal.mode": "Режим:",
        "removal.mode_mass": "Массово (оставить одну группу)",
        "removal.mode_user": "По пользователю",
        "removal.keep_group": "Оставить группу:",
        "removal.user": "Пользователь:",
        "removal.remove_hint": "Отметьте группы, из которых удалить участника:",
        "removal.ban": "Забанить (запретить возврат)",
        "removal.preview": "Предпросмотр",
        "removal.select_all": "Выбрать все",
        "removal.execute": "Выполнить удаление",
        "removal.col_member": "Участник",
        "removal.col_group": "Удалить из группы",
        "removal.empty": "Нечего удалять (пустой предпросмотр).",
        "removal.need_preview": "Сначала нажмите «Предпросмотр».",
        "removal.confirm_title": "Подтвердите удаление",
        "removal.confirm_body": (
            "Будет выполнено удалений: {count}. "
            "Реальное и трудно обратимое действие. Продолжить?"
        ),
        "removal.running": "Удаление… {done}/{total}",
        "removal.done": "Готово: успешно {ok}, ошибок {failed}.",
        "removal.admin_note": (
            "Требуются права администратора «блокировать пользователей» в группах."
        ),
        "group.member_col": "Участник",
        "group.id_col": "ID",
        "group.status_summary": "{status} — участников: {count}",
        "group.status_summary_total": "{status} — прочитано {fetched} / {total} (неполный список)",
        "status.full": "Полный доступ",
        "status.partial_hidden": "Скрытые участники",
        "status.admin_required": "Требуются права администратора",
        "status.error": "Ошибка",
        "analysis.single_title": "Только в одной группе",
        "analysis.multi_title": "В нескольких группах",
        "analysis.member_col": "Участник",
        "analysis.group_col": "Группа",
        "analysis.groups_col": "Группы",
        "export.done": "Экспортировано: {path}",
        "export.failed": "Ошибка экспорта: {error}",
        "export.sheet_group": "Участники",
        "export.sheet_single": "Одна группа",
        "export.sheet_multi": "Несколько групп",
        "export.sheet_all": "Все пользователи",
        "export.username_col": "Имя пользователя",
    },
}

_current_language = DEFAULT_LANGUAGE


def set_language(lang: str) -> None:
    """Définit la langue courante si elle est connue, sinon ne change rien."""
    global _current_language
    if lang in _TRANSLATIONS:
        _current_language = lang


def get_language() -> str:
    """Retourne le code de la langue courante."""
    return _current_language


def tr(key: str, **kwargs: object) -> str:
    """Traduit ``key`` dans la langue courante (repli FR puis clé brute).

    Les ``kwargs`` éventuels sont injectés via ``str.format`` (ex. ``tr("main.fetching", id=x)``).
    """
    table = _TRANSLATIONS.get(_current_language, {})
    text = table.get(key)
    if text is None:
        text = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
