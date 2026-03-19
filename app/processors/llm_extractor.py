"""
LLM-based metadata extraction using a configurable provider.
Supports full document processing with intelligent chunking for large documents.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


TENDER_PROMPT = """
You are extracting structured metadata from a government tender document.
Return ONLY valid JSON with the following keys:
- title
- department
- sector
- domains (array of strings)
- required_certifications (array of strings)
- required_technologies (array of strings)
- required_experience_years (number or null)
- estimated_value (string or null)
- eligibility_criteria (object with keys: min_turnover, min_experience_years, required_registrations)
- location
- delivery_period
- emd_amount
- summary

Text:
{content}
"""


COMPANY_PROMPT = """
You are extracting structured metadata from a company profile document.
Return ONLY valid JSON with the following keys:
- company_name
- industries (array of strings)
- capabilities (array of strings)
- certifications (array of strings)
- technologies (array of strings)
- domains (array of strings)
- past_clients (array of strings)
- government_experience (boolean or null)
- years_in_business (number or null)
- employee_count (string or null)
- annual_turnover (string or null)
- locations (array of strings)
- registrations (array of strings)
- summary

Text:
{content}
"""


CHUNK_MERGE_PROMPT = """
You are merging metadata extracted from multiple parts of a document.
Combine the following metadata objects into a single comprehensive object.
For arrays: combine and deduplicate items.
For strings: pick the most detailed/complete value.
For numbers: pick the most specific value.
For booleans: if any is true, result is true.
Return ONLY valid JSON.

