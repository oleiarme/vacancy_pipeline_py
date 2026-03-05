from __future__ import annotations

from vacancy_pipeline_py import paths

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main() -> None:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Missing Gmail auth dependencies. Install with: pip install -e .[gmail]"
        ) from exc

    paths.ensure_dir(paths.auth_dir())
    creds_file = paths.gmail_credentials_path()
    token_file = paths.gmail_token_path()

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Token refreshed automatically")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
            print("Authorization complete")
        token_file.write_text(creds.to_json(), encoding="utf-8")

    print(f"Token saved: {token_file}")
    print(f"Valid: {creds.valid}, Expired: {creds.expired}")


if __name__ == "__main__":
    main()
