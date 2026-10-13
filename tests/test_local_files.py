"""Local resource and persistence checks using isolated, disposable data."""

from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import app_paths


class LocalFilesTests(unittest.TestCase):
    def setUp(self):
        # Keeping the disposable directory beside the tests also supports
        # restricted environments whose system temp directory is unavailable.
        self.temporary = tempfile.TemporaryDirectory(
            prefix="mindmate-test-", dir=Path(__file__).resolve().parent
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.local_data = self.root / "local data"
        self.environment = mock.patch.dict(
            os.environ, {"MINDMATE_DATA_DIR": str(self.local_data)}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_assets_resolve_from_an_unrelated_working_directory(self):
        expected = app_paths.resource_root() / "Assets" / "Frames" / "Home Screen.png"
        unrelated = self.root / "unrelated working directory"
        unrelated.mkdir()
        original_directory = Path.cwd()
        try:
            os.chdir(unrelated)
            resolved = Path(app_paths.asset_path("Frames/Home Screen.png"))
            self.assertEqual(resolved, expected)
            self.assertTrue(resolved.is_file(), "The original home-screen asset is missing.")
        finally:
            os.chdir(original_directory)

    def test_stylesheet_quotes_asset_paths_with_spaces(self):
        bundle = self.root / "bundled resources"
        stylesheet = (
            "QFrame { border-image: url(Assets/Frames/Home Screen.png); }\n"
            "QPushButton:hover { border-image: url('Assets/Buttons/Back Button/Hover.png'); }\n"
            'QFrame#other { background-image: url("outside.png"); }'
        )
        with mock.patch.object(app_paths, "resource_root", return_value=bundle):
            resolved = app_paths.asset_stylesheet(stylesheet)
        self.assertIn(
            f'url("{(bundle / "Assets" / "Frames" / "Home Screen.png").as_posix()}")',
            resolved,
        )
        self.assertIn(
            f'url("{(bundle / "Assets" / "Buttons" / "Back Button" / "Hover.png").as_posix()}")',
            resolved,
        )
        self.assertIn('url("outside.png")', resolved)

    def test_empty_journal_is_rejected_without_creating_data(self):
        for text in ("", "   ", "\n\t\r\n"):
            with self.subTest(text=repr(text)):
                with self.assertRaises(ValueError):
                    app_paths.save_journal(text)
        self.assertFalse(self.local_data.exists())

    def test_journals_create_directory_and_preserve_existing_entries(self):
        now = datetime(2026, 10, 13, 9, 15)
        first = app_paths.save_journal("  An early thought — नमस्ते  ", now=now)
        self.assertEqual(first.parent, self.local_data / "Your Journals")
        self.assertEqual(first.name, "journal1.txt")
        first_text = first.read_text(encoding="utf-8")
        self.assertEqual(
            first_text,
            f'{now.strftime("%A, %d %B %Y (%I:%M %p)")}\n\nAn early thought — नमस्ते\n',
        )

        second = app_paths.save_journal("Another thought", now=now)
        third = app_paths.save_journal("A third thought", now=now)
        self.assertEqual(second.name, "journal2.txt")
        self.assertEqual(third.name, "journal3.txt")
        self.assertEqual(first.read_text(encoding="utf-8"), first_text)
        self.assertIn("Another thought", second.read_text(encoding="utf-8"))
        self.assertEqual(len(list(first.parent.glob("journal*.txt"))), 3)

    def test_failed_journal_write_propagates_and_removes_partial_entry(self):
        original_open = Path.open

        class FailingWriter:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, exception_type, exception, traceback):
                self.stream.close()

            def write(self, text):
                self.stream.write(text[:5])
                self.stream.flush()
                raise OSError("Simulated full disk")

        def failing_open(path, *args, **kwargs):
            return FailingWriter(original_open(path, *args, **kwargs))

        with mock.patch.object(Path, "open", new=failing_open):
            with self.assertRaises(OSError):
                app_paths.save_journal("This write cannot complete.")
        self.assertEqual(list((self.local_data / "Your Journals").iterdir()), [])

    def test_missing_settings_are_empty(self):
        self.assertEqual(app_paths.load_settings(), {})
        self.assertFalse(self.local_data.exists())

    def test_settings_json_roundtrip_is_utf8_and_private_values_are_not_reported(self):
        # Fabricated fixtures only; never consult the user's settings file.
        fixture = {"api_key": "not-a-real-key", "model": "example-model"}
        app_paths.save_settings(fixture)
        settings = app_paths.load_settings()
        self.assertEqual(set(settings), {"api_key", "model"})
        self.assertTrue(settings["api_key"] == fixture["api_key"])
        self.assertTrue(settings["model"] == fixture["model"])
        self.assertEqual(list(self.local_data.glob("settings-*.tmp")), [])

    def test_malformed_settings_raise_errors_without_disclosing_contents(self):
        self.local_data.mkdir()
        settings_file = self.local_data / "settings.json"
        for content, error in (("{broken", json.JSONDecodeError), ("[]", ValueError)):
            settings_file.write_text(content, encoding="utf-8")
            with self.subTest(format="json" if error is json.JSONDecodeError else "structure"):
                with self.assertRaises(error):
                    app_paths.load_settings()

    def test_settings_ignore_unknown_fields_and_non_string_values(self):
        self.local_data.mkdir()
        payload = {"api_key": 123, "model": "example-model", "unknown": "ignored"}
        (self.local_data / "settings.json").write_text(json.dumps(payload), encoding="utf-8")
        settings = app_paths.load_settings()
        self.assertEqual(set(settings), {"model"})
        self.assertTrue(settings["model"] == payload["model"])

    def test_failed_settings_replace_preserves_previous_file_and_cleans_temp(self):
        app_paths.save_settings({"model": "previous-model"})
        settings_file = self.local_data / "settings.json"
        previous_content = settings_file.read_bytes()
        with mock.patch.object(Path, "replace", side_effect=PermissionError("Simulated lock")):
            with self.assertRaises(PermissionError):
                app_paths.save_settings({"model": "replacement-model"})
        self.assertTrue(settings_file.read_bytes() == previous_content)
        self.assertEqual(list(self.local_data.glob("settings-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
