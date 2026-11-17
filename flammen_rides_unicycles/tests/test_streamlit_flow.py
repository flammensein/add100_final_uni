import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_DIRECTORY / "streamlit_app.py"
sys.path.insert(0, str(PROJECT_DIRECTORY))


class GuidedOrderFlowTests(unittest.TestCase):
    def test_billing_fields_are_shown_only_after_build_confirmation(self) -> None:
        app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
        self.assertFalse(app.exception, [str(error) for error in app.exception])
        self.assertEqual(len(app.text_input), 0)

        for label in (
            "Continue to saddle & seatpost",
            "Continue to rim & drivetrain",
            "Review build",
        ):
            next(button for button in app.button if button.label == label).click().run()
            self.assertFalse(app.exception, [str(error) for error in app.exception])
            self.assertEqual(len(app.text_input), 0)

        next(
            button
            for button in app.button
            if button.label == "Confirm build and continue to billing & shipping"
        ).click().run()
        self.assertFalse(app.exception, [str(error) for error in app.exception])
        self.assertIn("Full name", {widget.label for widget in app.text_input})
        self.assertIn("Street address", {widget.label for widget in app.text_input})


if __name__ == "__main__":
    unittest.main()
