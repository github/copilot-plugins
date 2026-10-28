"""Secure, local-only access to Messages.app data.

Portions of the security design are derived from the Anthropic iMessage plugin
at commit c54b5608d9be1910de9a5b91c2d15bf6673b9c35. This implementation was
rewritten for GitHub Copilot CLI and the Python standard library.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

APPLE_EPOCH_SECONDS = 978_307_200
MAX_MESSAGE_LENGTH = 100_000
TEXT_CHUNK_LIMIT = 10_000
SAFE_SERVICES = frozenset({"IMESSAGE"})
OPTIONAL_SERVICES = frozenset({"SMS", "RCS"})

SEND_SCRIPT = """\
on run argv
    set messageText to item 1 of argv
    set chatID to item 2 of argv
    tell application "Messages"
        send messageText to chat id chatID
    end tell
end run
"""


class IMessageError(RuntimeError):
    """Base error for expected iMessage failures."""


class UnsupportedPlatformError(IMessageError):
    """Raised when the server is used outside macOS."""


class ChatDatabaseError(IMessageError):
    """Raised when chat.db cannot be opened or queried."""


class AccessDeniedError(IMessageError):
    """Raised when a chat is not authorized by local policy."""


class SendError(IMessageError):
    """Raised when Messages.app rejects an outbound send."""


def normalize_handle(value: str) -> str:
    value = value.strip().lower()
    if not value:
        raise ValueError("A handle cannot be empty.")
    if "@" in value:
        return value
    digits = re.sub(r"[^\d+]", "", value)
    if digits.startswith("00"):
        digits = f"+{digits[2:]}"
    if digits.startswith("+"):
        digits = f"+{re.sub(r'[^0-9]', '', digits[1:])}"
    else:
        digits = re.sub(r"[^0-9]", "", digits)
    return digits or value


def normalize_service(value: str | None) -> str:
    return (value or "").strip().upper()


def account_to_handle(account: str) -> str | None:
    value = account.strip()
    if len(value) > 2 and value[1] == ":":
        value = value[2:]
    if not value or ("@" not in value and not re.search(r"\d", value)):
        return None
    return normalize_handle(value)


def is_address_handle(value: str) -> bool:
    if "@" in value:
        local, separator, domain = value.partition("@")
        return bool(local and separator and domain and " " not in value)
    return re.fullmatch(r"\+?\d{7,15}", value) is not None


def apple_timestamp(value: int | float | None) -> str | None:
    if value is None:
        return None
    numeric = float(value)
    if abs(numeric) > 100_000_000_000:
        numeric /= 1_000_000_000
    return datetime.fromtimestamp(
        numeric + APPLE_EPOCH_SECONDS, tz=timezone.utc
    ).isoformat()


def parse_attributed_body(body: bytes | None) -> str | None:
    if not body:
        return None

    marker_index = body.find(b"NSString")
    if marker_index < 0:
        return None

    payload_marker = body.find(b"+", marker_index + len(b"NSString"))
    if payload_marker < 0 or payload_marker + 1 >= len(body):
        return None

    index = payload_marker + 1
    prefix = body[index]
    index += 1
    if prefix in (0x81, 0x82, 0x83):
        width = prefix - 0x80
        if index + width > len(body):
            return None
        length = int.from_bytes(body[index : index + width], "little")
        index += width
    else:
        length = prefix
    if length <= 0 or index + length > len(body):
        return None
    try:
        return body[index : index + length].decode("utf-8")
    except UnicodeDecodeError:
        return None


@dataclass(frozen=True)
class GroupAccess:
    participants: tuple[str, ...]
    label: str = ""

    @classmethod
    def from_dict(cls, value: Any) -> "GroupAccess":
        if not isinstance(value, dict):
            raise ValueError("Each allowed group must be an object.")
        participants = value.get("participants")
        if not isinstance(participants, list) or not all(
            isinstance(item, str) for item in participants
        ):
            raise ValueError("An allowed group must contain a participant list.")
        label = value.get("label", "")
        if not isinstance(label, str):
            raise ValueError("An allowed group label must be a string.")
        return cls(
            participants=tuple(sorted({normalize_handle(item) for item in participants})),
            label=label,
        )


@dataclass(frozen=True)
class AccessPolicy:
    owner_handles: frozenset[str]
    allowed_handles: frozenset[str]
    allowed_groups: dict[str, GroupAccess]
    allow_sms_rcs: bool = False

    @classmethod
    def default(cls) -> "AccessPolicy":
        return cls(frozenset(), frozenset(), {}, False)

    @classmethod
    def from_dict(cls, value: Any) -> "AccessPolicy":
        if not isinstance(value, dict):
            raise ValueError("The access configuration must be a JSON object.")
        if value.get("version", 1) != 1:
            raise ValueError("Unsupported access configuration version.")

        owners = value.get("ownerHandles", [])
        allowed = value.get("allowedHandles", [])
        groups = value.get("allowedGroups", {})
        allow_sms_rcs = value.get("allowSmsRcs", False)
        if not isinstance(owners, list) or not all(isinstance(item, str) for item in owners):
            raise ValueError("ownerHandles must be an array of strings.")
        if not isinstance(allowed, list) or not all(
            isinstance(item, str) for item in allowed
        ):
            raise ValueError("allowedHandles must be an array of strings.")
        if not isinstance(groups, dict) or not all(
            isinstance(key, str) for key in groups
        ):
            raise ValueError("allowedGroups must be an object keyed by chat GUID.")
        if not isinstance(allow_sms_rcs, bool):
            raise ValueError("allowSmsRcs must be a boolean.")

        return cls(
            owner_handles=frozenset(normalize_handle(item) for item in owners),
            allowed_handles=frozenset(normalize_handle(item) for item in allowed),
            allowed_groups={
                key: GroupAccess.from_dict(group) for key, group in groups.items()
            },
            allow_sms_rcs=allow_sms_rcs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "ownerHandles": sorted(self.owner_handles),
            "allowedHandles": sorted(self.allowed_handles),
            "allowedGroups": {
                guid: {
                    "participants": list(group.participants),
                    "label": group.label,
                }
                for guid, group in sorted(self.allowed_groups.items())
            },
            "allowSmsRcs": self.allow_sms_rcs,
        }


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self.default_path()

    @staticmethod
    def default_path() -> Path:
        explicit = os.environ.get("COPILOT_IMESSAGE_STATE_DIR")
        if explicit:
            root = Path(explicit).expanduser()
        else:
            root = (
                Path.home()
                / "Library"
                / "Application Support"
                / "GitHub Copilot"
                / "iMessage"
            )
        return root / "access.json"

    def load(self) -> AccessPolicy:
        if not self.path.exists():
            return AccessPolicy.default()
        try:
            return AccessPolicy.from_dict(json.loads(self.path.read_text("utf-8")))
        except (OSError, json.JSONDecodeError, ValueError) as error:
            raise IMessageError(
                f"Invalid iMessage access configuration at {self.path}: {error}"
            ) from error

    def save(self, policy: AccessPolicy) -> None:
        directory = self.path.parent
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        payload = f"{json.dumps(policy.to_dict(), indent=2)}\n"
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{self.path.name}.", dir=directory
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise


@dataclass(frozen=True)
class Chat:
    row_id: int
    guid: str
    identifier: str
    display_name: str
    style: int | None
    service_name: str
    participants: tuple[str, ...]
    participant_services: tuple[str, ...]
    last_message_at: str | None

    @property
    def is_group(self) -> bool:
        return self.style == 43 or len(self.participants) > 1

    def public_dict(self) -> dict[str, Any]:
        return {
            "chat_id": self.guid,
            "name": self.display_name or self.identifier,
            "kind": "group" if self.is_group else "direct",
            "service": self.service_name,
            "participants": list(self.participants),
            "last_message_at": self.last_message_at,
        }


@dataclass(frozen=True)
class Message:
    row_id: int
    guid: str
    chat_guid: str
    sender: str
    is_from_me: bool
    text: str | None
    sent_at: str | None
    service: str
    has_attachments: bool

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChatDatabase:
    def __init__(
        self,
        path: Path | None = None,
        *,
        enforce_macos: bool = True,
    ) -> None:
        configured = os.environ.get("COPILOT_IMESSAGE_DB")
        self.path = path or (
            Path(configured).expanduser()
            if configured
            else Path.home() / "Library" / "Messages" / "chat.db"
        )
        self.enforce_macos = enforce_macos

    def connect(self) -> sqlite3.Connection:
        if self.enforce_macos and platform.system() != "Darwin":
            raise UnsupportedPlatformError(
                "The iMessage plugin is available only on macOS."
            )
        try:
            uri = f"file:{quote(str(self.path.resolve()), safe='/')}?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only = ON")
            return connection
        except sqlite3.Error as error:
            raise ChatDatabaseError(
                f"Cannot read {self.path}. Grant Full Disk Access to the terminal "
                "or application running Copilot CLI in System Settings > Privacy & "
                "Security > Full Disk Access, then restart it."
            ) from error

    def self_handles(self) -> frozenset[str]:
        try:
            with closing(self.connect()) as connection:
                account_rows = connection.execute(
                    """
                    SELECT DISTINCT account
                    FROM message
                    WHERE is_from_me = 1
                      AND service = 'iMessage'
                      AND account IS NOT NULL
                    """
                ).fetchall()
                accounts = frozenset(
                    handle
                    for row in account_rows
                    if (handle := account_to_handle(row["account"])) is not None
                )

                message_columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(message)")
                }
                if "destination_caller_id" not in message_columns:
                    return accounts

                # This field is the local iMessage route, not the remote sender.
                # Require it on both directions under a trusted account so a
                # one-sided or spoofable transport value cannot become "self".
                destination_rows = connection.execute(
                    """
                    WITH trusted_accounts AS (
                        SELECT DISTINCT account
                        FROM message
                        WHERE is_from_me = 1
                          AND service = 'iMessage'
                          AND account IS NOT NULL
                    )
                    SELECT
                        m.destination_caller_id,
                        MAX(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END)
                            AS has_outgoing,
                        MAX(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END)
                            AS has_incoming
                    FROM message AS m
                    JOIN trusted_accounts AS trusted ON trusted.account = m.account
                    WHERE m.service = 'iMessage'
                      AND m.destination_caller_id IS NOT NULL
                      AND m.destination_caller_id != ''
                    GROUP BY m.destination_caller_id
                    HAVING has_outgoing = 1 AND has_incoming = 1
                    """
                ).fetchall()
                confirmed_destinations = {
                    handle
                    for row in destination_rows
                    if (
                        handle := account_to_handle(row["destination_caller_id"])
                    )
                    is not None
                    and is_address_handle(handle)
                }
                return accounts | frozenset(confirmed_destinations)
        except sqlite3.Error as error:
            raise ChatDatabaseError(f"Unable to identify local iMessage accounts: {error}") from error

    def list_chats(self, scan_limit: int | None = 1000) -> list[Chat]:
        limit_clause = "LIMIT ?" if scan_limit is not None else ""
        parameters: tuple[int, ...] = (scan_limit,) if scan_limit is not None else ()
        try:
            with closing(self.connect()) as connection:
                rows = connection.execute(
                    f"""
                    SELECT
                        c.ROWID AS row_id,
                        c.guid,
                        COALESCE(c.chat_identifier, '') AS identifier,
                        COALESCE(c.display_name, '') AS display_name,
                        c.style,
                        COALESCE(c.service_name, '') AS service_name,
                        MAX(m.date) AS last_date
                    FROM chat AS c
                    LEFT JOIN chat_message_join AS cmj ON cmj.chat_id = c.ROWID
                    LEFT JOIN message AS m ON m.ROWID = cmj.message_id
                    GROUP BY c.ROWID
                    ORDER BY last_date DESC
                    {limit_clause}
                    """,
                    parameters,
                ).fetchall()
                return [self._chat(connection, row) for row in rows]
        except sqlite3.Error as error:
            raise ChatDatabaseError(f"Unable to list iMessage chats: {error}") from error

    def get_chat(self, guid: str) -> Chat | None:
        try:
            with closing(self.connect()) as connection:
                row = connection.execute(
                    """
                    SELECT
                        c.ROWID AS row_id,
                        c.guid,
                        COALESCE(c.chat_identifier, '') AS identifier,
                        COALESCE(c.display_name, '') AS display_name,
                        c.style,
                        COALESCE(c.service_name, '') AS service_name,
                        MAX(m.date) AS last_date
                    FROM chat AS c
                    LEFT JOIN chat_message_join AS cmj ON cmj.chat_id = c.ROWID
                    LEFT JOIN message AS m ON m.ROWID = cmj.message_id
                    WHERE c.guid = ?
                    GROUP BY c.ROWID
                    """,
                    (guid,),
                ).fetchone()
                return self._chat(connection, row) if row else None
        except sqlite3.Error as error:
            raise ChatDatabaseError(f"Unable to inspect iMessage chat {guid}: {error}") from error

    def messages(self, chat: Chat, limit: int) -> list[Message]:
        try:
            with closing(self.connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT
                        m.ROWID AS row_id,
                        COALESCE(m.guid, '') AS guid,
                        m.text,
                        m.attributedBody,
                        m.date,
                        m.is_from_me,
                        COALESCE(h.id, '') AS sender,
                        COALESCE(m.service, h.service, c.service_name, '') AS service,
                        COALESCE(m.cache_has_attachments, 0) AS has_attachments
                    FROM message AS m
                    JOIN chat_message_join AS cmj ON cmj.message_id = m.ROWID
                    JOIN chat AS c ON c.ROWID = cmj.chat_id
                    LEFT JOIN handle AS h ON h.ROWID = m.handle_id
                    WHERE cmj.chat_id = ?
                    ORDER BY m.date DESC
                    LIMIT ?
                    """,
                    (chat.row_id, limit),
                ).fetchall()
        except sqlite3.Error as error:
            raise ChatDatabaseError(
                f"Unable to read messages for chat {chat.guid}: {error}"
            ) from error

        messages = [
            Message(
                row_id=row["row_id"],
                guid=row["guid"],
                chat_guid=chat.guid,
                sender=(
                    "me"
                    if row["is_from_me"]
                    else normalize_handle(row["sender"])
                    if row["sender"]
                    else "unknown"
                ),
                is_from_me=bool(row["is_from_me"]),
                text=row["text"] or parse_attributed_body(row["attributedBody"]),
                sent_at=apple_timestamp(row["date"]),
                service=row["service"],
                has_attachments=bool(row["has_attachments"]),
            )
            for row in rows
        ]
        messages.reverse()
        return messages

    def search(
        self,
        query: str,
        chat_row_ids: Iterable[int],
        candidate_limit: int,
    ) -> list[tuple[Chat, Message]]:
        authorized_ids = tuple(dict.fromkeys(chat_row_ids))
        if not authorized_ids:
            return []
        placeholders = ",".join("?" for _ in authorized_ids)
        try:
            with closing(self.connect()) as connection:
                rows = connection.execute(
                    f"""
                    SELECT
                        m.ROWID AS row_id,
                        COALESCE(m.guid, '') AS guid,
                        m.text,
                        m.attributedBody,
                        m.date,
                        m.is_from_me,
                        COALESCE(h.id, '') AS sender,
                        COALESCE(m.service, h.service, c.service_name, '') AS service,
                        COALESCE(m.cache_has_attachments, 0) AS has_attachments,
                        c.ROWID AS chat_row_id,
                        c.guid AS chat_guid,
                        COALESCE(c.chat_identifier, '') AS identifier,
                        COALESCE(c.display_name, '') AS display_name,
                        c.style,
                        COALESCE(c.service_name, '') AS service_name
                    FROM message AS m
                    JOIN chat_message_join AS cmj ON cmj.message_id = m.ROWID
                    JOIN chat AS c ON c.ROWID = cmj.chat_id
                    LEFT JOIN handle AS h ON h.ROWID = m.handle_id
                    WHERE cmj.chat_id IN ({placeholders})
                      AND instr(lower(COALESCE(m.text, '')), lower(?)) > 0
                    ORDER BY m.date DESC
                    LIMIT ?
                    """,
                    (*authorized_ids, query, candidate_limit),
                ).fetchall()

                results: list[tuple[Chat, Message]] = []
                chat_cache: dict[int, Chat] = {}
                for row in rows:
                    chat_row_id = row["chat_row_id"]
                    chat = chat_cache.get(chat_row_id)
                    if chat is None:
                        chat = self._chat(
                            connection,
                            {
                                "row_id": chat_row_id,
                                "guid": row["chat_guid"],
                                "identifier": row["identifier"],
                                "display_name": row["display_name"],
                                "style": row["style"],
                                "service_name": row["service_name"],
                                "last_date": row["date"],
                            },
                        )
                        chat_cache[chat_row_id] = chat
                    results.append(
                        (
                            chat,
                            Message(
                                row_id=row["row_id"],
                                guid=row["guid"],
                                chat_guid=chat.guid,
                                sender=(
                                    "me"
                                    if row["is_from_me"]
                                    else normalize_handle(row["sender"])
                                    if row["sender"]
                                    else "unknown"
                                ),
                                is_from_me=bool(row["is_from_me"]),
                                text=row["text"]
                                or parse_attributed_body(row["attributedBody"]),
                                sent_at=apple_timestamp(row["date"]),
                                service=row["service"],
                                has_attachments=bool(row["has_attachments"]),
                            ),
                        )
                    )
                return results
        except sqlite3.Error as error:
            raise ChatDatabaseError(f"Unable to search iMessage history: {error}") from error

    @staticmethod
    def _chat(connection: sqlite3.Connection, row: Any) -> Chat:
        participants = connection.execute(
            """
            SELECT h.id, COALESCE(h.service, '')
            FROM chat_handle_join AS chj
            JOIN handle AS h ON h.ROWID = chj.handle_id
            WHERE chj.chat_id = ?
            ORDER BY h.id
            """,
            (row["row_id"],),
        ).fetchall()
        return Chat(
            row_id=row["row_id"],
            guid=row["guid"],
            identifier=row["identifier"],
            display_name=row["display_name"],
            style=row["style"],
            service_name=row["service_name"],
            participants=tuple(normalize_handle(item["id"]) for item in participants),
            participant_services=tuple(item[1] for item in participants),
            last_message_at=apple_timestamp(row["last_date"]),
        )


