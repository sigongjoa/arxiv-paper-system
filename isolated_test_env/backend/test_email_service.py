import os
import sys
# Add the parent directory of automation to sys.path for import
# This ensures that 'automation' can be imported as a package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation.email_service import EmailService
from automation.gmail_email_service import GmailEmailService

# Set EMAIL_TEST_MODE to 'true' explicitly for the test for SES
os.environ['EMAIL_TEST_MODE'] = 'true'

# Initialize SES EmailService
es_service_ses = EmailService()

# Define test email parameters for SES
subject_ses = "Test Newsletter (AWS SES)"
html_content_ses = "<p>This is a <b>test</b> newsletter content from AWS SES.</p>"
text_content_ses = "This is a test newsletter content from AWS SES."
recipients_ses = ["test@example.com", "zeskywa499@gmail.com"]
sender_email_ses = "sender@example.com"

# Send a test email for SES (it will be saved to disk in test mode)
try:
    print("\n=== Attempting to send test email via AWS SES Service ===")
    result_ses = es_service_ses.send_newsletter(
        subject=subject_ses,
        html_content=html_content_ses,
        text_content=text_content_ses,
        recipients=recipients_ses,
        sender_email=sender_email_ses
    )
    print(f"AWS SES Test email sent result: {result_ses}")
    if result_ses.get('test_mode'):
        print("AWS SES Email was saved to local files in test mode.")
    else:
        print("AWS SES Email was attempted to be sent via SES (not expected in test mode).")
except Exception as e:
    print(f"Error sending AWS SES test email: {e}")

# Test with PDF attachment for SES
pdf_content_ses = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj 4 0 obj<</Type/Font/Subtype/Type1/Name/F1/BaseFont/Helvetica/Encoding/MacRomanEncoding>>endobj 5 0 obj<</Length 44>>stream\nBT /F1 12 Tf 72 720 Td (Hello World!) Tj ET\nendstream\nendobj xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000059 00000 n\n0000000100 00000 n\n0000000171 00000 n\n0000000259 00000 n\ntrailer<</Size 6/Root 1 0 R>>startxref\n363\n%%EOF"
pdf_filename_ses = "test_attachment_ses.pdf"

try:
    print("\n=== Attempting to send AWS SES email with PDF attachment ===")
    result_with_pdf_ses = es_service_ses.send_newsletter(
        subject="Test Newsletter with PDF (AWS SES)",
        html_content="<p>This is a test newsletter with a <b>PDF attachment</b> from AWS SES.</p>",
        text_content="This is a test newsletter with a PDF attachment from AWS SES.",
        recipients=["test_pdf@example.com", "zeskywa499@gmail.com"],
        sender_email="sender_pdf@example.com",
        pdf_attachment=pdf_content_ses,
        pdf_filename=pdf_filename_ses
    )
    print(f"AWS SES Test email with PDF result: {result_with_pdf_ses}")
    if result_with_pdf_ses.get('test_mode'):
        print("AWS SES Email with PDF was saved to local files in test mode.")
    else:
        print("AWS SES Email with PDF was attempted to be sent via SES (not expected in test mode).")
except Exception as e:
    print(f"Error sending AWS SES test email with PDF: {e}")


# Set GMAIL_EMAIL_TEST_MODE to 'true' explicitly for the test for Gmail
os.environ['GMAIL_EMAIL_TEST_MODE'] = 'true'

# Initialize Gmail EmailService
es_service_gmail = GmailEmailService()

# Define test email parameters for Gmail
subject_gmail = "Test Newsletter (Gmail)"
html_content_gmail = "<p>This is a <b>test</b> newsletter content from Gmail.</p>"
text_content_gmail = "This is a test newsletter content from Gmail."
recipients_gmail = ["test_gmail@example.com", "zeskywa499@gmail.com"]
sender_alias_gmail = "My App (Gmail Test)"

# Send a test email for Gmail (it will be saved to disk in test mode)
try:
    print("\n=== Attempting to send test email via Gmail Service ===")
    result_gmail = es_service_gmail.send_email(
        subject=subject_gmail,
        html_content=html_content_gmail,
        text_content=text_content_gmail,
        recipients=recipients_gmail,
        sender_alias=sender_alias_gmail
    )
    print(f"Gmail Test email sent result: {result_gmail}")
    if result_gmail.get('test_mode'):
        print("Gmail Email was saved to local files in test mode.")
    else:
        print("Gmail Email was attempted to be sent (not expected in test mode).")
except Exception as e:
    print(f"Error sending Gmail test email: {e}") 