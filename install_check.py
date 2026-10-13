"""Non-interactive packaged-app check; no API requests or personal files."""

import json
from pathlib import Path
import re

from PyQt6 import QtGui, QtWidgets


def write_report(window, ui, report_path):
    missing = []
    image_references = 0
    for widget in window.findChildren(QtWidgets.QWidget):
        for match in re.finditer(r"url\((.*?)\)", widget.styleSheet()):
            path = Path(match.group(1).strip("\"'"))
            image_references += 1
            if not path.is_file() or QtGui.QPixmap(str(path)).isNull():
                missing.append(widget.objectName())
    mood_checks = []
    ui.moodSupportButton.click()
    for button in [ui.stressButton, ui.sadButton, ui.lonelyButton, ui.angryButton, ui.anxietyButton]:
        button.click()
        mood_checks.append(bool(ui.measures.toPlainText().strip()))
    ui.showHomeScreenFrame()
    font_loaded = "Inter Variable" in QtGui.QFontDatabase.families()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot = report_path.with_suffix(".png")
    screenshot_saved = window.grab().save(str(screenshot))
    passed = not missing and all(mood_checks) and font_loaded and screenshot_saved
    report_path.write_text(json.dumps({
        "passed": passed,
        "image_references": image_references,
        "missing_images": missing,
        "font_loaded": font_loaded,
        "mood_buttons": mood_checks,
        "screenshot_saved": screenshot_saved,
    }, indent=2), encoding="utf-8")
    return 0 if passed else 1
