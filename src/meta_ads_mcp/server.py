"""Meta Ads Manager MCP server."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .meta_client import MetaAdsClient
from .drive_client import download_drive_file, list_drive_folder

load_dotenv()

mcp = FastMCP("Meta Ads Manager")


def _meta() -> MetaAdsClient:
    app_id = os.environ["META_APP_ID"]
    app_secret = os.environ["META_APP_SECRET"]
    access_token = os.environ["META_ACCESS_TOKEN"]
    account_id = os.environ["META_AD_ACCOUNT_ID"]
    return MetaAdsClient(app_id, app_secret, access_token, account_id)


def _drive_creds() -> tuple[str | None, str | None]:
    return (
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or None,
        os.getenv("GOOGLE_OAUTH_CREDENTIALS_JSON") or None,
    )


# ── Account ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_account_info() -> str:
    """Get Meta ad account details: name, status, currency, balance, amount spent."""
    info = _meta().get_account_info()
    return json.dumps(info, indent=2)


# ── Campaigns ─────────────────────────────────────────────────────────────────

@mcp.tool()
def list_campaigns(status_filter: str = "") -> str:
    """
    List campaigns in the ad account.

    Args:
        status_filter: Optional status to filter by. One of: ACTIVE, PAUSED, ARCHIVED,
                       DELETED, IN_PROCESS, WITH_ISSUES. Leave blank for all.
    """
    campaigns = _meta().list_campaigns(status_filter or None)
    return json.dumps(campaigns, indent=2)


@mcp.tool()
def create_campaign(
    name: str,
    objective: str,
    status: str = "PAUSED",
    daily_budget_cents: int = 0,
    lifetime_budget_cents: int = 0,
    start_time: str = "",
    stop_time: str = "",
    special_ad_categories: str = "",
) -> str:
    """
    Create a new ad campaign.

    Args:
        name: Campaign name.
        objective: Campaign objective. Common values:
                   OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT,
                   OUTCOME_LEADS, OUTCOME_APP_PROMOTION, OUTCOME_SALES.
        status: PAUSED (default, safe) or ACTIVE.
        daily_budget_cents: Daily budget in cents (e.g. 1000 = $10.00). Use 0 to skip.
        lifetime_budget_cents: Lifetime budget in cents. Use 0 to skip.
        start_time: ISO 8601 datetime string, e.g. "2025-01-01T00:00:00+0000". Leave blank for now.
        stop_time: ISO 8601 datetime string. Leave blank for no end date.
        special_ad_categories: Comma-separated list if ad covers housing/employment/credit/social issues.
                                Usually leave blank.
    """
    cats = [c.strip() for c in special_ad_categories.split(",") if c.strip()] if special_ad_categories else []
    result = _meta().create_campaign(
        name=name,
        objective=objective,
        status=status,
        daily_budget=daily_budget_cents or None,
        lifetime_budget=lifetime_budget_cents or None,
        start_time=start_time or None,
        stop_time=stop_time or None,
        special_ad_categories=cats,
    )
    return json.dumps(result, indent=2)


# ── Ad Sets ───────────────────────────────────────────────────────────────────

@mcp.tool()
def list_ad_sets(campaign_id: str = "") -> str:
    """
    List ad sets. Optionally filter by campaign.

    Args:
        campaign_id: Campaign ID to filter by. Leave blank to list all ad sets.
    """
    ad_sets = _meta().list_ad_sets(campaign_id or None)
    return json.dumps(ad_sets, indent=2)


@mcp.tool()
def create_ad_set(
    name: str,
    campaign_id: str,
    optimization_goal: str,
    billing_event: str,
    targeting_json: str,
    daily_budget_cents: int = 0,
    lifetime_budget_cents: int = 0,
    bid_amount_cents: int = 0,
    status: str = "PAUSED",
    start_time: str = "",
    end_time: str = "",
) -> str:
    """
    Create an ad set inside a campaign.

    Args:
        name: Ad set name.
        campaign_id: ID of the parent campaign.
        optimization_goal: What to optimize for. Common values:
                           REACH, IMPRESSIONS, LINK_CLICKS, LANDING_PAGE_VIEWS,
                           LEAD_GENERATION, CONVERSIONS, VIDEO_VIEWS, THRUPLAY.
        billing_event: When you get charged. Common: IMPRESSIONS, LINK_CLICKS,
                       THRUPLAY (for video).
        targeting_json: JSON string defining the target audience. Example:
                        {"geo_locations":{"countries":["US"]},
                         "age_min":25,"age_max":54,
                         "genders":[1],
                         "interests":[{"id":"6003139266461","name":"Fitness"}]}
        daily_budget_cents: Daily budget in cents. Use 0 to skip (then set lifetime_budget_cents).
        lifetime_budget_cents: Lifetime budget in cents. Use 0 to skip.
        bid_amount_cents: Manual bid cap in cents. Use 0 for automatic bidding.
        status: PAUSED (default) or ACTIVE.
        start_time: ISO 8601 datetime. Leave blank to start immediately.
        end_time: ISO 8601 datetime. Leave blank for no end date.
    """
    targeting = json.loads(targeting_json) if targeting_json else None
    result = _meta().create_ad_set(
        name=name,
        campaign_id=campaign_id,
        daily_budget=daily_budget_cents or None,
        lifetime_budget=lifetime_budget_cents or None,
        billing_event=billing_event,
        optimization_goal=optimization_goal,
        targeting=targeting,
        status=status,
        start_time=start_time or None,
        end_time=end_time or None,
        bid_amount=bid_amount_cents or None,
    )
    return json.dumps(result, indent=2)


# ── Media upload ──────────────────────────────────────────────────────────────

@mcp.tool()
def upload_image(file_path: str) -> str:
    """
    Upload an image from the local filesystem to your Meta ad account.
    Returns an image hash you can use when creating ad creatives.

    Args:
        file_path: Absolute path to the image file (JPG, PNG, GIF).
    """
    result = _meta().upload_image(file_path)
    return json.dumps(result, indent=2)


@mcp.tool()
def upload_video(file_path: str, title: str = "") -> str:
    """
    Upload a video from the local filesystem to your Meta ad account.
    Returns a video_id you can use when creating ad creatives.

    Args:
        file_path: Absolute path to the video file (MP4, MOV, AVI, etc.).
        title: Optional title for the video.
    """
    result = _meta().upload_video(file_path, title or None)
    return json.dumps(result, indent=2)


@mcp.tool()
def download_from_google_drive(file_id: str, dest_dir: str = "") -> str:
    """
    Download a file from Google Drive to the local filesystem.
    Use the file_id from the Drive URL: drive.google.com/file/d/<FILE_ID>/view
    Returns the local path of the downloaded file.

    Args:
        file_id: Google Drive file ID.
        dest_dir: Optional local directory to save the file. Defaults to system temp.
    """
    sa_json, oauth_json = _drive_creds()
    local_path = download_drive_file(
        file_id=file_id,
        service_account_json=sa_json,
        oauth_json=oauth_json,
        dest_dir=dest_dir or None,
    )
    return json.dumps({"local_path": local_path}, indent=2)


@mcp.tool()
def list_google_drive_folder(folder_id: str) -> str:
    """
    List files inside a Google Drive folder.
    Use the folder_id from the Drive URL: drive.google.com/drive/folders/<FOLDER_ID>

    Args:
        folder_id: Google Drive folder ID.
    """
    sa_json, oauth_json = _drive_creds()
    files = list_drive_folder(folder_id, sa_json, oauth_json)
    return json.dumps(files, indent=2)


# ── Ad Creatives ──────────────────────────────────────────────────────────────

@mcp.tool()
def create_image_ad_creative(
    name: str,
    image_hash: str,
    page_id: str,
    message: str,
    link: str,
    headline: str = "",
    description: str = "",
    call_to_action: str = "LEARN_MORE",
) -> str:
    """
    Create an image-based ad creative.

    Args:
        name: Creative name (internal label).
        image_hash: Hash returned by upload_image.
        page_id: Your Facebook Page ID (the page the ad will come from).
        message: Primary text / body copy of the ad.
        link: Destination URL when someone clicks the ad.
        headline: Bold headline shown below the image. Optional.
        description: Description shown below the headline. Optional.
        call_to_action: Button label. Options: LEARN_MORE, SHOP_NOW, SIGN_UP,
                        BOOK_NOW, CONTACT_US, DOWNLOAD, GET_QUOTE, SUBSCRIBE,
                        WATCH_MORE, APPLY_NOW, GET_OFFER, ORDER_NOW, NO_BUTTON.
    """
    result = _meta().create_image_ad_creative(
        name=name,
        image_hash=image_hash,
        page_id=page_id,
        message=message,
        link=link,
        headline=headline or None,
        description=description or None,
        call_to_action_type=call_to_action,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def create_video_ad_creative(
    name: str,
    video_id: str,
    page_id: str,
    message: str,
    link: str,
    title: str = "",
    description: str = "",
    call_to_action: str = "LEARN_MORE",
    thumbnail_url: str = "",
) -> str:
    """
    Create a video-based ad creative.

    Args:
        name: Creative name (internal label).
        video_id: Video ID returned by upload_video.
        page_id: Your Facebook Page ID.
        message: Primary text / body copy of the ad.
        link: Destination URL when someone clicks.
        title: Video title shown in the ad. Optional.
        description: Description text. Optional.
        call_to_action: Button label. See create_image_ad_creative for options.
        thumbnail_url: URL of a custom thumbnail image. Optional.
    """
    result = _meta().create_video_ad_creative(
        name=name,
        video_id=video_id,
        page_id=page_id,
        message=message,
        link=link,
        title=title or None,
        description=description or None,
        call_to_action_type=call_to_action,
        image_url=thumbnail_url or None,
    )
    return json.dumps(result, indent=2)


# ── Ads ───────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_ads(ad_set_id: str = "", campaign_id: str = "") -> str:
    """
    List ads. Filter by ad_set_id or campaign_id (optional).

    Args:
        ad_set_id: Filter by ad set. Leave blank to ignore.
        campaign_id: Filter by campaign. Leave blank to ignore.
    """
    ads = _meta().list_ads(ad_set_id or None, campaign_id or None)
    return json.dumps(ads, indent=2)


@mcp.tool()
def create_ad(
    name: str,
    ad_set_id: str,
    creative_id: str,
    status: str = "PAUSED",
) -> str:
    """
    Create an ad by linking an ad set and an ad creative.

    Args:
        name: Ad name.
        ad_set_id: ID of the ad set this ad belongs to.
        creative_id: ID of the ad creative to use.
        status: PAUSED (default, safe to review before going live) or ACTIVE.
    """
    result = _meta().create_ad(
        name=name,
        ad_set_id=ad_set_id,
        creative_id=creative_id,
        status=status,
    )
    return json.dumps(result, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    mcp.run()


if __name__ == "__main__":
    main()
