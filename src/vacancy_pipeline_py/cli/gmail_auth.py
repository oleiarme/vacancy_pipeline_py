from __future__ import annotations

from vacancy_pipeline_py import paths

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def resolve_auth_paths():
    credentials_path = paths.gmail_credentials_path()
    token_path = paths.gmail_token_path()

    legacy_dir = paths.repo_root() / "auth"
    legacy_credentials_path = legacy_dir / "credentials.json"
    legacy_token_path = legacy_dir / "gmail_token.json"

    if not credentials_path.exists() and legacy_credentials_path.exists():
        credentials_path = legacy_credentials_path
    if not token_path.exists() and legacy_token_path.exists():
        token_path = legacy_token_path

    return credentials_path, token_path


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
    creds_file, token_file = resolve_auth_paths()

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
