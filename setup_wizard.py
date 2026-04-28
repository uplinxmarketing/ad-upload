#!/usr/bin/env python3
"""
Meta Ads MCP — Interactive Setup Wizard

Guides you through:
  1. Meta Marketing API credentials
  2. Google Drive credentials (optional)
  3. Auto-generates the Claude Desktop / Claude Code MCP config
"""

import json
import os
import platform
import sys
from pathlib import Path

DOTENV_PATH = Path(__file__).parent / ".env"
SRC_PATH = Path(__file__).parent / "src"

BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
DIM = "\033[2m"


def h(text: str) -> str:
    return f"{BOLD}{text}{RESET}"


def ok(text: str) -> str:
    return f"{GREEN}✓ {text}{RESET}"


def warn(text: str) -> str:
    return f"{YELLOW}⚠ {text}{RESET}"


def err(text: str) -> str:
    return f"{RED}✗ {text}{RESET}"


def info(text: str) -> str:
    return f"{CYAN}→ {text}{RESET}"


def prompt(label: str, default: str = "", secret: bool = False) -> str:
    hint = f" [{default}]" if default else ""
    if secret and default:
        hint = f" [****]"
    try:
        val = input(f"  {label}{hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{err('Setup cancelled.')}")
        sys.exit(1)
    return val or default


def load_existing_env() -> dict:
    if not DOTENV_PATH.exists():
        return {}
    env = {}
    for line in DOTENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def save_env(values: dict):
    lines = []
    for k, v in values.items():
        lines.append(f"{k}={v}")
    DOTENV_PATH.write_text("\n".join(lines) + "\n")


def claude_desktop_config_path() -> Path | None:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    return None


def build_mcp_entry(src_path: Path, env_values: dict) -> dict:
    entry: dict = {
        "command": sys.executable,
        "args": ["-m", "meta_ads_mcp.server"],
        "cwd": str(src_path),
    }
    env_block = {}
    for key in [
        "META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID",
        "GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_OAUTH_CREDENTIALS_JSON",
    ]:
        if env_values.get(key):
            env_block[key] = env_values[key]
    if env_block:
        entry["env"] = env_block
    return entry


def update_claude_desktop_config(config_path: Path, mcp_entry: dict):
    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            pass
    config.setdefault("mcpServers", {})
    config["mcpServers"]["meta-ads"] = mcp_entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2))


