"""Meta Marketing API client wrapper."""

import os
from pathlib import Path
from typing import Any

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.advideo import AdVideo


class MetaAdsClient:
    def __init__(self, app_id: str, app_secret: str, access_token: str, ad_account_id: str):
        FacebookAdsApi.init(app_id, app_secret, access_token)
        self.account_id = ad_account_id
        self.account = AdAccount(ad_account_id)

    # ── Account ──────────────────────────────────────────────────────────────

    def get_account_info(self) -> dict:
        fields = [
            "name", "account_status", "currency", "timezone_name",
            "amount_spent", "balance", "spend_cap",
        ]
        data = self.account.api_get(fields=fields)
        return dict(data)

    # ── Campaigns ─────────────────────────────────────────────────────────────

    def list_campaigns(self, status_filter: str | None = None) -> list[dict]:
        fields = ["name", "status", "objective", "daily_budget", "lifetime_budget", "start_time", "stop_time"]
        params: dict[str, Any] = {}
        if status_filter:
            params["effective_status"] = [status_filter]
        campaigns = self.account.get_campaigns(fields=fields, params=params)
        return [dict(c) for c in campaigns]

    def create_campaign(
        self,
        name: str,
        objective: str,
        status: str = "PAUSED",
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        start_time: str | None = None,
        stop_time: str | None = None,
        special_ad_categories: list[str] | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": special_ad_categories or [],
        }
        if daily_budget:
            params["daily_budget"] = daily_budget
        if lifetime_budget:
            params["lifetime_budget"] = lifetime_budget
        if start_time:
            params["start_time"] = start_time
        if stop_time:
            params["stop_time"] = stop_time

        campaign = self.account.create_campaign(fields=["id", "name"], params=params)
        return dict(campaign)

    # ── Ad Sets ───────────────────────────────────────────────────────────────

    def list_ad_sets(self, campaign_id: str | None = None) -> list[dict]:
        fields = ["name", "status", "campaign_id", "daily_budget", "lifetime_budget",
                  "billing_event", "optimization_goal", "targeting", "start_time", "end_time"]
        if campaign_id:
            campaign = Campaign(campaign_id)
            ad_sets = campaign.get_ad_sets(fields=fields)
        else:
            ad_sets = self.account.get_ad_sets(fields=fields)
        return [dict(s) for s in ad_sets]

    def create_ad_set(
        self,
        name: str,
        campaign_id: str,
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        billing_event: str = "IMPRESSIONS",
        optimization_goal: str = "REACH",
        targeting: dict | None = None,
        status: str = "PAUSED",
        start_time: str | None = None,
        end_time: str | None = None,
        bid_amount: int | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "name": name,
            "campaign_id": campaign_id,
            "billing_event": billing_event,
            "optimization_goal": optimization_goal,
            "targeting": targeting or {"geo_locations": {"countries": ["US"]}},
            "status": status,
        }
        if daily_budget:
            params["daily_budget"] = daily_budget
        if lifetime_budget:
            params["lifetime_budget"] = lifetime_budget
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if bid_amount:
            params["bid_amount"] = bid_amount

        ad_set = self.account.create_ad_set(fields=["id", "name"], params=params)
        return dict(ad_set)

    # ── Media upload ──────────────────────────────────────────────────────────

    def upload_image(self, file_path: str) -> dict:
        """Upload an image file and return its hash + url."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {file_path}")

        image = AdImage(parent_id=self.account_id)
        image[AdImage.Field.filename] = str(path)
        image.remote_create()
        return {
            "hash": image[AdImage.Field.hash],
            "url": image.get("url", ""),
            "name": path.name,
        }

    def upload_video(self, file_path: str, title: str | None = None) -> dict:
        """Upload a video file and return its id."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {file_path}")

        video = AdVideo(parent_id=self.account_id)
        video[AdVideo.Field.filepath] = str(path)
        if title:
            video[AdVideo.Field.title] = title
        video.remote_create()
        return {
            "video_id": video["id"],
            "name": path.name,
        }

    # ── Ad Creatives ──────────────────────────────────────────────────────────

    def create_image_ad_creative(
        self,
        name: str,
        image_hash: str,
        page_id: str,
        message: str,
        link: str,
        headline: str | None = None,
        description: str | None = None,
        call_to_action_type: str = "LEARN_MORE",
    ) -> dict:
        link_data: dict[str, Any] = {
            "image_hash": image_hash,
            "link": link,
            "message": message,
            "call_to_action": {"type": call_to_action_type, "value": {"link": link}},
        }
        if headline:
            link_data["name"] = headline
        if description:
            link_data["description"] = description

        params: dict[str, Any] = {
            "name": name,
            "object_story_spec": {
                "page_id": page_id,
                "link_data": link_data,
            },
        }
        creative = self.account.create_ad_creative(fields=["id", "name"], params=params)
        return dict(creative)

    def create_video_ad_creative(
        self,
        name: str,
        video_id: str,
        page_id: str,
        message: str,
        link: str,
        title: str | None = None,
        description: str | None = None,
        call_to_action_type: str = "LEARN_MORE",
        image_url: str | None = None,
    ) -> dict:
        video_data: dict[str, Any] = {
            "video_id": video_id,
            "message": message,
            "link": link,
            "call_to_action": {"type": call_to_action_type, "value": {"link": link}},
        }
        if title:
            video_data["title"] = title
        if description:
            video_data["description"] = description
        if image_url:
            video_data["image_url"] = image_url

        params: dict[str, Any] = {
            "name": name,
            "object_story_spec": {
                "page_id": page_id,
                "video_data": video_data,
            },
        }
        creative = self.account.create_ad_creative(fields=["id", "name"], params=params)
        return dict(creative)

    # ── Ads ───────────────────────────────────────────────────────────────────

    def list_ads(self, ad_set_id: str | None = None, campaign_id: str | None = None) -> list[dict]:
        fields = ["name", "status", "adset_id", "campaign_id", "creative", "effective_status"]
        if ad_set_id:
            ad_set = AdSet(ad_set_id)
            ads = ad_set.get_ads(fields=fields)
        elif campaign_id:
            campaign = Campaign(campaign_id)
            ads = campaign.get_ads(fields=fields)
        else:
            ads = self.account.get_ads(fields=fields)
        return [dict(a) for a in ads]

    def create_ad(
        self,
        name: str,
        ad_set_id: str,
        creative_id: str,
        status: str = "PAUSED",
    ) -> dict:
        params: dict[str, Any] = {
            "name": name,
            "adset_id": ad_set_id,
            "creative": {"creative_id": creative_id},
            "status": status,
        }
        ad = self.account.create_ad(fields=["id", "name"], params=params)
        return dict(ad)
