# Uplinx Meta Manager

A locally-run web application that connects to Meta (Facebook/Instagram) via OAuth and uses Claude AI to manage ad campaigns through a conversational chat interface. Upload creatives, schedule posts, pull analytics, and orchestrate your entire Meta advertising workflow — all from a single chat window running on your own machine.

---

## Prerequisites

- Python 3.10+
- Meta Developer App (App ID + App Secret)
- Anthropic API key
- Google Cloud OAuth credentials (optional, for Google Docs/Drive integration)

---

## Quick Start

### Windows

```
1. Double-click install.bat
2. Edit .env with your credentials
3. Double-click start.bat
4. Open http://localhost:8000
```

### Mac / Linux

```bash
chmod +x install.sh start.sh
./install.sh
# Edit .env with your credentials
./start.sh
```

---

## Getting Your API Credentials

### Meta App ID and Secret

1. Go to https://developers.facebook.com/apps/
2. Click **Create App** → choose **Business** type
3. Fill in an app name → click **Create**
4. Go to **App Settings → Basic**
5. Copy your **App ID** and **App Secret**
6. Under **Add a Product**, add **Facebook Login**
7. In **Facebook Login → Settings**, set **Valid OAuth Redirect URIs** to:
   ```
   http://localhost:8000/auth/meta/callback
   ```
8. Set **App Mode** to **Development** for testing
9. To share with others before App Review: go to **Roles → Test Users** and add their Facebook email

### Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign in or create an account
3. Go to **API Keys → Create Key**
4. Copy the key — it starts with `sk-ant-`

### Google OAuth Credentials (Optional)

1. Go to https://console.cloud.google.com/
2. Create a new project or select an existing one
3. Go to **APIs & Services** → enable the following APIs:
   - Google Docs API
   - Google Sheets API
   - Google Drive API
4. Go to **Credentials → Create Credentials → OAuth 2.0 Client IDs**
5. Set **Application type** to **Web application**
6. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/auth/google/callback
   ```
7. Click **Download JSON** and copy `client_id` and `client_secret` into your `.env`

---

## Configuration (.env)

After running the installer, open `.env` in any text editor and fill in your values:

```env
# ── Meta ──────────────────────────────────────────────────────────────────────
META_APP_ID=123456789012345          # Your Meta App ID from App Settings → Basic
META_APP_SECRET=abc123...            # Your Meta App Secret (keep this private)
META_REDIRECT_URI=http://localhost:8000/auth/meta/callback
                                     # Must exactly match the URI in your Meta App settings

# ── Anthropic ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...         # Your Anthropic API key

# ── Google (optional) ─────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID=                    # From Google Cloud Console OAuth credentials
GOOGLE_CLIENT_SECRET=                # From Google Cloud Console OAuth credentials
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# ── App ───────────────────────────────────────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
                                     # Used to sign session cookies — generate with:
                                     # python -c "import secrets; print(secrets.token_hex(32))"
ENCRYPTION_KEY=                      # Auto-generated on first run; do NOT change after setup
                                     # Changing this will invalidate all stored tokens

DATABASE_URL=sqlite:///./app.db      # Path to the SQLite database file

MAX_UPLOAD_SIZE_MB=50                # Maximum file size for creative uploads (increase for videos)
```

> **Never commit `.env` to git.** The `.gitignore` already excludes it, but double-check before pushing.

---

## Adding Test Users (Before Meta App Review)

If you want to share the app with clients before submitting it for Meta App Review, you need to add them as test users:

1. In your Meta App Dashboard, go to **Roles → Test Users**
2. Click **Add** and enter their Facebook email address
3. They will receive an invitation — they must accept it before they can connect
4. Once accepted, they can connect their account at `http://localhost:8000/auth/meta`

> Test users have the same access as you during development. App Review is only required when you want to onboard users who are not listed under Roles.

---

## Using the App

### Connecting Accounts

1. Click **Connections** in the left sidebar
2. Click **Connect Meta Account** → a Facebook OAuth window will open → authorize the app
3. Optionally click **Connect Google Account** to enable Google Drive and Docs integration

### Creating a Client

1. Click **+ New Client** in the sidebar
2. Fill in the client's name, industry, and a colour for easy identification
3. Under the **Ad Accounts** tab, add their Meta ad account and configure defaults:
   - Default Facebook Page
   - Default Pixel
   - Default daily budget
   - Target countries
   - Timezone

### Using the Chat

The chat interface is the primary way to interact with the app. Speak naturally:

- `"Create a campaign for Spain with €20/day budget targeting 25–45 year olds"`
- `"Pause all campaigns that have a CPM above €8"`
- `"Pull last week's performance and summarise by ad set"`

