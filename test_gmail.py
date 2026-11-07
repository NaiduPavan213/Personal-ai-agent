from integrations.gmail import send_email

email_id = send_email(
    to="YOUR_EMAIL@gmail.com",
    subject="Testing Gmail API",
    body="Hello! This email was sent by my AI Personal Assistant."
)

print(email_id)