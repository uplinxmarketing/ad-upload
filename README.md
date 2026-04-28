# Meta Ads Manager MCP

An MCP server that gives Claude direct access to Meta Ads Manager via the Marketing API.
Upload images/videos from your computer or Google Drive and create complete ad campaigns without touching a browser.

## What Claude can do with this

- Check your ad account balance and status
- List and create campaigns (Awareness, Traffic, Leads, Sales, etc.)
- List and create ad sets with targeting (location, age, gender, interests)
- Upload images and videos from your local machine
- Download assets from Google Drive then upload them to Meta
- Create image and video ad creatives with custom copy
- Publish ads (always starts as PAUSED so you can review first)

## Setup

### 1. Install

```bash
pip install -e .
```

### 2. Get Meta credentials

1. Go to [developers.facebook.com](https://developers.facebook.com/) and create an app (type: **Business**).
2. Add the **Marketing API** product.
3. Generate a **User Access Token** with these permissions:
   - `ads_management`
   - `ads_read`
   - `pages_read_engagement` (needed to post from your Page)
4. Convert it to a **long-lived token** (60-day) using the Graph API Explorer or the token exchange endpoint.
5. Find your **Ad Account ID** in Ads Manager — it looks like `act_123456789`.
6. Find your **Facebook Page ID** — visible in your Page settings.

### 3. Configure environment

```bash
cp .env.example .env
# Fill in your values
```

```env
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_long_lived_token
META_AD_ACCOUNT_ID=act_your_account_id
```

### 4. (Optional) Google Drive credentials

**Service account (recommended for shared team drives):**
1. Go to Google Cloud Console → IAM → Service Accounts → Create.
2. Download the JSON key file.
3. Share the Drive folder with the service account email.
4. Set `GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/key.json`.

**OAuth (recommended for personal Drive):**
1. Go to Google Cloud Console → APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app).
2. Download the JSON.
3. Set `GOOGLE_OAUTH_CREDENTIALS_JSON=/path/to/credentials.json`.
4. On first use, a browser window will open to authorize access.

### 5. Add to Claude Code (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "python",
      "args": ["-m", "meta_ads_mcp.server"],
      "cwd": "/path/to/ad-upload/src",
      "env": {
        "META_APP_ID": "your_app_id",
        "META_APP_SECRET": "your_app_secret",
        "META_ACCESS_TOKEN": "your_token",
        "META_AD_ACCOUNT_ID": "act_your_id",
        "GOOGLE_SERVICE_ACCOUNT_JSON": "/path/to/key.json"
      }
    }
  }
}
```

Or if you use a `.env` file:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "python",
      "args": ["-m", "meta_ads_mcp.server"],
      "cwd": "/path/to/ad-upload/src"
    }
  }
}
```

## Example conversations with Claude

**Upload an image ad from your computer:**
> "Upload /Users/me/Desktop/promo.jpg to my Meta account, then create an ad creative with the headline 'Summer Sale', body copy 'Up to 50% off everything', link to myshop.com, and a Shop Now button. Then build a Traffic campaign targeting US users aged 25–44 with a $20/day budget."

**Pull from Google Drive:**
> "Download the video with Drive ID `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs` and upload it as a video ad. Use this copy: [your text]. Target women 30–55 in New York and California."

**Check what's running:**
> "List all my active campaigns and show me the ads under the Summer Sale campaign."

## Available Tools

| Tool | Description |
|------|-------------|
| `get_account_info` | Account name, status, currency, balance |
| `list_campaigns` | List campaigns with optional status filter |
| `create_campaign` | Create a campaign with objective and budget |
| `list_ad_sets` | List ad sets, optionally filtered by campaign |
| `create_ad_set` | Create an ad set with targeting and budget |
| `upload_image` | Upload image from local path → returns image hash |
| `upload_video` | Upload video from local path → returns video ID |
| `download_from_google_drive` | Download Drive file → returns local path |
| `list_google_drive_folder` | List files in a Drive folder |
| `create_image_ad_creative` | Create creative with image + copy |
| `create_video_ad_creative` | Create creative with video + copy |
| `list_ads` | List ads, optionally filtered |
| `create_ad` | Create ad linking ad set + creative |

## Budget note

All values are in **cents** (USD). `1000` = $10.00. Ads are always created as `PAUSED` by default — Claude will not accidentally spend money without you explicitly setting status to `ACTIVE`.

## Token refresh

Meta access tokens expire after 60 days. When yours expires:
1. Go to Graph API Explorer → generate a new short-lived token.
2. Exchange it: `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN`
3. Update `META_ACCESS_TOKEN` in your `.env`.