class IMessageService:
    def __init__(
        self,
        database: ChatDatabase | None = None,
        config: ConfigStore | None = None,
    ) -> None:
        self.database = database or ChatDatabase()
        self.config = config or ConfigStore()

    def effective_policy(self) -> AccessPolicy:
        configured = self.config.load()
        detected = self.database.self_handles()
        return AccessPolicy(
            owner_handles=configured.owner_handles | detected,
            allowed_handles=configured.allowed_handles,
            allowed_groups=configured.allowed_groups,
            allow_sms_rcs=configured.allow_sms_rcs,
        )

    @staticmethod
    def service_allowed(chat: Chat, policy: AccessPolicy) -> bool:
        services = {
            normalize_service(service)
            for service in (*chat.participant_services, chat.service_name)
            if normalize_service(service)
        }
        if not services:
            return False
        if services <= SAFE_SERVICES:
            return True
        return policy.allow_sms_rcs and services <= SAFE_SERVICES | OPTIONAL_SERVICES

    @classmethod
    def is_self_chat(cls, chat: Chat, policy: AccessPolicy) -> bool:
        participants = frozenset(chat.participants)
        return (
            bool(participants)
            and participants <= policy.owner_handles
            and cls.service_allowed(chat, policy)
        )

    @classmethod
    def chat_allowed(cls, chat: Chat, policy: AccessPolicy) -> bool:
        if not cls.service_allowed(chat, policy):
            return False
        participants = frozenset(chat.participants)
        if cls.is_self_chat(chat, policy):
            return True
        if chat.is_group:
            group = policy.allowed_groups.get(chat.guid)
            return group is not None and frozenset(group.participants) == participants
        return len(participants) == 1 and participants <= policy.allowed_handles

    def access_summary(self) -> dict[str, int]:
        policy = self.effective_policy()
        chats = self.database.list_chats(scan_limit=None)
        return {
            "authorized_chat_count": sum(
                self.chat_allowed(chat, policy) for chat in chats
            ),
            "self_chat_count": sum(self.is_self_chat(chat, policy) for chat in chats),
        }

    def authorized_chat(self, guid: str) -> Chat:
        chat = self.database.get_chat(guid)
        if chat is None:
            raise AccessDeniedError(f"Unknown iMessage chat: {guid}")
        if not self.chat_allowed(chat, self.effective_policy()):
            raise AccessDeniedError(
                "Access denied. The chat is not a self-chat or explicit allowlist "
                "entry, its group membership changed, or its service is blocked."
            )
        return chat

    def list_chats(self, limit: int) -> list[dict[str, Any]]:
        policy = self.effective_policy()
        return [
            chat.public_dict()
            for chat in self.database.list_chats(scan_limit=None)
            if self.chat_allowed(chat, policy)
        ][:limit]

    def messages(self, guid: str, limit: int) -> list[dict[str, Any]]:
        chat = self.authorized_chat(guid)
        return [message.public_dict() for message in self.database.messages(chat, limit)]

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        policy = self.effective_policy()
        authorized_chats = [
            chat
            for chat in self.database.list_chats(scan_limit=None)
            if self.chat_allowed(chat, policy)
        ]
        results: list[dict[str, Any]] = []
        for chat, message in self.database.search(
            query,
            (chat.row_id for chat in authorized_chats),
            limit,
        ):
            if self.chat_allowed(chat, policy):
                results.append(
                    {"chat": chat.public_dict(), "message": message.public_dict()}
                )
                if len(results) >= limit:
                    break
        return results

    def send(self, guid: str, text: str) -> dict[str, Any]:
        if platform.system() != "Darwin":
            raise UnsupportedPlatformError(
                "Sending iMessages is available only on macOS."
            )
        if not text or not text.strip():
            raise ValueError("Message text cannot be empty.")
        if len(text) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message text exceeds the {MAX_MESSAGE_LENGTH}-character limit."
            )
        chat = self.authorized_chat(guid)
        chunks = list(_chunk_text(text, TEXT_CHUNK_LIMIT))
        for chunk_index, chunk in enumerate(chunks):
            try:
                result = subprocess.run(
                    ["osascript", "-", chunk, chat.guid],
                    input=SEND_SCRIPT,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise SendError(f"Could not invoke Messages.app: {error}") from error
            if result.returncode != 0:
                detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
                raise SendError(
                    f"Messages.app rejected chunk {chunk_index + 1} after "
                    f"{chunk_index} of {len(chunks)} chunks were sent. "
                    "Do not retry without confirming what the recipient received. "
                    "In System Settings > Privacy & "
                    "Security > Automation, allow the terminal or application running "
                    f"Copilot CLI to control Messages. AppleScript reported: {detail}"
                )
        return {"chat_id": chat.guid, "chunks_sent": len(chunks), "characters": len(text)}


def _chunk_text(text: str, limit: int) -> Iterable[str]:
    remaining = text
    while len(remaining) > limit:
        split = max(
            remaining.rfind("\n", 0, limit + 1),
            remaining.rfind(" ", 0, limit + 1),
        )
        if split <= 0:
            split = limit
        yield remaining[:split]
        remaining = remaining[split:]
        if remaining.startswith("\n") or remaining.startswith(" "):
            remaining = remaining[1:]
    if remaining:
        yield remaining
