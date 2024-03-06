import base64
import bs4
import email
import os.path
import pickle
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Authentication scopes
SCOPES = ['https://mail.google.com/'] 

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

def fetch_and_parse_emails():
    service = get_gmail_service()

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

        print(newsletter_content)

# Update your main script execution
if __name__ == '__main__': 
    fetch_and_parse_emails()
