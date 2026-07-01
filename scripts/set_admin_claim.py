"""
Set Firebase custom claim `admin=true` for a user.

DISABLED — the app migrated from Firebase auth to the central auth gateway.
Admin access is now derived from the gateway JWT `role == "admin"` claim
(synced into MongoDB `users.is_admin`), so this Firebase custom-claim CLI is
obsolete. Kept (commented out) for reference / rollback.
"""

from __future__ import annotations

# import argparse
# import os
# import sys
#
# import firebase_admin
# from dotenv import load_dotenv
# from firebase_admin import auth, credentials
#
#
# def init_app(path: str):
#     if not path:
#         raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_PATH is not set")
#     if not os.path.isfile(path):
#         raise RuntimeError(f"Service account file not found: {path}")
#     cred = credentials.Certificate(path)
#     return firebase_admin.initialize_app(cred)
#
#
# def main() -> int:
#     parser = argparse.ArgumentParser(description="Set Firebase custom claim admin=true")
#     group = parser.add_mutually_exclusive_group(required=True)
#     group.add_argument("--email", help="User email to grant admin claim")
#     group.add_argument("--uid", help="User UID to grant admin claim")
#     args = parser.parse_args()
#
#     load_dotenv()
#     path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
#     init_app(path)
#
#     try:
#         if args.email:
#             user = auth.get_user_by_email(args.email)
#             uid = user.uid
#         else:
#             uid = args.uid
#         auth.set_custom_user_claims(uid, {"admin": True})
#     except Exception as exc:
#         print(f"Failed to set admin claim: {exc}")
#         return 1
#
#     print(f"Admin claim set for uid={uid}")
#     return 0
#
#
# if __name__ == "__main__":
#     raise SystemExit(main())
