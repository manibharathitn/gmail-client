from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import base64
from bs4 import BeautifulSoup
from googleapiclient.errors import HttpError


class EmailManager:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = self.get_credentials()

    def get_credentials(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def get_emails(self):
        service = build('gmail', 'v1', credentials=self.creds)
        result = service.users().messages().list(userId='me').execute()
        messages = result.get('messages')

        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            try:
                payload = txt['payload']
                headers = payload['headers']

                subject = next(d['value'] for d in headers if d['name'] == 'Subject')
                sender = next(d['value'] for d in headers if d['name'] == 'From')

                parts = payload.get('parts')[0]
                data = parts['body']['data'].replace("-", "+").replace("_", "/")
                decoded_data = base64.b64decode(data)

                soup = BeautifulSoup(decoded_data, "lxml")
                body = soup.body()

                print(f"Subject: {subject}")
                print(f"From: {sender}")
                print(f"Message: {body}\n")
            except Exception as e:
                print(f"An error occurred: {e}")

    def mark_as_read(self, msg_id):
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except HttpError as error:
            print(f'An error occurred: {error}')

    def move_to_label(self, msg_id, new_label_id):
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'addLabelIds': [new_label_id]}
            ).execute()
        except HttpError as error:
            print(f'An error occurred: {error}')

    def get_labels(self):
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            result = service.users().labels().list(userId='me').execute()
            labels = result.get('labels', [])

            for label in labels:
                print(f"Label ID: {label['id']}, Label Name: {label['name']}")
        except HttpError as error:
            print(f'An error occurred: {error}')

if __name__ == '__main__':
    reader = EmailManager()
    # reader.get_emails()
    reader.get_labels()