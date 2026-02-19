"""
Email service for tender sharing.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any, Dict, List

import httpx

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.provider = (settings.EMAIL_PROVIDER or "smtp").lower()

    async def send_tender_share(
        self,
        recipients: List[str],
        tender: Dict[str, Any],
        match_percent: int,
        note: str | None = None,
    ) -> Dict[str, Any]:
        if not recipients:
            raise ValueError("At least one recipient is required")

        subject = f"Tender Shared: {tender.get('title') or 'Tender'} (Match {match_percent}%)"
        body = self._build_body(tender=tender, match_percent=match_percent, note=note)

        if self.provider == "sendgrid" and settings.SENDGRID_API_KEY:
            return await self._send_with_sendgrid(recipients, subject, body)

        if self.provider == "smtp" and settings.SMTP_HOST and settings.SMTP_USER:
            return await self._send_with_smtp(recipients, subject, body)

        logger.info("email.share_mocked", recipients=recipients, subject=subject)
        return {"sent": True, "provider": "mock", "count": len(recipients)}

    async def _send_with_smtp(self, recipients: List[str], subject: str, body: str) -> Dict[str, Any]:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
            return {"sent": True, "provider": "smtp", "count": len(recipients)}
        except Exception as exc:
            logger.info("email.smtp_failed", error=str(exc))
            return {"sent": False, "provider": "smtp", "count": 0, "error": str(exc)}

    async def _send_with_sendgrid(self, recipients: List[str], subject: str, body: str) -> Dict[str, Any]:
        payload = {
            "personalizations": [{"to": [{"email": email} for email in recipients]}],
            "from": {"email": settings.EMAIL_FROM.split("<")[-1].replace(">", "").strip() or "no-reply@example.com"},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
                )
            if response.status_code >= 300:
                return {"sent": False, "provider": "sendgrid", "count": 0, "error": response.text}
            return {"sent": True, "provider": "sendgrid", "count": len(recipients)}
        except Exception as exc:
            return {"sent": False, "provider": "sendgrid", "count": 0, "error": str(exc)}

    def _build_body(self, tender: Dict[str, Any], match_percent: int, note: str | None) -> str:
        lines = [
            f"Tender Title: {tender.get('title') or 'N/A'}",
            f"Department: {tender.get('department') or 'N/A'}",
            f"Location: {tender.get('location') or 'N/A'}",
            f"Bid ID: {tender.get('bid_id') or 'N/A'}",
            f"Published Date: {tender.get('published_date') or 'N/A'}",
            f"Closing Date: {tender.get('close_date') or 'N/A'}",
            f"Portal Link: {tender.get('gem_url') or 'N/A'}",
            f"Match Percentage: {match_percent}%",
            "",
            "Summary:",
            tender.get("summary") or "N/A",
            "",
            f"Open in app: {settings.FRONTEND_BASE_URL}/tenders/{tender.get('id')}",
        ]
        if note:
            lines.extend(["", "Note:", note])
        return "\n".join(lines)