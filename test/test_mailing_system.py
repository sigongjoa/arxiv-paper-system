import os
import unittest

# Adjust path to include project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in os.sys.path:
    os.sys.path.insert(0, project_root)

from mailer import send_email


class TestMailingSystem(unittest.TestCase):
    def test_send_email(self):
        """Attempt to send a test email."""
        to_email = "zeskywa499@gmail.com"
        try:
            send_email(
                subject="Test Email",
                body="This is a test email from arxiv-paper-system.",
                to_email=to_email,
            )
        except Exception as e:
            self.fail(f"Failed to send email: {e}")


if __name__ == "__main__":
    unittest.main()
