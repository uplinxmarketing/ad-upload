"""Google Drive client — download files by ID to a local temp path."""

import os
import tempfile
from pathlib import Path

import httpx
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
_TOKEN_CACHE = Path.home() / ".meta_ads_mcp_drive_token.pickle"


def _build_service_from_service_account(json_path: str):
    creds = service_account.Credentials.from_service_account_file(json_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _build_service_from_oauth(credentials_json: str):
    creds = None
    if _TOKEN_CACHE.exists():
        with open(_TOKEN_CACHE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_json, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_CACHE, "wb") as f:
            pickle.dump(creds, f)

    return build("drive", "v3", credentials=creds)


def build_drive_service(service_account_json: str | None = None, oauth_json: str | None = None):
    if service_account_json and Path(service_account_json).exists():
        return _build_service_from_service_account(service_account_json)
    if oauth_json and Path(oauth_json).exists():
        return _build_service_from_oauth(oauth_json)
    raise RuntimeError(
        "No Google Drive credentials configured. "
        "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_OAUTH_CREDENTIALS_JSON in your .env file."
    )


def download_drive_file(
    file_id: str,
    service_account_json: str | None = None,
    oauth_json: str | None = None,
    dest_dir: str | None = None,
) -> str:
    """Download a Google Drive file by ID. Returns local file path."""
    service = build_drive_service(service_account_json, oauth_json)

    # Get file metadata to determine name and mime type
    meta = service.files().get(fileId=file_id, fields="name,mimeType").execute()
    filename = meta["name"]

    out_dir = Path(dest_dir) if dest_dir else Path(tempfile.gettempdir()) / "meta_ads_mcp"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest_path = out_dir / filename

    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return str(dest_path)


def list_drive_folder(
    folder_id: str,
    service_account_json: str | None = None,
    oauth_json: str | None = None,
) -> list[dict]:
    """List files in a Google Drive folder."""
    service = build_drive_service(service_account_json, oauth_json)
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id,name,mimeType,size,modifiedTime)",
    ).execute()
    return results.get("files", [])
