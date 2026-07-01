"""
Firebase Admin initialization and token verification helpers.

DISABLED — the app migrated from Firebase auth to the central auth gateway
(see app/utils/jwt_auth.py and app/api/dependencies.py). This module is kept
(commented out) for reference and easy rollback; it has no live callers.
"""

from __future__ import annotations

# import os
# from typing import Any, Dict
#
# import firebase_admin
# from firebase_admin import auth as firebase_auth
# from firebase_admin import credentials
#
# from app.config import settings
#
# _app = None
#
#
# def _init_firebase_app():
#     path = (settings.FIREBASE_SERVICE_ACCOUNT_PATH or "").strip()
#     if not path:
#         raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_PATH is not set")
#     if not os.path.isfile(path):
#         raise RuntimeError(f"Firebase service account file not found: {path}")
#
#     cred = credentials.Certificate(path)
#     return firebase_admin.initialize_app(cred)
#
#
# def get_firebase_app():
#     global _app
#     if _app:
#         return _app
#     try:
#         _app = firebase_admin.get_app()
#     except ValueError:
#         _app = _init_firebase_app()
#     return _app
#
#
# def verify_firebase_token(token: str) -> Dict[str, Any]:
#     app = get_firebase_app()
#     return firebase_auth.verify_id_token(token, app=app)
