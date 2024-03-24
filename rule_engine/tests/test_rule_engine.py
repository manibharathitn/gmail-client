import json
import unittest
from unittest.mock import MagicMock, call
from ..rule_engine import RuleEngine
from unittest.mock import mock_open, patch

class TestRuleEngine(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'rules': [{'field_name': 'subject', 'predicate': 'contains', 'value': 'test'}],
        'actions': [{'action_name': 'mark_as_read'}],
        'collection_predicate': 'all'
    }))
    def setUp(self, mock_file):
        self.rule_engine = RuleEngine('rules.json')

    @patch('rule_engine.rule_engine.Rule')
    @patch('rule_engine.rule_engine.Action')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'rules': [{'field_name': 'subject', 'predicate': 'contains', 'value': 'test'}],
        'actions': [{'action_name': 'mark_as_read'}],
        'collection_predicate': 'all'
    }))
    def test_load_rules_from_json(self, mock_file, mock_action, mock_rule):
        self.rule_engine.load_rules_from_json('rules.json')
        # Assert that the Rule and Action classes were called with the correct arguments
        mock_rule.assert_called_with('subject', 'contains', 'test')
        mock_action.assert_called_with('mark_as_read', None)

        # Assert that the collection_predicate attribute was set correctly
        self.assertEqual(self.rule_engine.collection_predicate, 'all')

    @patch('rule_engine.rule_engine.Email.filter')
    def test_filter(self, mock_filter):
        # Mock the filter method to return a predefined list of email IDs
        mock_filter.return_value.all.return_value = [('email1',), ('email2',)]

        # Call the filter method
        self.rule_engine.filter()

        # Assert that the filter method was called with the correct arguments
        mock_filter.assert_called_with(subject={'contains': 'test'})

        # Assert that the filtered_email_ids attribute was set correctly
        self.assertEqual(self.rule_engine.filtered_email_ids, set(['email1', 'email2']))

    @patch('rule_engine.rule_engine.Action.perform')
    def test_perform_action(self, mock_perform):
        # Set the filtered_email_ids attribute to a predefined list of email IDs
        self.rule_engine.filtered_email_ids = ['email1', 'email2']

        # Call the perform_action method
        self.rule_engine.perform_action(None)

        # Assert that the perform method was called for each email ID
        calls = [call('email1', None), call('email2', None)]
        mock_perform.assert_has_calls(calls)

    @patch('rule_engine.rule_engine.Email.filter')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'rules': [{'field_name': 'subject', 'predicate': 'contains', 'value': 'test'}, {'field_name': 'from', 'predicate': 'contains', 'value': 'sender1'}],
        'actions': [{'action_name': 'mark_as_read'}],
        'collection_predicate': 'all'
    }))
    def test_filter_all_multiple_rules(self, file_mock, mock_filter):
        # Mock the filter method to return different lists of email IDs for different rules
        def side_effect(**kwargs):
            mock_all = MagicMock()
            if kwargs == {'subject': {'contains': 'test'}}:
                mock_all.all.return_value = [('email1',), ('email2',)]
            elif kwargs == {'sender': {'contains': 'sender1'}}:
                mock_all.all.return_value = [('email1',)]
            else:
                mock_all.all.return_value = []
            return mock_all

        mock_filter.side_effect = side_effect
        self.rule_engine.load_rules_from_json('rules.json')

        self.rule_engine.collection_predicate = 'all'

        # Call the filter method
        self.rule_engine.filter()

        # Assert that the filtered_email_ids attribute contains only the email IDs that are common to all rules
        self.assertEqual(self.rule_engine.filtered_email_ids, set(['email1']))

    @patch('rule_engine.rule_engine.Email.filter')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'rules': [{'field_name': 'subject', 'predicate': 'contains', 'value': 'test'},
                  {'field_name': 'from', 'predicate': 'contains', 'value': 'sender1'}],
        'actions': [{'action_name': 'mark_as_read'}],
        'collection_predicate': 'all'
    }))
    def test_filter_any_multiple_rules(self, file_mock, mock_filter):
        # Mock the filter method to return different lists of email IDs for different rules
        def side_effect(**kwargs):
            mock_all = MagicMock()
            if kwargs == {'subject': {'contains': 'test'}}:
                mock_all.all.return_value = [('email1',), ('email2',)]
            elif kwargs == {'sender': {'contains': 'sender1'}}:
                mock_all.all.return_value = [('email1',)]
            else:
                mock_all.all.return_value = []
            return mock_all

        mock_filter.side_effect = side_effect
        self.rule_engine.load_rules_from_json('rules.json')

        self.rule_engine.collection_predicate = 'any'

        # Call the filter method
        self.rule_engine.filter()

        # Assert that the filtered_email_ids attribute contains the email IDs that satisfy any of the rules
        self.assertEqual(self.rule_engine.filtered_email_ids, set(['email1', 'email2']))

if __name__ == '__main__':
    unittest.main()