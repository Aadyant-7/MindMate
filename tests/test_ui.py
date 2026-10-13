"""Exercise the existing image UI without credentials or personal journal data."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import re
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from PyQt6 import QtCore, QtTest, QtWidgets
from ChatBot_API import ChatConfig, ChatError
from MindMate import MindMateWindow, Ui_MainWindow


class FakeChat:
    config = ChatConfig(api_key="test-key")

    def __init__(self, reply="A short supportive reply.", error=None, release=None):
        self.reply = reply
        self.error = error
        self.release = release
        self.received = []

    def respond(self, text):
        self.received.append(text)
        if self.release:
            self.release.wait(3)
        if self.error:
            raise ChatError(self.error)
        return self.reply


class OriginalUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.environment = patch.dict(os.environ, {
            "MINDMATE_DATA_DIR": self.temp.name, "GEMINI_API_KEY": "", "GEMINI_MODEL": "gemini-3.5-flash-lite"})
        self.environment.start()
        self.window = MindMateWindow()
        self.ui = Ui_MainWindow()
        self.window.ui = self.ui
        self.ui.setupUi(self.window)
        self.window.setFixedSize(800, 520)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.ui.chat_worker is not None:
            self.ui.chat_worker.wait(4000)
            self.app.processEvents()
        self.ui.writeJournal.clear()
        self.window.close()
        self.app.processEvents()
        self.window.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        self.environment.stop()
        self.temp.cleanup()

    def wait_for(self, condition):
        deadline = time.monotonic() + 4
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            QtTest.QTest.qWait(5)
        self.assertTrue(condition())

    def test_artwork_is_portable_and_all_home_buttons_work(self):
        for widget in self.window.findChildren(QtWidgets.QWidget):
            for match in re.finditer(r"url\((.*?)\)", widget.styleSheet()):
                self.assertTrue(Path(match.group(1).strip("\"'")).is_file(), widget.objectName())
        for button, frame, back in [(self.ui.chatbotButton, self.ui.chatbotFrame, self.ui.backButton),
                                   (self.ui.journalsButton, self.ui.journalsFrame, self.ui.backButton_2),
                                   (self.ui.moodSupportButton, self.ui.moodSupportFrame, self.ui.backButton_3)]:
            button.click()
            self.assertFalse(frame.isHidden())
            self.assertTrue(self.ui.homeScreenFrame.isHidden())
            back.click()
            self.assertFalse(self.ui.homeScreenFrame.isHidden())

    def test_survey_sequence_and_previous_navigation(self):
        self.ui.statsButton.click()
        for index in range(1, 7):
            self.assertFalse(getattr(self.ui, f"stats{index}Frame").isHidden())
            name = "forwardButton" if index == 1 else f"forwardButton_{index}"
            getattr(self.ui, name).click()
        self.assertFalse(self.ui.stats7Frame.isHidden())
        self.ui._navigate_survey(-1)
        self.assertFalse(self.ui.stats6Frame.isHidden())
        self.ui._navigate_survey(1)
        self.ui.backButton_4.click()
        self.assertFalse(self.ui.homeScreenFrame.isHidden())

    def test_all_moods_render_and_long_text_can_scroll(self):
        self.ui.moodSupportButton.click()
        for button in [self.ui.stressButton, self.ui.sadButton, self.ui.lonelyButton,
                       self.ui.angryButton, self.ui.anxietyButton]:
            button.click()
            self.assertGreater(len(self.ui.measures.toPlainText()), 100)
            self.assertEqual(self.ui.measures.verticalScrollBarPolicy(), QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ui.measures.setPlainText("A long suggestion.\n" * 100)
        self.app.processEvents()
        self.assertGreater(self.ui.measures.verticalScrollBar().maximum(), 0)

    def test_journal_empty_save_success_and_failure_preserve_text(self):
        self.ui.journalsButton.click()
        with patch.object(QtWidgets.QMessageBox, "information"):
            self.assertFalse(self.ui.save_journal_entry())
        self.assertFalse((Path(self.temp.name) / "Your Journals").exists())
        self.ui.writeJournal.setPlainText("An isolated test journal.")
        with patch.object(QtWidgets.QMessageBox, "exec", return_value=0):
            self.assertTrue(self.ui.save_journal_entry())
        files = list((Path(self.temp.name) / "Your Journals").glob("*.txt"))
        self.assertEqual(len(files), 1)
        self.assertIn("An isolated test journal.", files[0].read_text(encoding="utf-8"))
        self.assertEqual(self.ui.writeJournal.toPlainText(), "")
        self.ui.writeJournal.setPlainText("Keep this unsaved draft.")
        with patch("MindMate.save_journal", side_effect=OSError("disk full")), patch.object(QtWidgets.QMessageBox, "warning"):
            self.assertFalse(self.ui.save_journal_entry())
        self.assertEqual(self.ui.writeJournal.toPlainText(), "Keep this unsaved draft.")

    def test_chat_runs_in_background_and_escapes_text(self):
        release = threading.Event()
        service = FakeChat(reply="<b>Literal reply</b>\nSecond line", release=release)
        self.ui.chat_service = service
        self.ui.chatbotButton.click()
        self.ui.lineEdit.setText("<b>Literal message</b>")
        QtTest.QTest.keyClick(self.ui.lineEdit, QtCore.Qt.Key.Key_Return)
        self.assertIsNotNone(self.ui.chat_worker)
        self.assertFalse(self.ui.sendButton.isEnabled())
        self.assertIn("<b>Literal message</b>", self.ui.chatbox.toPlainText())
        self.ui.backButton.click()
        self.assertFalse(self.ui.homeScreenFrame.isHidden())
        release.set()
        self.wait_for(lambda: self.ui.chat_worker is None)
        self.assertIn("<b>Literal reply</b>", self.ui.chatbox.toPlainText())
        self.assertTrue(self.ui.sendButton.isEnabled())
        self.assertEqual(service.received, ["<b>Literal message</b>"])

    def test_chat_failure_restores_input_and_can_retry(self):
        self.ui.chat_service = FakeChat(error="A safe connection error.")
        self.ui.chatbotButton.click()
        self.ui.lineEdit.setText("Please keep my message")
        self.ui.sendButton.click()
        self.wait_for(lambda: self.ui.chat_worker is None)
        self.assertEqual(self.ui.lineEdit.text(), "Please keep my message")
        self.assertIn("safe connection error", self.ui.chatbox.toPlainText())
        self.ui.chat_service = FakeChat()
        self.ui.sendButton.click()
        self.wait_for(lambda: self.ui.chat_worker is None)
        self.assertEqual(self.ui.chatbox.toPlainText().count("Please keep my message"), 1)

    def test_missing_key_cancel_keeps_message(self):
        self.ui.lineEdit.setText("Message before setup")
        with patch.object(self.ui, "configure_chat", return_value=False):
            self.ui.handleSendButton()
        self.assertEqual(self.ui.lineEdit.text(), "Message before setup")
        self.assertIsNone(self.ui.chat_worker)

    def test_settings_dialog_saves_without_editing_source(self):
        def save_dialog():
            dialog = self.app.activeModalWidget()
            edits = dialog.findChildren(QtWidgets.QLineEdit)
            edits[0].setText("test-key")
            buttons = dialog.findChild(QtWidgets.QDialogButtonBox)
            buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Save).click()

        QtCore.QTimer.singleShot(0, save_dialog)
        self.assertTrue(self.ui.configure_chat())
        self.assertTrue((Path(self.temp.name) / "settings.json").is_file())
        self.assertEqual(self.ui.chat_service.config.api_key, "test-key")

    def test_unsaved_journal_can_cancel_close(self):
        self.ui.writeJournal.setPlainText("A draft")
        with patch.object(QtWidgets.QMessageBox, "question", return_value=QtWidgets.QMessageBox.StandardButton.Cancel):
            self.window.close()
        self.assertTrue(self.window.isVisible())
        self.assertEqual(self.ui.writeJournal.toPlainText(), "A draft")

    def test_close_during_request_finishes_without_thread_crash(self):
        release = threading.Event()
        self.ui.chat_service = FakeChat(release=release)
        self.ui.lineEdit.setText("Pending reply")
        self.ui.handleSendButton()
        self.window.close()
        self.assertTrue(self.window.isVisible())
        self.assertFalse(self.window.isEnabled())
        release.set()
        self.wait_for(lambda: not self.window.isVisible())


if __name__ == "__main__":
    unittest.main()
