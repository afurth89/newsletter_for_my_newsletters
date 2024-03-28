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

from src.my_model import summarize_text_with_my_model


load_dotenv()
client = OpenAI() # defaults to getting the key using os.environ.get("OPENAI_API_KEY")

# Write input and output to JSON files and store
timestamp = datetime.datetime.now()
subfolder = f'artifacts/{timestamp.strftime("%m%d")}'
os.makedirs(subfolder, exist_ok=True)

# Authentication scopes
SCOPES = ['https://mail.google.com/'] 

ENV = os.getenv('ENV')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

EMAILS_TO_FETCH = 5  # Number of emails to fetch

MAX_TOKENS = 1000  # Maximum number of tokens to use for summarization of a single email
API_URL = "https://api.openai.com/v1/completions"
OPENAI_MODEL = "gpt-3.5-turbo"


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
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=EMAILS_TO_FETCH).execute()
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
            sender = [i['value'] for i in headers if i['name'] == 'From'][0]
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
                'sender': sender,
                'subject': subject,
                'body': email_body
            }

            newsletter_content.append(email_data)

        
        with open(f'{subfolder}/{timestamp.strftime("%H%M")}_input.json', 'w') as file:
            json.dump(newsletter_content, file)

        return newsletter_content

def summarize_text_with_open_ai(text):
    """Uses OpenAI's API to summarize the given text using a conversational approach."""
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": "You are a highly skilled assistant, adept at summarizing detailed text into concise, informative summaries. Your task involves accurately capturing the content of the text and excelling at discerning and conveying the author's point of view. It's crucial to identify the nuances of their opinions. You are to interpret and summarize not only the factual content but also analyze the underlying perspectives and arguments, making the author's stance on the topics discussed crystal clear in your summary."},
                {"role": "user", "content": f"Generate a clear and structured summary that includes an initial one-sentence overview of the text. Follow this with bullet points summarizing each paragraph of the original content. Focus on accurately conveying both the content and the author's opinions. Highlight the author's stance on the discussed topics. Your summary should not only inform but also offer insight into what the author truly thinks about these issues. Format it into an HTML snippet enclosed in a <div>: \"{text}\""}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error occurred while sending request to OpenAI API: {e}")
        return "An error occurred during summarization."

def summarize_email_content(newsletter_content):
    summaries = []
    for email in newsletter_content:
        sender = email.get("sender")
        subject = email.get("subject")
        body = email.get("body")
        open_ai_summary = summarize_text_with_open_ai(body)
        my_model_summary = summarize_text_with_my_model(body)
        print(f"\nSender: {sender}\nSubject: {subject}\nOpen AI Summary: {open_ai_summary}\n")
        summaries.append({"sender": sender, "subject": subject, "open_ai_summary": open_ai_summary, "my_model_summary": my_model_summary})  # Append the subject and summary as a dict
    
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
      <h3>By {summary['sender']}</h3> 
      <h3>Open AI Summary</h3>
      {summary['open_ai_summary']}
      <h3>My Model Summary</h3>
      {summary['my_model_summary']}
    </div>
    """

  return html_template.format(summary_blocks)


# Update your main script execution
if __name__ == '__main__': 
    service = get_gmail_service()
    email_data = fetch_and_parse_emails(service)
    summaries = summarize_email_content(email_data)
    html_content = generate_summary_html(summaries)
    if (ENV == 'prod'):
        print(f'\nSending email to {EMAIL_RECIPIENT}\n')
        send_email(service, to=EMAIL_RECIPIENT, subject=f'Newsletter Summary: {timestamp.strftime("%m/%d")}',  message_content=html_content) 
    else:
        file_path = f'{subfolder}/{timestamp.strftime("%H%M")}_email.html'
        with open(file_path, 'w') as file:
            print(f'\nSkipping email sending in non-prod environment. Storing HTML content to {file_path}')
            file.write(html_content)
