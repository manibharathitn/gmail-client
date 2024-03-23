import logging
from datetime import datetime

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import base64
from bs4 import BeautifulSoup
from googleapiclient.errors import HttpError

from models.email import Email

from logger import logger

class EmailManager:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_file='../credentials.json', token_file='../token.pickle'):
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

    def sync_emails(self):
        service = build('gmail', 'v1', credentials=self.creds)
        result = service.users().messages().list(userId='me').execute()
        messages = result.get('messages')

        email_list = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            try:
                payload = txt['payload']
                headers = payload['headers']

                subject = next(d['value'] for d in headers if d['name'] == 'Subject')
                sender = next(d['value'] for d in headers if d['name'] == 'From')
                recipient = next(d['value'] for d in headers if d['name'] == 'To')
                cc = next((d['value'] for d in headers if d['name'] == 'Cc'), None)
                date_received = next(d['value'] for d in headers if d['name'] == 'Date')

                parts = payload.get('parts')[0]
                data = parts['body']['data'].replace("-", "+").replace("_", "/")
                decoded_data = base64.b64decode(data)

                soup = BeautifulSoup(decoded_data, "lxml")
                body = soup.body()

                email = Email(msg_id=msg['id'], subject=subject, sender=sender, content=body, recipient=recipient, cc=cc,
                              date_received=date_received, synced_at=datetime.now())
                email_list.append(email)

                logger.info(f"Subject: {subject}")
                logger.info(f"From: {sender}")
                logger.info(f"recipient: {recipient}")
                logger.info(f"cc: {cc}")
                logger.info(f"date_received: {date_received}")
                logger.info(f"msg_id: {msg['id']}")

            except Exception as e:
                logger.error(f"An error occurred: {e}")

    def mark_as_read(self, msg_id):
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

    def move_to_label(self, msg_id, new_label_id):
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'addLabelIds': [new_label_id]}
            ).execute()
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

    def get_labels(self):
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            result = service.users().labels().list(userId='me').execute()
            labels = result.get('labels', [])

            for label in labels:
                logger.info(f"Label ID: {label['id']}, Label Name: {label['name']}")
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

if __name__ == '__main__':
    reader = EmailManager()
    reader.sync_emails()
    # reader.get_labels()