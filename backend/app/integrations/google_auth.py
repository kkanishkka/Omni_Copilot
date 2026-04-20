import os

# MUST be set before any oauthlib imports to allow http:// for local dev
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config.settings import settings

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
    }
}


def _make_flow(state: str = None) -> Flow:
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        state=state,
    )
    return flow


def get_google_auth_url(user_id: str) -> str:
    flow = _make_flow(state=user_id)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )
    return auth_url


def _normalize_callback_url(url: str) -> str:
    """
    Normalize the callback URL for oauthlib token exchange.

    Problems we solve here:
    1. When uvicorn binds to 0.0.0.0, request.url shows 0.0.0.0 as host —
       Google's token endpoint rejects this. Replace with 127.0.0.1.
    2. Behind a proxy or in some environments, the scheme may be reported
       as https even for localhost — oauthlib rejects https://localhost
       unless OAUTHLIB_INSECURE_TRANSPORT is set (we set it, but normalise
       to http anyway to be safe).
    3. The normalized URL must exactly match a registered redirect URI in
       Google Cloud Console. We reconstruct it from settings.GOOGLE_REDIRECT_URI
       (which IS registered) plus only the query params Google sent back.
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    query = parsed.query  # preserve ?code=...&state=...&scope=...

    # Parse the registered redirect URI from settings — this is what Google knows
    registered = urllib.parse.urlparse(settings.GOOGLE_REDIRECT_URI)

    # Rebuild using the registered scheme+host+path, but keep Google's query params
    normalized = urllib.parse.urlunparse((
        registered.scheme,   # http  (as registered in GCP)
        registered.netloc,   # localhost:8000  (as registered in GCP)
        registered.path,     # /api/auth/google/callback
        "",
        query,               # code=...&state=...&iss=...&scope=...
        "",
    ))
    return normalized


def handle_google_callback(code: str, state: str, request_url: str = None):
    """
    Exchange the OAuth2 authorization code for tokens.

    Uses authorization_response= (full URL) instead of code= to avoid the
    oauthlib MismatchingStateError that causes 307 redirect loops.
    """
    flow = _make_flow(state=state)

    if request_url:
        # Normalize to match registered redirect URI exactly
        auth_response = _normalize_callback_url(request_url)
    else:
        # Fallback: reconstruct from code + state using registered redirect URI
        import urllib.parse
        params: dict = {"code": code}
        if state:
            params["state"] = state
        auth_response = f"{settings.GOOGLE_REDIRECT_URI}?{urllib.parse.urlencode(params)}"

    flow.fetch_token(authorization_response=auth_response)

    credentials = flow.credentials

    service = build("oauth2", "v2", credentials=credentials)
    profile = service.userinfo().get().execute()

    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
    }

    return profile, token_data


def build_credentials(token_data: dict) -> Credentials:
    return Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id", settings.GOOGLE_CLIENT_ID),
        client_secret=token_data.get("client_secret", settings.GOOGLE_CLIENT_SECRET),
        scopes=token_data.get("scopes", SCOPES),
    )
