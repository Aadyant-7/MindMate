"""Chat behavior checks using fake provider responses; no network or credentials."""

import io
import json
import socket
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from ChatBot_API import ChatConfig, ChatError, ChatService, MAX_HISTORY_TURNS


def provider_reply(text="Take one small step at a time."):
    return io.BytesIO(json.dumps({
        "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]
    }).encode("utf-8"))


class ChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ChatService(ChatConfig(api_key="test-placeholder"))

    def test_missing_key_never_sends_request(self):
        with patch("ChatBot_API.urlopen") as request:
            with self.assertRaisesRegex(ChatError, "API key"):
                ChatService(ChatConfig()).respond("Hello")
            request.assert_not_called()

    def test_followup_receives_successful_conversation(self):
        with patch("ChatBot_API.urlopen", side_effect=[provider_reply("Hello!"), provider_reply("Yes, I remember.")]) as request:
            self.service.respond("I feel nervous about exams.")
            self.service.respond("Do you remember what I said?")
        second_request = request.call_args_list[1].args[0]
        messages = json.loads(second_request.data)["contents"]
        self.assertEqual([message["role"] for message in messages], ["user", "model", "user"])
        self.assertEqual(messages[0]["parts"][0]["text"], "I feel nervous about exams.")
        self.assertNotIn("test-placeholder", second_request.full_url)
        self.assertNotIn("test-placeholder", second_request.data.decode())

    def test_failed_request_preserves_existing_history(self):
        with patch("ChatBot_API.urlopen", return_value=provider_reply()):
            self.service.respond("Hello")
        previous = self.service.history
        error = HTTPError("https://example.invalid/", 429, "raw private body", {}, io.BytesIO(b"secret-server-body"))
        with patch("ChatBot_API.urlopen", side_effect=error):
            with self.assertRaisesRegex(ChatError, "quota") as result:
                self.service.respond("Please help")
        self.assertNotIn("secret-server-body", str(result.exception))
        self.assertEqual(previous, self.service.history)

    def test_error_categories_are_useful_and_sanitized(self):
        for status, expected in [(401, "access"), (403, "access"), (404, "model"), (503, "temporarily"), (504, "timed out")]:
            with self.subTest(status=status):
                error = HTTPError("https://example.invalid/?key=private-value", status, "private-value", {}, io.BytesIO(b"private-value"))
                with patch("ChatBot_API.urlopen", side_effect=error):
                    with self.assertRaisesRegex(ChatError, expected) as result:
                        self.service.respond("Hello")
                self.assertNotIn("private-value", str(result.exception))

    def test_invalid_key_reported_even_when_provider_returns_400(self):
        body = json.dumps({"error": {"message": "private-value", "details": [{"reason": "API_KEY_INVALID"}]}}).encode()
        error = HTTPError("https://example.invalid/", 400, "private-value", {}, io.BytesIO(body))
        with patch("ChatBot_API.urlopen", side_effect=error):
            with self.assertRaisesRegex(ChatError, "rejected the API key") as result:
                self.service.respond("Hello")
        self.assertNotIn("private-value", str(result.exception))

    def test_network_and_timeout_errors_have_distinct_messages(self):
        for failure, expected in [
            (socket.timeout(), "timed out"),
            (URLError(socket.timeout()), "timed out"),
            (URLError("private network details"), "internet connection"),
        ]:
            with self.subTest(expected=expected):
                with patch("ChatBot_API.urlopen", side_effect=failure):
                    with self.assertRaisesRegex(ChatError, expected) as result:
                        self.service.respond("Hello")
                self.assertNotIn("private network details", str(result.exception))
                self.assertEqual([], self.service.history)

    def test_empty_blocked_and_malformed_responses_do_not_enter_history(self):
        bodies = [
            {"candidates": []},
            {"promptFeedback": {"blockReason": "SAFETY"}},
            {"candidates": [{"finishReason": "SAFETY", "content": {"parts": [{"text": "blocked"}]}}]},
            {"candidates": [{"content": {"parts": [{"text": "private thoughts", "thought": True}]}}]},
            {"candidates": None},
            [],
        ]
        for body in bodies:
            with self.subTest(body=body):
                with patch("ChatBot_API.urlopen", return_value=io.BytesIO(json.dumps(body).encode())):
                    with self.assertRaises(ChatError):
                        self.service.respond("Hello")
                self.assertEqual([], self.service.history)
        with patch("ChatBot_API.urlopen", return_value=io.BytesIO(b"invalid json")):
            with self.assertRaisesRegex(ChatError, "unreadable"):
                self.service.respond("Hello")

    def test_history_is_bounded_independent_and_can_be_reset(self):
        with patch("ChatBot_API.urlopen", side_effect=lambda *args, **kwargs: provider_reply("A short reply")):
            for index in range(MAX_HISTORY_TURNS + 3):
                self.service.respond("Message " + str(index))
        self.assertEqual(MAX_HISTORY_TURNS * 2, len(self.service.history))
        self.assertEqual("Message 3", self.service.history[0]["parts"][0]["text"])
        copy = self.service.history
        copy[0]["parts"][0]["text"] = "Changed externally"
        self.assertNotEqual(copy, self.service.history)
        self.service.reset()
        self.assertEqual([], self.service.history)

    def test_invalid_configuration_cannot_change_request_destination(self):
        for config in [
            ChatConfig(api_key="test-placeholder", model="../../external?key=value"),
            ChatConfig(api_key="key\nInjected: header"),
            ChatConfig(api_key="test-placeholder", timeout=0),
        ]:
            with self.subTest(config=config):
                with patch("ChatBot_API.urlopen") as request:
                    with self.assertRaises(ChatError):
                        ChatService(config).respond("Hello")
                    request.assert_not_called()
        self.assertNotIn("test-placeholder", repr(self.service.config))


if __name__ == "__main__":
    unittest.main()
