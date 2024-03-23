import unittest
from unittest.mock import patch, MagicMock
from email_reader.email_reader import EmailManager


class TestEmailManager(unittest.TestCase):
    @patch.object(EmailManager, 'get_credentials', return_value='dummy_credentials')
    def setUp(self, mock_get_credentials):
        self.email_manager = EmailManager()

    @patch('email_reader.build')
    def test_get_emails(self, mock_build):
        # Setup
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {'messages': []}

        # Call
        self.email_manager.get_emails()

        # Assert
        mock_build.assert_called_once_with('gmail', 'v1', credentials='dummy_credentials')
        mock_service.users.assert_called_once()
        mock_service.users.return_value.messages.assert_called_once()
        mock_service.users.return_value.messages.return_value.list.assert_called_once_with(userId='me')
        mock_service.users.return_value.messages.return_value.list.return_value.execute.assert_called_once()

    @patch('email_reader.build')
    def test_mark_as_read(self, mock_build):
        # Setup
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Call
        self.email_manager.mark_as_read('message_id')

        # Assert
        mock_build.assert_called_once_with('gmail', 'v1', credentials='dummy_credentials')
        mock_service.users.assert_called_once()
        mock_service.users.return_value.messages.assert_called_once()
        mock_service.users.return_value.messages.return_value.modify.assert_called_once_with(userId='me',
                                                                                             id='message_id', body={
                'removeLabelIds': ['UNREAD']})

    @patch('email_reader.build')
    def test_move_to_label(self, mock_build):
        # Setup
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Call
        self.email_manager.move_to_label('message_id', 'new_label_id')

        # Assert
        mock_build.assert_called_once_with('gmail', 'v1', credentials='dummy_credentials')
        mock_service.users.assert_called_once()
        mock_service.users.return_value.messages.assert_called_once()
        mock_service.users.return_value.messages.return_value.modify.assert_called_once_with(userId='me',
                                                                                             id='message_id', body={
                'addLabelIds': ['new_label_id']})

    @patch('email_reader.build')
    def test_get_labels(self, mock_build):
        # Setup
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {'labels': []}

        # Call
        self.email_manager.get_labels()

        # Assert
        mock_build.assert_called_once_with('gmail', 'v1', credentials='dummy_credentials')
        mock_service.users.assert_called_once()
        mock_service.users.return_value.labels.assert_called_once()
        mock_service.users.return_value.labels.return_value.list.assert_called_once_with(userId='me')
        mock_service.users.return_value.labels.return_value.list.return_value.execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()