**Tips:**
- Type `/` to see a list of available quick commands
- Drag and drop images directly into the chat to upload creatives
- Click the attach button to upload images or video files
- Switch between clients using the dropdown at the top of the sidebar — the context resets automatically

### Creating Skills

Skills are Markdown files that give Claude specific, persistent instructions tailored to your workflow or a particular client.

1. Go to **Skills** in the sidebar
2. Click **Upload Skill** to upload an existing `.md` file, or write one directly in the editor
3. Assign the skill to a specific client, or mark it as **Global** to apply it to all clients
4. Toggle skills on (green) or off using the switch next to each skill

Claude reads all active skills at the start of every conversation. Use skills to encode naming conventions, approval processes, reporting templates, or any standing instructions you would otherwise repeat.

### Quick Commands

Quick commands are shortcuts that expand into full prompts. Type `/` in the chat input to browse them:

| Command | What it does |
|---|---|
| `/upload-ads` | Upload all ads from the active folder using the last shared doc |
| `/weekly-report` | Performance report for the last 7 days |
| `/monthly-report` | Last 30 days with recommendations |
| `/pause-all` | Lists all active campaigns and asks for confirmation before pausing |
| `/list-campaigns` | Shows all campaigns with status and current budget |

To create custom commands: go to **Settings → Quick Commands → New Command**, write the trigger (e.g. `/my-command`) and the full prompt it should expand to.

---

## Installing on a Second Device

1. **Export client data:** right-click a client in the sidebar → **Export** (saves a `.json` file)
2. **Copy your `.env` file** to the new device (keep it out of shared drives or cloud sync)
3. On the new device, run `install.bat` (Windows) or `./install.sh` (Mac/Linux)
4. Paste your `.env` into the project folder
5. Import client data via **Settings → Import**
6. Re-authenticate your Meta and Google accounts — OAuth tokens are device-specific and cannot be transferred

---

## Security

- All OAuth tokens are **encrypted at rest** using Fernet symmetric encryption
- Tokens are **never sent to the frontend** — they live only in the server-side database
- Session cookies are **signed** and expire after **8 hours of inactivity**
- Requests are **rate limited** to 60 per minute per IP address
- **CORS is restricted to localhost only** — the API will not respond to requests from other origins

**Your responsibilities:**

- **Protect your `.env` file** — it contains your `SECRET_KEY` and `ENCRYPTION_KEY`. Anyone with these values can decrypt the token database.
- **Never share your `.db` file** — it contains encrypted tokens and all client data.
- **Never commit `.env` to git** — the `.gitignore` already excludes it, but verify before every push.

---

## Troubleshooting

### 10 Most Common Issues

1. **"Meta account not connected"**
   Token may have expired. Go to **Connections → Reconnect Meta Account** to re-authorize.

2. **"Module not found" on startup**
   The virtual environment is not activated. Run:
   ```
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # Mac / Linux
   ```
   Then start the app again.

3. **OAuth redirect error**
   The `META_REDIRECT_URI` in your `.env` must exactly match the redirect URI saved in your Meta App settings — including the protocol (`http`), host (`localhost`), port, and path. A trailing slash difference will cause this error.

4. **"Invalid state" on OAuth callback**
   This is a cookie issue. Clear browser cookies for `localhost` and try the connection flow again.

5. **File upload fails**
   Check `MAX_UPLOAD_SIZE_MB` in your `.env`. The default is 50 MB. Increase it for large video files and restart the server.

6. **Claude doesn't use my skill**
   Make sure the skill is toggled **ON** (green indicator) in the Skills panel. Skills are loaded fresh at the start of each conversation — they won't apply to a conversation already in progress.

7. **Port 8000 already in use**
   Another process is occupying the port. Either stop that process, or change `--port 8000` in `start.bat` / `start.sh` to another port (e.g. `8001`) and update the redirect URIs in your `.env` and Meta App settings to match.

8. **Google Drive not reading files**
   The file must be shared with at least **view access**. Also confirm that your Google OAuth scopes include `drive.readonly` — re-authenticate Google if you added scopes after the initial connection.

9. **Rate limit errors from Meta**
   The app will automatically slow down requests when approaching Meta's rate limits. The **API Usage** counter in the sidebar shows current consumption. If the app is paused, wait 5 minutes for the window to reset.

10. **"Database locked" error**
    Only one instance of the app should run at a time. Close any other terminal windows running `uvicorn` and restart.

---

## Upgrading

When a new version is released:

```bash
git pull origin main
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
```

Database migrations run automatically on startup. Your existing client data, skills, and settings are preserved.