def main():
    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"{BOLD}  Meta Ads Manager MCP — Setup Wizard{RESET}")
    print(f"{BOLD}{'='*55}{RESET}\n")

    existing = load_existing_env()
    env = dict(existing)

    # ── Step 1: Meta credentials ──────────────────────────────────────────────
    print(h("Step 1 · Meta Marketing API credentials"))
    print(f"{DIM}  Get these at developers.facebook.com → your app → Marketing API{RESET}\n")

    env["META_APP_ID"] = prompt("App ID", existing.get("META_APP_ID", ""))
    env["META_APP_SECRET"] = prompt("App Secret", existing.get("META_APP_SECRET", ""), secret=True)
    env["META_ACCESS_TOKEN"] = prompt(
        "Long-lived Access Token (needs ads_management + ads_read)",
        existing.get("META_ACCESS_TOKEN", ""), secret=True
    )
    env["META_AD_ACCOUNT_ID"] = prompt(
        "Ad Account ID (format: act_XXXXXXXXXX)",
        existing.get("META_AD_ACCOUNT_ID", "")
    )

    meta_ok = all(env.get(k) for k in ["META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"])
    if not meta_ok:
        print(f"\n{err('Meta credentials incomplete — some fields were left blank.')}")
        print(warn("You can re-run this wizard at any time to complete setup."))

    # ── Step 2: Google Drive (optional) ──────────────────────────────────────
    print(f"\n{h('Step 2 · Google Drive (optional)')}")
    print(f"{DIM}  Skip this if you only upload from your computer.{RESET}\n")

    drive_choice = prompt(
        "Set up Google Drive? (y/N)",
        default="n"
    ).lower()

    if drive_choice == "y":
        print(f"\n  {DIM}Option A: Service account JSON (recommended for team/shared drives){RESET}")
        print(f"  {DIM}Option B: OAuth credentials JSON (recommended for personal Drive){RESET}\n")
        drive_type = prompt("Which type? (A/b)", default="A").upper()

        if drive_type == "A":
            env["GOOGLE_SERVICE_ACCOUNT_JSON"] = prompt(
                "Path to service account JSON file",
                existing.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
            )
            env.pop("GOOGLE_OAUTH_CREDENTIALS_JSON", None)
        else:
            env["GOOGLE_OAUTH_CREDENTIALS_JSON"] = prompt(
                "Path to OAuth credentials JSON file",
                existing.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "")
            )
            env.pop("GOOGLE_SERVICE_ACCOUNT_JSON", None)
    else:
        print(f"  {DIM}Skipping Google Drive.{RESET}")

    # ── Save .env ─────────────────────────────────────────────────────────────
    save_env({k: v for k, v in env.items() if v})
    print(f"\n{ok(f'Credentials saved to {DOTENV_PATH}')}")

    # ── Step 3: Claude config ─────────────────────────────────────────────────
    print(f"\n{h('Step 3 · Connect to Claude')}")
    print(f"{DIM}  This adds the MCP server to your Claude Desktop / Claude Code config.{RESET}\n")

    mcp_entry = build_mcp_entry(SRC_PATH, env)

    # Try to auto-update Claude Desktop config
    config_path = claude_desktop_config_path()
    auto_updated = False

    if config_path:
        auto_choice = prompt(
            f"Auto-add to Claude Desktop config at\n  {config_path}\n  Proceed? (Y/n)",
            default="y"
        ).lower()

        if auto_choice != "n":
            try:
                update_claude_desktop_config(config_path, mcp_entry)
                print(f"\n{ok(f'Claude Desktop config updated: {config_path}')}")
                auto_updated = True
            except Exception as e:
                print(f"\n{err(f'Could not update config automatically: {e}')}")

    if not auto_updated:
        print(f"\n{warn('Add this block to your Claude Desktop config manually:')}")
        print(f'{DIM}  File: {config_path or "~/.config/Claude/claude_desktop_config.json"}{RESET}\n')
        snippet = {"mcpServers": {"meta-ads": mcp_entry}}
        print(json.dumps(snippet, indent=2))

    # Claude Code CLI snippet
    print(f"\n{h('For Claude Code (CLI) — add to .claude/settings.json in your project:')}")
    claude_code_snippet = {"mcpServers": {"meta-ads": mcp_entry}}
    print(json.dumps(claude_code_snippet, indent=2))

    # ── Step 4: Verify connection ─────────────────────────────────────────────
    print(f"\n{h('Step 4 · Verify connection')}")
    verify_choice = prompt("Test the Meta API connection now? (Y/n)", default="y").lower()

    if verify_choice != "n":
        # Load newly saved env
        for k, v in env.items():
            os.environ.setdefault(k, v)
        sys.path.insert(0, str(SRC_PATH))
        try:
            from meta_ads_mcp.meta_client import MetaAdsClient
            print(f"\n  {DIM}Connecting to Meta API…{RESET}")
            c = MetaAdsClient(
                env["META_APP_ID"],
                env["META_APP_SECRET"],
                env["META_ACCESS_TOKEN"],
                env["META_AD_ACCOUNT_ID"],
            )
            info_data = c.get_account_info()
            print(f"\n{ok('Connected successfully!')}")
            print(f"  Account name  : {info_data.get('name', '—')}")
            print(f"  Currency      : {info_data.get('currency', '—')}")
            print(f"  Timezone      : {info_data.get('timezone_name', '—')}")
            status_map = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
                          9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE", 101: "CLOSED",
                          201: "ANY_ACTIVE", 202: "ANY_CLOSED"}
            raw_status = info_data.get("account_status")
            status_label = status_map.get(raw_status, str(raw_status))
            print(f"  Account status: {status_label}")
        except KeyError as e:
            print(f"\n{err(f'Missing credential: {e}')}")
        except Exception as e:
            print(f"\n{err(f'Connection failed: {e}')}")
            print(warn("Double-check your App ID, App Secret, and Access Token."))

    # ── Done ──────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"{GREEN}{BOLD}  Setup complete!{RESET}")
    print(f"{BOLD}{'='*55}{RESET}")
    print(f"""
Next steps:
  1. {h('Restart Claude Desktop')} (or reload your Claude Code session)
     so it picks up the new MCP server.

  2. {h('Open the dashboard')} to manage ads visually:
       streamlit run app.py

  3. {h('Talk to Claude')} — it now has access to your Meta account:
       "Upload /path/to/image.jpg and create a Traffic campaign
        targeting US users 25–44 with $20/day budget."

  4. Token expires in ~60 days. Re-run this wizard to refresh.
""")


if __name__ == "__main__":
    main()
