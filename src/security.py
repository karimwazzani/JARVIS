import os


def _parse_chat_ids(raw: str) -> set[str]:
    return {part.strip() for part in raw.split(",") if part.strip()}


def get_authorized_chat_ids() -> set[str]:
    return _parse_chat_ids(os.getenv("AUTHORIZED_CHAT_IDS", ""))


def is_chat_authorized(chat_id: object) -> bool:
    authorized_ids = get_authorized_chat_ids()
    if not authorized_ids:
        return True
    return str(chat_id) in authorized_ids
