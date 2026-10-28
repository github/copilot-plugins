# iMessage for GitHub Copilot CLI

Read authorized Messages.app conversations and send text replies from GitHub
Copilot CLI. Everything runs locally on your Mac: the MCP server opens
`~/Library/Messages/chat.db` read-only and sends through Messages.app with
AppleScript. It does not run or contact an external server.

## Requirements

- macOS with Messages.app signed in to iMessage
- Python 3.10 or later
- Full Disk Access for the terminal or application that runs Copilot CLI
- Automation permission for that application to control Messages.app when
  sending

## Install

The `copilot-plugins` marketplace is registered by default:

```shell
copilot plugin install imessage@copilot-plugins
```

Restart Copilot CLI after granting permissions.

## Permissions

### Read messages

In **System Settings > Privacy & Security > Full Disk Access**, enable the
terminal or desktop application from which you run Copilot CLI. Fully quit and
restart that application afterward. The database is always opened in SQLite
read-only and query-only mode.

### Send messages

The first send should prompt for permission to control Messages.app. If it
doesn't, open **System Settings > Privacy & Security > Automation** and allow
the terminal or application running Copilot CLI to control **Messages**.

## Secure-by-default access

- Only macOS is supported.
- Self handles are detected from authenticated iMessage account records and
  local destination identities observed on both incoming and outgoing
  iMessages; self-chats are allowed. Message recipients and SMS/RCS rows never
  contribute self identities.
- Every other direct sender is denied until explicitly allowlisted.
- Every group is denied until its chat GUID and exact participant snapshot are
  allowed. If membership changes, access closes until the group is allowed
  again.
- SMS, MMS, and RCS are denied by default because their sender IDs can be
  spoofed. Enabling them weakens the self-chat and allowlist trust boundary.
- Message contents are untrusted input. The included skills forbid changing
  access or sending because an iMessage asked Copilot to do so.
- Outbound text and chat IDs are passed to a fixed AppleScript as process
  arguments; they are never interpolated into AppleScript source.
- Messages are accessed only through explicit MCP tool calls. The plugin does
  not poll in the background or initiate Copilot sessions from incoming texts.
- The plugin sends no signature or branding and supports text only.

Access state is stored with owner-only permissions at
`~/Library/Application Support/GitHub Copilot/iMessage/access.json`.
`COPILOT_IMESSAGE_STATE_DIR` can override the directory for direct server
launches; the status tool pins the active path in its helper command.

## Configure access

Ask Copilot to "configure iMessage access." The `imessage_status` tool reports
the exact configuration path and helper command for the installed copy.
It also reports `self_chat_count` and `authorized_chat_count`. If both are zero,
the policy is live but no chat participant matches a detected/configured owner
handle. Start a self-chat addressed exactly to a detected handle, configure the
actual self alias, or explicitly allow a trusted direct handle. Policy and
database changes are read on every tool call; restarting Copilot is unnecessary
unless macOS permissions changed.

For a source checkout, the equivalent commands are:

```shell
# Inspect the current deny-by-default policy
python3 plugins/imessage/server/imessage_mcp.py config show

# Pin explicit owner handles in addition to automatic detection
python3 plugins/imessage/server/imessage_mcp.py config set-owners \
  --detect --handle you@example.com --handle +15551234567

# Allow or remove one direct iMessage handle
python3 plugins/imessage/server/imessage_mcp.py config allow +15557654321
python3 plugins/imessage/server/imessage_mcp.py config remove +15557654321

# List local groups, then allow an exact GUID and participant snapshot
python3 plugins/imessage/server/imessage_mcp.py config list-groups
python3 plugins/imessage/server/imessage_mcp.py config allow-group \
  'iMessage;+;chat123456789' --label 'Family'
python3 plugins/imessage/server/imessage_mcp.py config remove-group \
  'iMessage;+;chat123456789'
```

The helper writes `access.json` atomically with mode `0600`; its directory uses
mode `0700`.

SMS/RCS can only be enabled with an explicit risk acknowledgement:

```shell
python3 plugins/imessage/server/imessage_mcp.py config set-sms-rcs \
  --enabled --acknowledge-spoofing-risk
```

Disable it again with `config set-sms-rcs --disabled`.

## Tools

| Tool | Purpose |
|---|---|
| `imessage_status` | Check platform, database permission, self detection, and policy |
| `imessage_chats` | List recent authorized self/direct/group chats |
| `imessage_chat_messages` | Read one authorized chat |
| `imessage_search` | Search plain-text messages in authorized chats |
| `imessage_reply` | Send text to an authorized chat through Messages.app |

Rich text stored in Apple's binary `attributedBody` format is decoded on a
best-effort basis. Search only covers `message.text`, so some newer rich-text
messages may not be searchable.

## Upstream attribution

The security design and typed-message parsing are derived from Anthropic's
[official iMessage plugin](https://github.com/anthropics/claude-plugins-official/tree/c54b5608d9be1910de9a5b91c2d15bf6673b9c35/external_plugins/imessage),
Copyright 2026 Anthropic, PBC, under the Apache License 2.0. This port was
rewritten for GitHub Copilot CLI and is not endorsed by Anthropic. See
[`NOTICE`](NOTICE) and [`LICENSE`](LICENSE).
