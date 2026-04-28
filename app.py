"""
Meta Ads Manager — Streamlit Dashboard
Run with: streamlit run app.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))
from meta_ads_mcp.meta_client import MetaAdsClient
from meta_ads_mcp.drive_client import download_drive_file, list_drive_folder

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Meta Ads Manager",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 500; }
    .metric-card {
        background: #f8f9fa; border-radius: 10px;
        padding: 1rem 1.5rem; margin-bottom: 0.5rem;
    }
    .step-badge {
        background: #1877F2; color: white; border-radius: 50%;
        width: 28px; height: 28px; display: inline-flex;
        align-items: center; justify-content: center;
        font-weight: bold; margin-right: 8px;
    }
    div[data-testid="stSidebarContent"] { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client() -> MetaAdsClient | None:
    try:
        return MetaAdsClient(
            os.environ["META_APP_ID"],
            os.environ["META_APP_SECRET"],
            os.environ["META_ACCESS_TOKEN"],
            os.environ["META_AD_ACCOUNT_ID"],
        )
    except KeyError:
        return None


def client() -> MetaAdsClient:
    c = get_client()
    if c is None:
        st.error("Meta credentials not configured. Run `python setup_wizard.py` first.")
        st.stop()
    return c


def drive_creds():
    return (
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or None,
        os.getenv("GOOGLE_OAUTH_CREDENTIALS_JSON") or None,
    )


def status_badge(status: str) -> str:
    colors = {
        "ACTIVE": "🟢",
        "PAUSED": "🟡",
        "ARCHIVED": "⚫",
        "DELETED": "🔴",
        "IN_PROCESS": "🔵",
        "WITH_ISSUES": "🟠",
    }
    return f"{colors.get(status, '⚪')} {status}"


def currency_fmt(cents: int | str | None, currency: str = "USD") -> str:
    if cents is None:
        return "—"
    try:
        return f"${int(cents)/100:,.2f}"
    except (ValueError, TypeError):
        return str(cents)


# ── Sidebar navigation ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📢 Meta Ads Manager")
    st.divider()
    page = st.radio(
        "Navigate to",
        ["Account", "Upload Media", "Campaigns & Ads", "Create Campaign Wizard"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Credentials loaded from `.env`")
    configured = all(
        os.getenv(k) for k in ["META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]
    )
    if configured:
        st.success("Meta API ✓")
    else:
        st.error("Meta API not configured")
        st.caption("Run `python setup_wizard.py`")

    drive_ok = bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_OAUTH_CREDENTIALS_JSON"))
    if drive_ok:
        st.success("Google Drive ✓")
    else:
        st.warning("Google Drive not configured")


# ── Account page ──────────────────────────────────────────────────────────────

if page == "Account":
    st.title("Account Overview")

    with st.spinner("Loading account info…"):
        try:
            info = client().get_account_info()
        except Exception as e:
            st.error(f"Could not load account: {e}")
            st.stop()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Account Name", info.get("name", "—"))
    with col2:
        st.metric("Status", info.get("account_status", "—"))
    with col3:
        st.metric("Currency", info.get("currency", "—"))
    with col4:
        st.metric("Timezone", info.get("timezone_name", "—"))

    st.divider()
    col5, col6 = st.columns(2)
    with col5:
        spent = info.get("amount_spent")
        st.metric("Amount Spent (lifetime)", currency_fmt(spent))
    with col6:
        balance = info.get("balance")
        st.metric("Account Balance", currency_fmt(balance))

    with st.expander("Raw API response"):
        st.json(info)


# ── Upload Media page ─────────────────────────────────────────────────────────

elif page == "Upload Media":
    st.title("Upload Media")
    st.caption("Upload images or videos to your Meta ad account. You'll get back a hash/ID to use in creatives.")

    tab_local, tab_drive = st.tabs(["📁 Local File", "☁️ Google Drive"])

    # ── Local upload ──────────────────────────────────────────────────────────
    with tab_local:
        media_type = st.radio("File type", ["Image", "Video"], horizontal=True)
        uploaded = st.file_uploader(
            "Drag and drop or browse",
            type=(["jpg", "jpeg", "png", "gif"] if media_type == "Image" else ["mp4", "mov", "avi", "mkv"]),
            label_visibility="collapsed",
        )
        if media_type == "Video":
            video_title = st.text_input("Video title (optional)")

        if uploaded and st.button("Upload to Meta", type="primary", key="upload_local"):
            with tempfile.NamedTemporaryFile(suffix=Path(uploaded.name).suffix, delete=False) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                with st.spinner(f"Uploading {uploaded.name}…"):
                    if media_type == "Image":
                        result = client().upload_image(tmp_path)
                        st.success("Image uploaded!")
                        st.code(result["hash"], language=None)
                        col1, col2 = st.columns(2)
                        col1.metric("Image Hash", result["hash"])
                        col2.info("Copy this hash — you'll need it when creating an image creative.")
                    else:
                        result = client().upload_video(tmp_path, video_title or None)
                        st.success("Video uploaded!")
                        col1, col2 = st.columns(2)
                        col1.metric("Video ID", result["video_id"])
                        col2.info("Copy this ID — you'll need it when creating a video creative.")
                    with st.expander("Full response"):
                        st.json(result)
            except Exception as e:
                st.error(f"Upload failed: {e}")
            finally:
                os.unlink(tmp_path)

    # ── Google Drive upload ───────────────────────────────────────────────────
    with tab_drive:
        if not drive_ok:
            st.warning("Google Drive is not configured. Run `python setup_wizard.py` and add Drive credentials.")
        else:
            st.markdown(
                "Paste the **file ID** from your Drive URL:  \n"
                "`https://drive.google.com/file/d/`**`<FILE_ID>`**`/view`"
            )
            drive_file_id = st.text_input("Google Drive File ID")
            drive_media_type = st.radio("File type", ["Image", "Video"], horizontal=True, key="drive_mt")
            drive_video_title = ""
            if drive_media_type == "Video":
                drive_video_title = st.text_input("Video title (optional)", key="drive_vt")

            col_browse, col_upload = st.columns([1, 1])
            folder_id = st.text_input("Or browse a folder ID", key="folder_browse")
            if folder_id and st.button("List folder contents"):
                sa, oauth = drive_creds()
                try:
                    with st.spinner("Listing folder…"):
                        files = list_drive_folder(folder_id, sa, oauth)
                    st.dataframe(files, use_container_width=True)
                except Exception as e:
                    st.error(f"Could not list folder: {e}")

            if drive_file_id and st.button("Download & Upload to Meta", type="primary", key="upload_drive"):
                sa, oauth = drive_creds()
                try:
                    with st.spinner("Downloading from Drive…"):
                        local_path = download_drive_file(drive_file_id, sa, oauth)
                    st.info(f"Downloaded to `{local_path}`")
                    with st.spinner("Uploading to Meta…"):
                        if drive_media_type == "Image":
                            result = client().upload_image(local_path)
                            st.success("Image uploaded to Meta!")
                            st.metric("Image Hash", result["hash"])
                        else:
                            result = client().upload_video(local_path, drive_video_title or None)
                            st.success("Video uploaded to Meta!")
                            st.metric("Video ID", result["video_id"])
                        with st.expander("Full response"):
                            st.json(result)
                except Exception as e:
                    st.error(f"Failed: {e}")


# ── Campaigns & Ads page ──────────────────────────────────────────────────────

elif page == "Campaigns & Ads":
    st.title("Campaigns & Ads")

    tab_camps, tab_adsets, tab_ads = st.tabs(["Campaigns", "Ad Sets", "Ads"])

    with tab_camps:
        status_options = ["All", "ACTIVE", "PAUSED", "ARCHIVED", "IN_PROCESS", "WITH_ISSUES"]
        status_filter = st.selectbox("Filter by status", status_options, index=0)
        if st.button("Refresh", key="refresh_camps"):
            st.cache_data.clear()

        with st.spinner("Loading campaigns…"):
            try:
                camps = client().list_campaigns(None if status_filter == "All" else status_filter)
            except Exception as e:
                st.error(str(e))
                camps = []

        if not camps:
            st.info("No campaigns found.")
        else:
            for c in camps:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    col1.markdown(f"**{c.get('name', '—')}**  \n`{c.get('id', '')}`")
                    col2.markdown(status_badge(c.get("status", "")))
                    col3.markdown(f"*{c.get('objective', '—')}*")
                    budget = c.get("daily_budget") or c.get("lifetime_budget")
                    budget_label = "Daily" if c.get("daily_budget") else "Lifetime"
                    col4.markdown(f"{budget_label}: {currency_fmt(budget)}")
                    st.divider()

    with tab_adsets:
        camp_id_filter = st.text_input("Filter by Campaign ID (optional)", key="as_filter")
        if st.button("Refresh", key="refresh_as"):
            st.cache_data.clear()

        with st.spinner("Loading ad sets…"):
            try:
                ad_sets = client().list_ad_sets(camp_id_filter or None)
            except Exception as e:
                st.error(str(e))
                ad_sets = []

        if not ad_sets:
            st.info("No ad sets found.")
        else:
            for s in ad_sets:
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.markdown(f"**{s.get('name', '—')}**  \n`{s.get('id', '')}`")
                col2.markdown(status_badge(s.get("status", "")))
                budget = s.get("daily_budget") or s.get("lifetime_budget")
                col3.markdown(f"Budget: {currency_fmt(budget)}")
                st.divider()

    with tab_ads:
        col_f1, col_f2 = st.columns(2)
        ads_adset_filter = col_f1.text_input("Filter by Ad Set ID", key="ad_as_filter")
        ads_camp_filter = col_f2.text_input("Filter by Campaign ID", key="ad_c_filter")

        if st.button("Refresh", key="refresh_ads"):
            st.cache_data.clear()

        with st.spinner("Loading ads…"):
            try:
                ads = client().list_ads(ads_adset_filter or None, ads_camp_filter or None)
            except Exception as e:
                st.error(str(e))
                ads = []

        if not ads:
            st.info("No ads found.")
        else:
            for a in ads:
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.markdown(f"**{a.get('name', '—')}**  \n`{a.get('id', '')}`")
                col2.markdown(status_badge(a.get("effective_status", a.get("status", ""))))
                col3.markdown(f"Ad Set: `{a.get('adset_id', '—')}`")
                st.divider()


# ── Create Campaign Wizard ────────────────────────────────────────────────────

elif page == "Create Campaign Wizard":
    st.title("Create Campaign Wizard")
    st.caption("Step-by-step: Campaign → Ad Set → Media & Copy → Review & Publish")

    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_data" not in st.session_state:
        st.session_state.wizard_data = {}

    step = st.session_state.wizard_step
    data = st.session_state.wizard_data

    # Progress bar
    st.progress(step / 4, text=f"Step {step} of 4")
    st.divider()

    # ── Step 1: Campaign ──────────────────────────────────────────────────────
    if step == 1:
        st.subheader("1 · Campaign Details")

        objectives = [
            "OUTCOME_AWARENESS",
            "OUTCOME_TRAFFIC",
            "OUTCOME_ENGAGEMENT",
            "OUTCOME_LEADS",
            "OUTCOME_APP_PROMOTION",
            "OUTCOME_SALES",
        ]
        objective_labels = {
            "OUTCOME_AWARENESS": "Awareness — reach as many people as possible",
            "OUTCOME_TRAFFIC": "Traffic — send people to your website",
            "OUTCOME_ENGAGEMENT": "Engagement — get likes, comments, shares",
            "OUTCOME_LEADS": "Leads — collect contact information",
            "OUTCOME_APP_PROMOTION": "App Promotion — get app installs",
            "OUTCOME_SALES": "Sales — drive conversions and purchases",
        }

        camp_name = st.text_input("Campaign name *", value=data.get("camp_name", ""))
        objective = st.selectbox(
            "Campaign objective *",
            objectives,
            format_func=lambda x: objective_labels[x],
            index=objectives.index(data.get("objective", "OUTCOME_TRAFFIC")),
        )

        col1, col2 = st.columns(2)
        budget_type = col1.radio("Budget type", ["Daily", "Lifetime"], horizontal=True,
                                  index=0 if data.get("camp_budget_type", "Daily") == "Daily" else 1)
        budget_amount = col2.number_input(
            f"{budget_type} budget ($)",
            min_value=1.0, max_value=100000.0,
            value=float(data.get("camp_budget_amount", 10.0)),
            step=0.50,
        )

        col3, col4 = st.columns(2)
        start_time = col3.text_input("Start date (YYYY-MM-DD, optional)", value=data.get("camp_start", ""))
        stop_time = col4.text_input("Stop date (YYYY-MM-DD, optional)", value=data.get("camp_stop", ""))

        st.caption("Ads start as **PAUSED** — you control when they go live.")

        if st.button("Next →", type="primary", disabled=not camp_name):
            data.update({
                "camp_name": camp_name,
                "objective": objective,
                "camp_budget_type": budget_type,
                "camp_budget_amount": budget_amount,
                "camp_start": start_time,
                "camp_stop": stop_time,
            })
            st.session_state.wizard_step = 2
            st.rerun()

    # ── Step 2: Ad Set ────────────────────────────────────────────────────────
    elif step == 2:
        st.subheader("2 · Ad Set & Targeting")

        adset_name = st.text_input("Ad set name *", value=data.get("adset_name", ""))

        col1, col2 = st.columns(2)
        countries_raw = col1.text_input(
            "Target countries (comma-separated country codes)",
            value=data.get("countries", "US"),
            help="e.g. US, GB, CA, AU",
        )
        page_id = col2.text_input(
            "Facebook Page ID *",
            value=data.get("page_id", ""),
            help="Found in your Page settings. Ads appear from this Page.",
        )

        col3, col4 = st.columns(2)
        age_min = col3.number_input("Min age", min_value=18, max_value=64, value=int(data.get("age_min", 25)))
        age_max = col4.number_input("Max age", min_value=18, max_value=65, value=int(data.get("age_max", 54)))

        genders_options = {"All genders": [], "Men only": [1], "Women only": [2]}
        gender_label = st.radio("Gender", list(genders_options.keys()), horizontal=True,
                                index=list(genders_options.keys()).index(data.get("gender_label", "All genders")))

        opt_goals = ["REACH", "IMPRESSIONS", "LINK_CLICKS", "LANDING_PAGE_VIEWS",
                     "LEAD_GENERATION", "CONVERSIONS", "VIDEO_VIEWS", "THRUPLAY"]
        optimization_goal = st.selectbox(
            "Optimization goal",
            opt_goals,
            index=opt_goals.index(data.get("optimization_goal", "LINK_CLICKS")),
        )

        billing_map = {
            "LINK_CLICKS": "LINK_CLICKS",
            "LANDING_PAGE_VIEWS": "IMPRESSIONS",
            "REACH": "IMPRESSIONS",
            "IMPRESSIONS": "IMPRESSIONS",
            "LEAD_GENERATION": "IMPRESSIONS",
            "CONVERSIONS": "IMPRESSIONS",
            "VIDEO_VIEWS": "THRUPLAY",
            "THRUPLAY": "THRUPLAY",
        }
        billing_event = billing_map.get(optimization_goal, "IMPRESSIONS")
        st.caption(f"Billing event auto-set to: **{billing_event}**")

        col5, col6 = st.columns(2)
        as_budget_type = col5.radio("Ad set budget", ["Daily", "Lifetime"], horizontal=True,
                                     index=0 if data.get("as_budget_type", "Daily") == "Daily" else 1)
        as_budget_amount = col6.number_input(
            f"{as_budget_type} budget ($)",
            min_value=1.0, max_value=100000.0,
            value=float(data.get("as_budget_amount", 10.0)),
            step=0.50,
        )

        col_back, col_next = st.columns([1, 4])
        if col_back.button("← Back"):
            st.session_state.wizard_step = 1
            st.rerun()
        if col_next.button("Next →", type="primary", disabled=not (adset_name and page_id)):
            countries = [c.strip().upper() for c in countries_raw.split(",") if c.strip()]
            targeting = {
                "geo_locations": {"countries": countries},
                "age_min": age_min,
                "age_max": age_max,
            }
            if genders_options[gender_label]:
                targeting["genders"] = genders_options[gender_label]

            data.update({
                "adset_name": adset_name,
                "page_id": page_id,
                "countries": countries_raw,
                "age_min": age_min,
                "age_max": age_max,
                "gender_label": gender_label,
                "targeting": targeting,
                "optimization_goal": optimization_goal,
                "billing_event": billing_event,
                "as_budget_type": as_budget_type,
                "as_budget_amount": as_budget_amount,
            })
            st.session_state.wizard_step = 3
            st.rerun()

    # ── Step 3: Media & Copy ──────────────────────────────────────────────────
    elif step == 3:
        st.subheader("3 · Media & Ad Copy")

        media_type = st.radio("Ad format", ["Image Ad", "Video Ad"], horizontal=True,
                               index=0 if data.get("media_type", "Image Ad") == "Image Ad" else 1)

        creative_name = st.text_input("Creative name *", value=data.get("creative_name", ""))

        st.markdown("**Upload media**")
        tab_loc, tab_drv = st.tabs(["Local File", "Google Drive"])

        with tab_loc:
            file_types = ["jpg", "jpeg", "png", "gif"] if media_type == "Image Ad" else ["mp4", "mov", "avi"]
            uploaded_file = st.file_uploader("Upload file", type=file_types, key="wizard_upload")
            if uploaded_file and st.button("Upload to Meta", key="wiz_upload_local"):
                with tempfile.NamedTemporaryFile(suffix=Path(uploaded_file.name).suffix, delete=False) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                try:
                    with st.spinner("Uploading…"):
                        if media_type == "Image Ad":
                            result = client().upload_image(tmp_path)
                            data["image_hash"] = result["hash"]
                            st.success(f"Uploaded! Image hash: `{result['hash']}`")
                        else:
                            result = client().upload_video(tmp_path)
                            data["video_id"] = result["video_id"]
                            st.success(f"Uploaded! Video ID: `{result['video_id']}`")
                finally:
                    os.unlink(tmp_path)

        with tab_drv:
            if not drive_ok:
                st.warning("Google Drive not configured. Run `python setup_wizard.py`.")
            else:
                wiz_drive_id = st.text_input("Google Drive file ID", key="wiz_drive_id")
                if wiz_drive_id and st.button("Download & Upload", key="wiz_drive_upload"):
                    sa, oauth = drive_creds()
                    with st.spinner("Downloading from Drive…"):
                        local_path = download_drive_file(wiz_drive_id, sa, oauth)
                    with st.spinner("Uploading to Meta…"):
                        if media_type == "Image Ad":
                            result = client().upload_image(local_path)
                            data["image_hash"] = result["hash"]
                            st.success(f"Uploaded! Hash: `{result['hash']}`")
                        else:
                            result = client().upload_video(local_path)
                            data["video_id"] = result["video_id"]
                            st.success(f"Uploaded! Video ID: `{result['video_id']}`")

        # Show already-uploaded media
        if media_type == "Image Ad" and data.get("image_hash"):
            st.info(f"Image hash ready: `{data['image_hash']}`")
        elif media_type == "Video Ad" and data.get("video_id"):
            st.info(f"Video ID ready: `{data['video_id']}`")

        st.divider()
        st.markdown("**Ad copy**")

        primary_text = st.text_area(
            "Primary text (body copy) *",
            value=data.get("primary_text", ""),
            max_chars=2000,
            help="Main text of the ad. Keep it concise and engaging.",
        )
        headline = st.text_input("Headline", value=data.get("headline", ""),
                                  help="Bold text below the image.")
        description = st.text_input("Description", value=data.get("description", ""),
                                     help="Smaller text below the headline.")
        destination_url = st.text_input("Destination URL *", value=data.get("destination_url", ""),
                                         placeholder="https://yourwebsite.com")

        cta_options = ["LEARN_MORE", "SHOP_NOW", "SIGN_UP", "BOOK_NOW", "CONTACT_US",
                       "DOWNLOAD", "GET_QUOTE", "SUBSCRIBE", "WATCH_MORE", "APPLY_NOW",
                       "GET_OFFER", "ORDER_NOW", "NO_BUTTON"]
        cta_labels = {k: k.replace("_", " ").title() for k in cta_options}
        call_to_action = st.selectbox(
            "Call to action button",
            cta_options,
            format_func=lambda x: cta_labels[x],
            index=cta_options.index(data.get("call_to_action", "LEARN_MORE")),
        )

        has_media = (media_type == "Image Ad" and data.get("image_hash")) or \
                    (media_type == "Video Ad" and data.get("video_id"))
        can_proceed = has_media and primary_text and destination_url and creative_name

        col_back, col_next = st.columns([1, 4])
        if col_back.button("← Back", key="back3"):
            st.session_state.wizard_step = 2
            st.rerun()
        if col_next.button("Next →", type="primary", disabled=not can_proceed, key="next3"):
            data.update({
                "media_type": media_type,
                "creative_name": creative_name,
                "primary_text": primary_text,
                "headline": headline,
                "description": description,
                "destination_url": destination_url,
                "call_to_action": call_to_action,
            })
            st.session_state.wizard_step = 4
            st.rerun()

    # ── Step 4: Review & Publish ──────────────────────────────────────────────
    elif step == 4:
        st.subheader("4 · Review & Publish")

        ad_name = st.text_input("Ad name *", value=data.get("ad_name", data.get("camp_name", "") + " — Ad 1"))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Campaign**")
            st.write(f"Name: {data.get('camp_name')}")
            st.write(f"Objective: {data.get('objective')}")
            budget_label = data.get('camp_budget_type', 'Daily')
            st.write(f"{budget_label} Budget: ${data.get('camp_budget_amount', 0):.2f}")

            st.markdown("**Ad Set**")
            st.write(f"Name: {data.get('adset_name')}")
            st.write(f"Countries: {data.get('countries')}")
            st.write(f"Ages: {data.get('age_min')}–{data.get('age_max')}")
            st.write(f"Optimization: {data.get('optimization_goal')}")

        with col2:
            st.markdown("**Creative**")
            st.write(f"Format: {data.get('media_type')}")
            if data.get("image_hash"):
                st.write(f"Image hash: `{data['image_hash']}`")
            if data.get("video_id"):
                st.write(f"Video ID: `{data['video_id']}`")
            st.write(f"Primary text: {data.get('primary_text', '')[:80]}…")
            st.write(f"Headline: {data.get('headline', '—')}")
            st.write(f"CTA: {data.get('call_to_action')}")
            st.write(f"URL: {data.get('destination_url')}")

        st.divider()
        st.info("All items will be created as **PAUSED**. Go to Meta Ads Manager to review and activate.")

        col_back, col_pub = st.columns([1, 4])
        if col_back.button("← Back", key="back4"):
            st.session_state.wizard_step = 3
            st.rerun()

        if col_pub.button("🚀 Create Campaign", type="primary", key="publish"):
            data["ad_name"] = ad_name
            results = {}
            try:
                with st.spinner("Creating campaign…"):
                    camp_budget_cents = int(data["camp_budget_amount"] * 100)
                    daily_b = camp_budget_cents if data["camp_budget_type"] == "Daily" else None
                    life_b = camp_budget_cents if data["camp_budget_type"] == "Lifetime" else None
                    campaign = client().create_campaign(
                        name=data["camp_name"],
                        objective=data["objective"],
                        status="PAUSED",
                        daily_budget=daily_b,
                        lifetime_budget=life_b,
                        start_time=data.get("camp_start") or None,
                        stop_time=data.get("camp_stop") or None,
                    )
                    results["campaign"] = campaign
                    st.success(f"Campaign created: `{campaign['id']}`")

                with st.spinner("Creating ad set…"):
                    as_budget_cents = int(data["as_budget_amount"] * 100)
                    as_daily = as_budget_cents if data["as_budget_type"] == "Daily" else None
                    as_life = as_budget_cents if data["as_budget_type"] == "Lifetime" else None
                    ad_set = client().create_ad_set(
                        name=data["adset_name"],
                        campaign_id=campaign["id"],
                        daily_budget=as_daily,
                        lifetime_budget=as_life,
                        billing_event=data["billing_event"],
                        optimization_goal=data["optimization_goal"],
                        targeting=data["targeting"],
                        status="PAUSED",
                    )
                    results["ad_set"] = ad_set
                    st.success(f"Ad set created: `{ad_set['id']}`")

                with st.spinner("Creating creative…"):
                    if data["media_type"] == "Image Ad":
                        creative = client().create_image_ad_creative(
                            name=data["creative_name"],
                            image_hash=data["image_hash"],
                            page_id=data["page_id"],
                            message=data["primary_text"],
                            link=data["destination_url"],
                            headline=data.get("headline") or None,
                            description=data.get("description") or None,
                            call_to_action_type=data["call_to_action"],
                        )
                    else:
                        creative = client().create_video_ad_creative(
                            name=data["creative_name"],
                            video_id=data["video_id"],
                            page_id=data["page_id"],
                            message=data["primary_text"],
                            link=data["destination_url"],
                            title=data.get("headline") or None,
                            description=data.get("description") or None,
                            call_to_action_type=data["call_to_action"],
                        )
                    results["creative"] = creative
                    st.success(f"Creative created: `{creative['id']}`")

                with st.spinner("Creating ad…"):
                    ad = client().create_ad(
                        name=data["ad_name"],
                        ad_set_id=ad_set["id"],
                        creative_id=creative["id"],
                        status="PAUSED",
                    )
                    results["ad"] = ad
                    st.success(f"Ad created: `{ad['id']}`")

                st.balloons()
                st.markdown("### Campaign created successfully!")
                st.markdown(
                    "Go to [Meta Ads Manager](https://adsmanager.facebook.com) to review and activate your campaign."
                )

                with st.expander("All created IDs"):
                    st.json(results)

                if st.button("Start a new campaign"):
                    st.session_state.wizard_step = 1
                    st.session_state.wizard_data = {}
                    st.rerun()

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.caption("Any items created before the error still exist in your account.")
