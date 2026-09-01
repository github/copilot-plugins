from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "server"))

from imessage import (  # noqa: E402
    AccessDeniedError,
    AccessPolicy,
    ChatDatabase,
    ConfigStore,
    GroupAccess,
    IMessageService,
    SendError,
    is_address_handle,
    parse_attributed_body,
)
from imessage_mcp import MCPServer  # noqa: E402


def create_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE handle (
            ROWID INTEGER PRIMARY KEY,
            id TEXT,
            service TEXT
        );
        CREATE TABLE chat (
            ROWID INTEGER PRIMARY KEY,
            guid TEXT,
            chat_identifier TEXT,
            display_name TEXT,
            style INTEGER,
            service_name TEXT
        );
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY,
            guid TEXT,
            text TEXT,
            attributedBody BLOB,
            date INTEGER,
            is_from_me INTEGER,
            account TEXT,
            handle_id INTEGER,
            service TEXT,
            cache_has_attachments INTEGER DEFAULT 0,
            destination_caller_id TEXT
        );
        CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER);
        CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);

        INSERT INTO handle VALUES
            (1, 'me@example.com', 'iMessage'),
            (2, '+1 (555) 111-2222', 'iMessage'),
            (3, 'friend@example.com', 'iMessage'),
            (4, 'me@example.com', 'SMS');

        INSERT INTO chat VALUES
            (1, 'iMessage;-;me@example.com', 'me@example.com', '', 45, 'iMessage'),
            (2, 'iMessage;-;+15551112222', '+15551112222', '', 45, 'iMessage'),
            (3, 'iMessage;+;group1', 'group1', 'Friends', 43, 'iMessage'),
            (4, 'SMS;-;me@example.com', 'me@example.com', '', 45, 'SMS');

        INSERT INTO chat_handle_join VALUES
            (1, 1),
            (2, 2),
            (3, 2),
            (3, 3),
            (4, 4);

        INSERT INTO message VALUES
            (1, 'm1', 'self note', NULL, 1000000000, 1, 'E:me@example.com', 1, 'iMessage', 0, NULL),
            (2, 'm2', 'hello from friend', NULL, 2000000000, 0, NULL, 2, 'iMessage', 0, NULL),
            (3, 'm3', NULL, X'4E5341747472696275746564537472696E674E53537472696E67019484012B0568656C6C6F', 3000000000, 0, NULL, 3, 'iMessage', 0, NULL),
            (4, 'm4', 'spoofed self', NULL, 4000000000, 0, NULL, 4, 'SMS', 0, NULL);

        INSERT INTO chat_message_join VALUES (1, 1), (2, 2), (3, 3), (4, 4);
        """
    )
    connection.commit()
    connection.close()


class IMessageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database_path = self.root / "chat.db"
        self.config_path = self.root / "state" / "access.json"
        create_database(self.database_path)
        self.database = ChatDatabase(self.database_path, enforce_macos=False)
        self.config = ConfigStore(self.config_path)
        self.service = IMessageService(self.database, self.config)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def save(self, policy: AccessPolicy) -> None:
        self.config.save(policy)

    def test_default_policy_allows_only_imessage_self_chat(self) -> None:
        chats = self.service.list_chats(20)
        self.assertEqual(["iMessage;-;me@example.com"], [chat["chat_id"] for chat in chats])
        self.assertEqual(
            {"authorized_chat_count": 1, "self_chat_count": 1},
            self.service.access_summary(),
        )
        with self.assertRaises(AccessDeniedError):
            self.service.authorized_chat("SMS;-;me@example.com")

    def test_configured_self_alias_reloads_without_server_restart(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO handle VALUES (5, 'alias@example.com', 'iMessage')"
            )
            connection.execute(
                """
                INSERT INTO chat VALUES
                    (5, 'iMessage;-;alias@example.com', 'alias@example.com', '',
                     45, 'iMessage')
                """
            )
            connection.execute("INSERT INTO chat_handle_join VALUES (5, 5)")

        self.assertNotIn(
            "iMessage;-;alias@example.com",
            {chat["chat_id"] for chat in self.service.list_chats(20)},
        )
        self.save(
            AccessPolicy(
                owner_handles=frozenset({"alias@example.com"}),
                allowed_handles=frozenset(),
                allowed_groups={},
            )
        )
        self.assertIn(
            "iMessage;-;alias@example.com",
            {chat["chat_id"] for chat in self.service.list_chats(20)},
        )

    def test_confirmed_imessage_destination_alias_identifies_self_chat(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO handle VALUES (5, '+15550009999', 'iMessage')"
            )
            connection.execute(
                """
                INSERT INTO chat VALUES
                    (5, 'iMessage;-;+15550009999', '+15550009999', '',
                     45, 'iMessage')
                """
            )
            connection.execute("INSERT INTO chat_handle_join VALUES (5, 5)")
            connection.executemany(
                """
                INSERT INTO message
                    (ROWID, guid, text, date, is_from_me, account, handle_id,
                     service, destination_caller_id)
                VALUES (?, ?, 'fixture', ?, ?, 'E:me@example.com', ?,
                        'iMessage', ?)
                """,
                [
                    (5, "alias-incoming", 5_000_000_000, 0, 2, "+15550009999"),
                    (6, "alias-outgoing", 6_000_000_000, 1, 2, "+15550009999"),
                    (7, "self-outgoing", 7_000_000_000, 1, 5, "+15550009999"),
                    (8, "unconfirmed", 8_000_000_000, 1, 2, "+15550008888"),
                ],
            )
            connection.executemany(
                "INSERT INTO chat_message_join VALUES (?, ?)",
                [(2, 5), (2, 6), (5, 7), (2, 8)],
            )

        detected = self.database.self_handles()
        self.assertIn("+15550009999", detected)
        self.assertNotIn("+15550008888", detected)
        chats = {chat["chat_id"] for chat in self.service.list_chats(20)}
        self.assertIn("iMessage;-;+15550009999", chats)
        self.assertNotIn("iMessage;-;+15551112222", chats)

    def test_self_detection_ignores_sms_destination_alias(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO message
                    (ROWID, guid, text, date, is_from_me, account, handle_id,
                     service, destination_caller_id)
                VALUES (?, ?, 'fixture', ?, ?, 'E:me@example.com', 4,
                        'SMS', '+15550007777')
                """,
                [
                    (5, "sms-incoming", 5_000_000_000, 0),
                    (6, "sms-outgoing", 6_000_000_000, 1),
                ],
            )
        self.assertNotIn("+15550007777", self.database.self_handles())

    def test_self_detection_supports_legacy_schema_without_destination(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "ALTER TABLE message DROP COLUMN destination_caller_id"
            )
        self.assertEqual(frozenset({"me@example.com"}), self.database.self_handles())

    def test_address_handle_validation_rejects_short_codes(self) -> None:
        self.assertTrue(is_address_handle("+15550009999"))
        self.assertTrue(is_address_handle("owner@example.com"))
        self.assertFalse(is_address_handle("12345"))
        self.assertFalse(is_address_handle("not-an-address"))

    def test_direct_and_group_access_require_explicit_exact_allowlists(self) -> None:
        group = GroupAccess(
            participants=("+15551112222", "friend@example.com"),
            label="Friends",
        )
        self.save(
            AccessPolicy(
                owner_handles=frozenset(),
                allowed_handles=frozenset({"+15551112222"}),
                allowed_groups={"iMessage;+;group1": group},
            )
        )

        chats = {chat["chat_id"] for chat in self.service.list_chats(20)}
        self.assertEqual(
            {
                "iMessage;-;me@example.com",
                "iMessage;-;+15551112222",
                "iMessage;+;group1",
            },
            chats,
        )

        changed = GroupAccess(participants=("+15551112222",), label="Stale")
        self.save(
            AccessPolicy(
                owner_handles=frozenset(),
                allowed_handles=frozenset({"+15551112222"}),
                allowed_groups={"iMessage;+;group1": changed},
            )
        )
        self.assertNotIn(
            "iMessage;+;group1",
            {chat["chat_id"] for chat in self.service.list_chats(20)},
        )

    def test_sms_rcs_requires_opt_in_even_for_spoofed_self_handle(self) -> None:
        self.assertNotIn(
            "SMS;-;me@example.com",
            {chat["chat_id"] for chat in self.service.list_chats(20)},
        )
        self.save(
            AccessPolicy(
                owner_handles=frozenset(),
                allowed_handles=frozenset(),
                allowed_groups={},
                allow_sms_rcs=True,
            )
        )
        self.assertIn(
            "SMS;-;me@example.com",
            {chat["chat_id"] for chat in self.service.list_chats(20)},
        )

    def test_config_is_atomic_and_owner_only(self) -> None:
        policy = AccessPolicy(
            owner_handles=frozenset({"me@example.com"}),
            allowed_handles=frozenset({"+15551112222"}),
            allowed_groups={},
        )
        self.save(policy)
        self.assertEqual(policy, self.config.load())
        self.assertEqual(0o600, self.config_path.stat().st_mode & 0o777)
        self.assertEqual(0o700, self.config_path.parent.stat().st_mode & 0o777)
        self.assertEqual([], list(self.config_path.parent.glob(".access.json.*")))

    def test_messages_decode_typed_body_and_search_is_scoped(self) -> None:
        group = GroupAccess(
            participants=("+15551112222", "friend@example.com"),
            label="Friends",
        )
        self.save(
            AccessPolicy(
                owner_handles=frozenset(),
                allowed_handles=frozenset({"+15551112222"}),
                allowed_groups={"iMessage;+;group1": group},
            )
        )
        messages = self.service.messages("iMessage;+;group1", 10)
        self.assertEqual("hello", messages[0]["text"])
        results = self.service.search("friend", 10)
        self.assertEqual(["iMessage;-;+15551112222"], [item["chat"]["chat_id"] for item in results])
        self.assertEqual([], self.service.search("spoofed", 10))

        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO message
                    (guid, text, date, is_from_me, handle_id, service)
                VALUES (?, 'hello from friend', ?, 0, 4, 'SMS')
                """,
                ((f"denied-{index}", 10_000_000_000 + index) for index in range(1100)),
            )
            first_row = connection.execute(
                "SELECT MAX(ROWID) - 1099 FROM message"
            ).fetchone()[0]
            connection.executemany(
                "INSERT INTO chat_message_join VALUES (4, ?)",
                ((first_row + index,) for index in range(1100)),
            )
        results = self.service.search("hello from friend", 10)
        self.assertEqual(
            ["iMessage;-;+15551112222"],
            [item["chat"]["chat_id"] for item in results],
        )

    def test_send_uses_fixed_applescript_and_argv(self) -> None:
        self.save(
            AccessPolicy(
                owner_handles=frozenset(),
                allowed_handles=frozenset({"+15551112222"}),
                allowed_groups={},
            )
        )
        dangerous = 'hello"\ndo shell script "touch /tmp/nope"'
        completed = type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        with patch("imessage.platform.system", return_value="Darwin"), patch(
            "imessage.subprocess.run", return_value=completed
        ) as run:
            result = self.service.send("iMessage;-;+15551112222", dangerous)

        self.assertEqual(1, result["chunks_sent"])
        arguments = run.call_args.args[0]
        script = run.call_args.kwargs["input"]
        self.assertIn(dangerous, arguments)
        self.assertNotIn(dangerous, script)
        self.assertIn("chat id chatID", script)

    def test_partial_send_error_reports_delivered_chunk_count(self) -> None:
        self.save(
            AccessPolicy(
                owner_handles=frozenset(),
                allowed_handles=frozenset({"+15551112222"}),
                allowed_groups={},
            )
        )
        success = type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        failure = type(
            "Completed",
            (),
            {"returncode": 1, "stdout": "", "stderr": "not permitted"},
        )()
        with patch("imessage.platform.system", return_value="Darwin"), patch(
            "imessage.subprocess.run", side_effect=[success, failure]
        ):
            with self.assertRaisesRegex(SendError, "1 of 2 chunks were sent"):
                self.service.send("iMessage;-;+15551112222", "x" * 10001)

    def test_mcp_lists_tools_and_returns_tool_errors(self) -> None:
        server = MCPServer(lambda: self.service)
        listed = server.dispatch(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertIn("imessage_reply", names)

        denied = server.dispatch(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "imessage_chat_messages",
                    "arguments": {"chat_id": "iMessage;-;+15551112222"},
                },
            }
        )
        self.assertTrue(denied["result"]["isError"])
        self.assertIn("AccessDeniedError", denied["result"]["content"][0]["text"])

    def test_status_explains_when_no_self_chat_matches_owner(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DELETE FROM chat_message_join WHERE chat_id = 1")
            connection.execute("DELETE FROM chat_handle_join WHERE chat_id = 1")
            connection.execute("DELETE FROM chat WHERE ROWID = 1")

        server = MCPServer(lambda: self.service)
        response = server.dispatch(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "imessage_status", "arguments": {}},
            }
        )
        result = response["result"]["structuredContent"]["result"]
        self.assertTrue(result["database_readable"])
        self.assertEqual(0, result["self_chat_count"])
        self.assertEqual(0, result["authorized_chat_count"])
        self.assertIn("No iMessage chat currently matches", result["access_hint"])

    def test_attributed_body_parser_rejects_invalid_payloads(self) -> None:
        self.assertEqual(
            "hello",
            parse_attributed_body(b"NSString\x01\x94\x84\x01+\x05hello"),
        )
        long_message = "x" * 130
        self.assertEqual(
            long_message,
            parse_attributed_body(
                b"NSString\x01\x94\x84\x01+\x81\x82" + long_message.encode()
            ),
        )
        self.assertIsNone(parse_attributed_body(b"unrelated bytes"))

    def test_policy_rejects_malformed_configuration(self) -> None:
        self.config_path.parent.mkdir()
        self.config_path.write_text(json.dumps({"allowSmsRcs": "yes"}), "utf-8")
        with self.assertRaisesRegex(Exception, "allowSmsRcs"):
            self.config.load()


if __name__ == "__main__":
    unittest.main()
