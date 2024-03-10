import base64
import bs4
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import logging
import os.path
import pickle
import re
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from openai import OpenAI

load_dotenv()
client = OpenAI() # defaults to getting the key using os.environ.get("OPENAI_API_KEY")

# Write input and output to JSON files and store
timestamp = datetime.datetime.now()
subfolder = f'artifacts/{timestamp.strftime("%m%d")}'
os.makedirs(subfolder, exist_ok=True)

# Authentication scopes
SCOPES = ['https://mail.google.com/'] 

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
API_URL = "https://api.openai.com/v1/completions"
OPENAI_MODEL = "gpt-3.5-turbo"

EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

def get_gmail_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    # It's created automatically when the authorization flow completes.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    print('Gmail service created')
    return build('gmail', 'v1', credentials=creds)

def extract_text_from_part(part):
    if part.get_content_type() == 'text/plain':
        return part.get_payload(decode=True).decode() 
    elif part.get_content_type() == 'text/html':
        html = part.get_payload(decode=True).decode()
        soup = bs4.BeautifulSoup(html, 'html.parser')
        return soup.get_text()  
    return ''  # If the content type is not text

def clean_excessive_whitespace(text):
    return re.sub(r'\s{2,}', ' ', text)  # Replace 2 or more whitespace characters with a single space 

def remove_html_tags(text):
    clean = re.sub('<[^<]+?>', '', text)  # Removes '<...>' HTML tag patterns
    return clean

sanitization_pipeline = [
    clean_excessive_whitespace,
    remove_html_tags,
    # You can add more functions here
]

def fetch_and_parse_emails(service):
    

    # Fetch recent emails from Inbox
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        newsletter_content = []  # Storage for all text content
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
        
            # Extract subject
            headers = msg['payload']['headers']
            subject = [i['value'] for i in headers if i['name'] == 'Subject'][0]
            email_body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == "text/plain":
                        data = part['body']['data'] 
                        decoded_data = base64.urlsafe_b64decode(data.encode('ASCII')).decode()
                        cleaned_data = decoded_data  # Start with decoded data

                        for func in sanitization_pipeline:
                            cleaned_data = func(cleaned_data)
                        email_body += cleaned_data
            
            email_data = {
                'subject': subject,
                # 'author': extract_author(msg),  # Assuming you'll write an author extraction function
                'body': email_body
            }

            newsletter_content.append(email_data)

        
        with open(f'{subfolder}/{timestamp.strftime("%H%M")}_input.json', 'w') as file:
            json.dump(newsletter_content, file)

        return newsletter_content

def summarize_text(text):
    """Uses OpenAI's API to summarize the given text using a conversational approach."""
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a highly skilled assistant, adept at summarizing detailed text into concise, informative summaries."},
                {"role": "user", "content": f"Summarize this text for me: \"{text}\""}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error occurred while sending request to OpenAI API: {e}")
        return "An error occurred during summarization."

def summarize_email_content(newsletter_content):
    summaries = []
    for email in newsletter_content:
        subject = email.get("subject")
        body = email.get("body")
        summary = summarize_text(body)
        print(f"Subject: {subject}\nSummary: {summary}\n")
        summaries.append({"subject": subject, "summary": summary})  # Append the subject and summary as a dict
    
    with open(f'{subfolder}/{timestamp.strftime("%H%M")}_output.json', 'w') as file:
        json.dump(summaries, file)

    return summaries

def send_email(service, to, subject, message_content):
  """Creates and sends an email using the Gmail service."""
  message = create_message('me', to, subject, message_content, is_html=True)  # Replace 'me' with your email if needed
  sent_message = service.users().messages().send(userId='me', body=message).execute()
  print(f'Message Id: {sent_message["id"]}')

def create_message(sender, to, subject, message_text, is_html=False):
  """Creates an email MIME message object."""

  message = MIMEMultipart('alternative')  # Create a multipart message for HTML + plain text versions
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject

  if is_html:
     part = MIMEText(message_text, 'html')
  else:
      part = MIMEText(message_text, 'plain')

  message.attach(part)
  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def generate_summary_html(summaries):
  """Generates an HTML email template with summaries."""
  html_template = """
  <!DOCTYPE html>
  <html>
  <head>
    <title>Newsletter Summaries</title>
    <style>
      body {{ font-family: Arial, sans-serif; }}
      .summary-container {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; }}
      h2 {{ color: #333; }}
      .summary {{ margin-top: 10px; }}
    </style>
  </head>
  <body>
    <h1>Newsletter Summaries</h1>
    {} 
  </body>
  </html>
  """

  summary_blocks = ""
  for summary in summaries:
    summary_blocks += f"""
    <div class="summary-container">
      <h2>{summary['subject']}</h2>
      <p class="summary">{summary['summary']}</p>
    </div>
    """

  return html_template.format(summary_blocks)


# Update your main script execution
if __name__ == '__main__': 
    service = get_gmail_service()
    email_data = fetch_and_parse_emails(service)
    summaries = summarize_email_content(email_data)
    html_content = generate_summary_html(summaries)
    send_email(service, to=EMAIL_RECIPIENT, subject=f'Newsletter Summary: {timestamp.strftime("%m/%d")}',  message_content=html_content) 
