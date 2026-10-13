"""Small, synchronous Gemini client used by MindMate's Qt chat worker.

Only the messages explicitly sent in chat go to Gemini. This module has no
access to journal files and never persists chat history or API credentials.
Keep one ChatService for the current session, and call respond from a worker
thread so the desktop interface remains responsive.
"""

from copy import deepcopy
from dataclasses import dataclass, field
import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL = "gemini-3.5-flash-lite"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
MAX_INPUT_CHARACTERS = 12_000
MAX_HISTORY_TURNS = 10
MAX_HISTORY_CHARACTERS = 40_000
MAX_RESPONSE_BYTES = 2_000_000

SYSTEM_PROMPT = (
    "You are MindMate, a kind, supportive wellness companion. Listen with empathy "
    "and offer practical, gentle suggestions for everyday feelings. You are not a "
    "therapist or medical professional: do not diagnose, prescribe, or promise a "
    "cure. When professional care is appropriate, encourage the user to reach out "
    "to a qualified professional. If someone may be in immediate danger, encourage "
    "them to contact local emergency services and a trusted person nearby; never "
    "invent hotline phone numbers. Keep replies concise, usually under 180 words. "
    "Use plain text, short paragraphs, and numbered steps when useful. Avoid "
    "Markdown formatting, asterisks, and HTML. Ask at most one helpful question."
)


@dataclass(frozen=True)
class ChatConfig:
    api_key: str = field(default="", repr=False)
    model: str = DEFAULT_MODEL
    timeout: int = 30


class ChatError(Exception):
    """An error whose message is safe to show directly in the interface."""


class ChatService:
    """A chat session with bounded history; use one request at a time."""

    def __init__(self, config: ChatConfig):
        self.config = config
        self._history = []

    @property
    def history(self):
        """Return an independent copy of this session's successful exchanges."""
        return deepcopy(self._history)

    def reset(self):
        """Forget the current session (call when no request is running)."""
        self._history.clear()

    def respond(self, user_input: str) -> str:
        """Return a reply, keeping history only when the entire request succeeds."""
        api_key, model, timeout = self._validated_config()
        if not isinstance(user_input, str) or not user_input.strip():
            raise ChatError("Write a message before sending it.")
        text = user_input.strip()
        if len(text) > MAX_INPUT_CHARACTERS:
            raise ChatError("That message is too long. Please send a shorter message.")

        user_message = {"role": "user", "parts": [{"text": text}]}
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": self._history + [user_message],
            "generationConfig": {"maxOutputTokens": 2048},
        }
        request = Request(
            API_BASE + model + ":generateContent",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                raw_response = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            # Never expose the URL, raw provider body, or credentials in the UI.
            try:
                error_body = error.read(32_768)
            except (OSError, ValueError):
                error_body = b""
            finally:
                error.close()
            raise ChatError(self._http_error_message(error.code, error_body)) from None
        except (TimeoutError, socket.timeout):
            raise ChatError("The request timed out. Please try again.") from None
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise ChatError("The request timed out. Please try again.") from None
            raise ChatError("Could not connect to Gemini. Check your internet connection and try again.") from None
        except OSError:
            raise ChatError("The connection was interrupted. Please try again.") from None

        if len(raw_response) > MAX_RESPONSE_BYTES:
            raise ChatError("Gemini returned an unexpectedly large response. Please try again.")
        try:
            data = json.loads(raw_response.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ChatError("Gemini returned an unreadable response. Please try again.") from None

        reply = self._reply_text(data)
        self._history.extend([user_message, {"role": "model", "parts": [{"text": reply}]}])
        self._trim_history()
        return reply

    def _validated_config(self):
        api_key = self.config.api_key.strip()
        if not api_key:
            raise ChatError("Add your Gemini API key in Chat settings to start chatting.")
        if any(ord(char) < 33 or ord(char) > 126 for char in api_key):
            raise ChatError("The API key is not valid. Copy it again into Chat settings.")
        model = self.config.model.strip()
        if model.startswith("models/"):
            model = model[len("models/"):]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", model):
            raise ChatError("Enter a valid Gemini model name in Chat settings.")
        if not isinstance(self.config.timeout, int) or not 1 <= self.config.timeout <= 120:
            raise ChatError("The chat timeout must be between 1 and 120 seconds.")
        return api_key, model, self.config.timeout

    @staticmethod
    def _http_error_message(code, body):
        if code == 400:
            # Google's invalid keys often arrive as HTTP 400 rather than 401.
            try:
                details = json.loads(body).get("error", {}).get("details", [])
                key_error = any(
                    isinstance(detail, dict)
                    and detail.get("reason") in {"API_KEY_INVALID", "API_KEY_EXPIRED", "API_KEY_NOT_FOUND"}
                    for detail in details
                )
            except (ValueError, AttributeError, TypeError):
                key_error = False
            if key_error:
                return "Gemini rejected the API key. Check it in Chat settings."
            return "Gemini could not accept the request. Check your API key and model in Chat settings."
        if code in (401, 403):
            return "Gemini denied access. Check your API key, model access, and account availability."
        if code == 404:
            return "This Gemini model is unavailable. Choose a supported model in Chat settings."
        if code == 429:
            return "Gemini's rate limit or quota was reached. Wait and try again, or check your Google AI Studio quota."
        if code in (408, 504):
            return "The request timed out. Please try again."
        if code >= 500:
            return "Gemini is temporarily unavailable. Please try again later."
        return "Gemini could not complete the request. Please try again."

    @staticmethod
    def _reply_text(data):
        if not isinstance(data, dict):
            raise ChatError("Gemini returned an unreadable response. Please try again.")
        feedback = data.get("promptFeedback", {})
        if isinstance(feedback, dict) and feedback.get("blockReason") not in (None, "", "BLOCK_REASON_UNSPECIFIED"):
            raise ChatError("Gemini could not respond to that message. Try rephrasing it.")
        candidates = data.get("candidates", [])
        if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
            raise ChatError("Gemini returned no reply. Please try again.")
        candidate = candidates[0]
        if candidate.get("finishReason") in {
            "SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY"
        }:
            raise ChatError("Gemini could not respond to that message. Try rephrasing it.")
        content = candidate.get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []
        if not isinstance(parts, list):
            parts = []
        reply = "".join(
            part["text"] for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str) and not part.get("thought")
        ).strip()
        if not reply:
            raise ChatError("Gemini returned no reply. Please try again.")
        return reply

    def _trim_history(self):
        # Remove complete user/model pairs so roles remain correctly ordered.
        while len(self._history) > MAX_HISTORY_TURNS * 2 or (
            len(self._history) > 2
            and sum(len(message["parts"][0]["text"]) for message in self._history) > MAX_HISTORY_CHARACTERS
        ):
            del self._history[:2]