Metadata objects to merge:
{metadata_list}
"""


class LLMExtractor:
    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER.lower()
        self._model = None
        self._client: Optional[httpx.Client] = None

        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not configured")
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        elif self.provider in {"ollama", "local"}:
            self._client = httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS)
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")

    def _get_max_chars(self) -> int:
        """Get maximum characters based on provider."""
        if self.provider == "gemini":
            return settings.LLM_GEMINI_MAX_CHARS
        return settings.LLM_INPUT_MAX_CHARS

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks for processing."""
        max_chars = self._get_max_chars()

        # If text fits within limit, return as single chunk
        if len(text) <= max_chars:
            return [text]

        chunk_size = settings.LLM_CHUNK_SIZE
        overlap = settings.LLM_CHUNK_OVERLAP
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at a sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start + chunk_size - overlap, end)
                if para_break > start:
                    end = para_break
                else:
                    # Look for sentence break
                    sentence_break = text.rfind('. ', start + chunk_size - overlap, end)
                    if sentence_break > start:
                        end = sentence_break + 1

            chunks.append(text[start:end].strip())
            start = end - overlap  # Overlap for context continuity

            # Prevent infinite loop
            if start >= len(text) - overlap:
                break

        logger.info("llm.text_chunked", total_length=len(text), num_chunks=len(chunks))
        return chunks

    def _merge_metadata(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple metadata dicts into one comprehensive result."""
        if not metadata_list:
            return {}
        if len(metadata_list) == 1:
            return metadata_list[0]

        # Try LLM-based merging for better results
        try:
            metadata_json = json.dumps(metadata_list, indent=2)
            prompt = CHUNK_MERGE_PROMPT.format(metadata_list=metadata_json)
            response_text = self._generate(prompt)
            merged = self._parse_json(response_text)
            if merged:
                return merged
        except Exception as exc:
            logger.info("llm.merge_failed", error=str(exc))

        # Fallback: manual merging
        return self._manual_merge(metadata_list)

    def _manual_merge(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Manually merge metadata when LLM merging fails."""
        merged: Dict[str, Any] = {}

        for metadata in metadata_list:
            for key, value in metadata.items():
                if value is None:
                    continue

                existing = merged.get(key)

                if existing is None:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(existing, list):
                    # Merge and deduplicate arrays
                    combined = existing + [v for v in value if v not in existing]
                    merged[key] = combined
                elif isinstance(value, str) and isinstance(existing, str):
                    # Keep longer/more detailed string
                    if len(value) > len(existing):
                        merged[key] = value
                elif isinstance(value, bool):
                    # If any is True, result is True
                    merged[key] = existing or value
                elif isinstance(value, (int, float)) and existing is None:
                    merged[key] = value

        return merged

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def extract_tender(self, text: str) -> Dict[str, Any]:
        """Extract tender metadata from full document text."""
        max_chars = self._get_max_chars()

        # If text fits within limit, process directly
        if len(text) <= max_chars:
            prompt = TENDER_PROMPT.format(content=text)
            response_text = self._generate(prompt)
            return self._parse_json(response_text)

        # For very large documents, use chunking
        chunks = self._split_into_chunks(text)
        metadata_list = []

        for i, chunk in enumerate(chunks):
            logger.info("llm.processing_chunk", chunk_num=i+1, total_chunks=len(chunks))
            prompt = TENDER_PROMPT.format(content=chunk)
            response_text = self._generate(prompt)
            metadata = self._parse_json(response_text)
            if metadata:
                metadata_list.append(metadata)

        return self._merge_metadata(metadata_list)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def extract_company(self, text: str) -> Dict[str, Any]:
        """Extract company metadata from full document text."""
        max_chars = self._get_max_chars()

        # If text fits within limit, process directly
        if len(text) <= max_chars:
            prompt = COMPANY_PROMPT.format(content=text)
            response_text = self._generate(prompt)
            return self._parse_json(response_text)

        # For very large documents, use chunking
        chunks = self._split_into_chunks(text)
        metadata_list = []

        for i, chunk in enumerate(chunks):
            logger.info("llm.processing_chunk", chunk_num=i+1, total_chunks=len(chunks))
            prompt = COMPANY_PROMPT.format(content=chunk)
            response_text = self._generate(prompt)
            metadata = self._parse_json(response_text)
            if metadata:
                metadata_list.append(metadata)

        return self._merge_metadata(metadata_list)

    def _generate(self, prompt: str) -> str:
        try:
            if self.provider == "gemini":
                response = self._model.generate_content(prompt)
                return response.text

            payload = {"model": settings.LLM_MODEL, "prompt": prompt, "stream": False}
            url = settings.LLM_BASE_URL.rstrip("/") + "/api/generate"
            headers = {"Content-Type": "text/plain"}
            response = self._client.post(url, content=json.dumps(payload), headers=headers)
            response.raise_for_status()
            try:
                data = response.json()
                return data.get("response") or data.get("text") or response.text
            except json.JSONDecodeError:
                return response.text
        except Exception as exc:
            raise RuntimeError(self._normalize_provider_error(exc)) from exc

    def _normalize_provider_error(self, exc: Exception) -> str:
        raw_message = str(exc).strip() or exc.__class__.__name__
        normalized = " ".join(raw_message.split())
        lowered = normalized.lower()

        if self.provider == "gemini":
            if (
                "api key expired" in lowered
                or "api_key_invalid" in lowered
                or "api key not valid" in lowered
                or ("api key" in lowered and "invalid" in lowered)
            ):
                return (
                    "Gemini API key is invalid or expired. Update GEMINI_API_KEY in the backend "
                    ".env file and restart the API server."
                )
            if "quota" in lowered or "rate limit" in lowered or "resource_exhausted" in lowered:
                return "Gemini quota or rate limit exceeded. Retry later or use a different LLM provider."
            if "model" in lowered and ("not found" in lowered or "unsupported" in lowered):
                return (
                    f"Gemini model '{settings.GEMINI_MODEL}' is unavailable. "
                    "Update GEMINI_MODEL in the backend .env file."
                )
            return f"Gemini request failed: {normalized}"

        if isinstance(exc, httpx.ConnectError):
            return f"Could not connect to Ollama at {settings.LLM_BASE_URL}. Start Ollama or update LLM_BASE_URL."
        if isinstance(exc, httpx.TimeoutException):
            return f"Ollama request timed out after {settings.LLM_TIMEOUT_SECONDS} seconds."
        if isinstance(exc, httpx.HTTPStatusError):
            response_text = " ".join((exc.response.text or "").split())
            if response_text:
                return f"Ollama returned HTTP {exc.response.status_code}: {response_text[:240]}"
            return f"Ollama returned HTTP {exc.response.status_code}."
        return normalized

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                logger.info("llm.json_parse_failed", raw=text[:300])
                return {}
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                logger.info("llm.json_parse_failed", raw=text[:300])
                return {}

    def generate_text(self, prompt: str) -> str:
        """Generate free-form text using the configured provider."""
        return self._generate(prompt)
