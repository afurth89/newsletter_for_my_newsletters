import email
import imaplib
import logging
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration and Setup
SERVICE_ACCOUNT_FILE = 'newsletter-for-my-newsletters-ed1e11e37005.json' 
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/cloud-platform'] 
SENDER_EMAIL = 'andrewfurthnewsletters@gmail.com'  # Your dedicated Gmail address

logging.basicConfig(level=logging.DEBUG)  # Enable detailed logging

load_dotenv()

# TODO: Revisit service account authentication for Gmail. Current credentials 
#       are not generating a valid access token. Investigate library versions, 
#       service account permissions, and potential API changes.

# Connect to Gmail IMAP server
imap_server = imaplib.IMAP4_SSL('imap.gmail.com')

# Get credentials from environment variables
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')

# Use environment variables for login:
imap_server.login(USER_EMAIL, USER_PASSWORD)

imap_server.select('INBOX')  # Select the inbox

# Fetch recent emails (max 10)
status, email_ids = imap_server.search(None, '(SINCE "01-Jan-2023")')  # Adjust date as needed
id_list = email_ids[0].split()
num_emails_to_fetch = min(10, len(id_list))

# Process emails
for i in range(num_emails_to_fetch):
    status, email_data = imap_server.fetch(id_list[i], '(RFC822)') 
    email_message = email.message_from_bytes(email_data[0][1])

    subject = email_message['Subject']
    body = email_message.get_payload(decode=True)  # Get the decoded body
    if body is not None:
        body_text = body.decode('utf-8')[:100]  # Truncate to the first 100 characters
    else:
        body_text = '[No text content]'

    print(f"Subject: {subject}")
    print(f"Body (first 100): {body_text}")
    print("-" * 20)

imap_server.close()
imap_server.logout()
