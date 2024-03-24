"""
email_manager.py

This module contains the EmailManager class which is responsible for interacting with the Gmail API.

Classes:
    EmailManager: Manages the interaction with the Gmail API.

"""

import base64
import os.path
import pickle
from datetime import datetime

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from logger import logger
from models.email import Email


class EmailManager:
    """
    Manages the interaction with the Gmail API.

    Attributes:
        credentials_file (str): The path to the file containing the credentials.
        token_file (str): The path to the file containing the token.
    """

    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self, credentials_file='../credentials.json', token_file='../token.pickle'):
        """
        Initializes the EmailManager with the given credentials and token files.

        Args:
            credentials_file (str): The path to the file containing the credentials.
            token_file (str): The path to the file containing the token.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = self.get_credentials()

    def get_credentials(self):
        """
        Retrieves the credentials for the Gmail API or creates one.

        Returns:
            The credentials for the Gmail API.
        """
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
        """
        Syncs the emails from the Gmail API and saves them to the database.
        """
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

                email = self._init_email(msg_id=msg['id'], subject=subject, sender=sender, content=body, recipient=recipient, cc=cc,
                              date_received=date_received, synced_at=datetime.now())

                email.save()

                logger.info(f"Subject: {subject}")
                logger.info(f"From: {sender}")
                logger.info(f"recipient: {recipient}")
                logger.info(f"cc: {cc}")
                logger.info(f"date_received: {date_received}")
                logger.info(f"msg_id: {msg['id']}")

            except Exception as e:
                logger.error(f"An error occurred: {e}")

    def mark_as_read(self, msg_id):
        """
        Marks the email with the given message ID as read.

        Args:
            msg_id (str): The message ID of the email to mark as read.
        """
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

    def move_to_label(self, msg_id, new_label_name):
        """
        Moves the email with the given message ID to the label with the given label ID.

        Args:
            msg_id (str): The message ID of the email to move.
            new_label_id (str): The ID of the label to move the email to.
        """
        try:
            new_label_id = self.get_label_id(new_label_name)
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'addLabelIds': [new_label_id]}
            ).execute()
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

    def get_label_id(self, label_name):
        """
        Retrieves the ID of the label with the given name from the Gmail API.

        Args:
            label_name (str): The name of the label.

        Returns:
            The ID of the label, or None if no such label exists.
        """
        try:
            labels = self.get_labels()
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

        return None

    def get_labels(self):
        """
        Retrieves and logs the labels from the Gmail API.
        """
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            result = service.users().labels().list(userId='me').execute()
            labels = result.get('labels', [])

            for label in labels:
                logger.info(f"Label ID: {label['id']}, Label Name: {label['name']}")
            return labels
        except HttpError as error:
            logger.error(f'An error occurred: {error}')

    def _init_email(self, msg_id, subject, sender, content, recipient, cc, date_received, synced_at):
        """
        Upserts an Email object with the given attributes based on msg_id.
        Returns:
            The initialized/existing Email object.
        """
        email = Email.get_by_msg_id(msg_id) or Email()
        email.msg_id = msg_id
        email.subject = subject
        email.sender = sender
        email.content = str(content)
        email.recipient = recipient
        email.cc = cc
        email.date_received = date_received
        email.synced_at = synced_at
        return email
