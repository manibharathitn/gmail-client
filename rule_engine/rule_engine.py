"""
rule_engine.py

This module contains the Rule, Action, and RuleEngine classes.

Classes:
    Rule: Represents a rule that can be applied to an email.
    Action: Represents an action that can be performed on an email.
    RuleEngine: Applies rules and performs actions on emails.

"""

import itertools
import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from logger import logger
from models.email import Email


class Rule:
    """
    Represents a rule that can be applied to an email.

    Attributes:
        field_name (str): The name of the field the rule applies to.
        predicate (str): The condition that must be met for the rule to apply.
        value (str): The value that the field must meet for the rule to apply.
    """

    FIELD_NAME_COLUMN_MAPPING = {
        # Mapping of field name in rules file to column name in email table
        'subject': 'subject',
        'from': 'sender',
        'to': 'recipient',
        'cc': 'cc',
        'date_received': 'date_received',
    }

    def __init__(self, field_name, predicate, value):
        self.field_name = field_name
        self.predicate = predicate
        self.value = value

    def get_constituents(self):
        field_name = self.FIELD_NAME_COLUMN_MAPPING[self.field_name]
        predicate = self.predicate
        value = self.value

        if field_name == 'date_received' and 'd' in self.value:
            days = int(self.value.replace('d', ''))
            value = datetime.now() - timedelta(days=days)
        elif field_name == 'date_received' and 'm' in self.value:
            months = int(self.value.replace('m', ''))
            value = datetime.now() - relativedelta(months=months)

        return field_name, predicate, value


class Action:
    """
    Represents an action that can be performed on an email.

    Attributes:
        action_name (str): The name of the action.
        action_value (str): The value associated with the action, if any.
    """

    def __init__(self, action_name, action_value=None):
        self.action_name = action_name
        self.action_value = action_value

    def perform(self, msg_id, email_manager):
        if self.action_name == 'mark_as_read':
            logger.info(f"Marking email as read: {msg_id}")
            email_manager.mark_as_read(msg_id)
        elif self.action_name == 'move_to_label':
            logger.info(f"Moving email to label: {msg_id}")
            email_manager.move_to_label(msg_id, self.action_value)


class RuleEngine:
    """
    Applies rules and performs actions on emails.

    Attributes:
        rules_file_path (str): The path to the file containing the rules.
    """

    def __init__(self, rules_file_path):
        self.collection_predicate = None
        self.rules = []
        self.actions = []
        self.filtered_email_ids = None
        self.load_rules_from_json(rules_file_path)

    def load_rules_from_json(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)

        self.rules = [Rule(rule['field_name'], rule['predicate'], rule['value']) for rule in data['rules']]
        self.actions = [Action(action['action_name'], action.get('action_value')) for action in data['actions']]
        self.collection_predicate = data.get('collection_predicate')
        logger.info(f"successfully parsed rules from file: {file_path}")

    def filter(self):
        for rule in self.rules:
            field_name, predicate, value = rule.get_constituents()
            email_msg_ids = Email.filter(**{field_name: {predicate: value}}).all()
            email_msg_ids = list(itertools.chain(*email_msg_ids)) if email_msg_ids else email_msg_ids
            # if collection_predicate is all, then we need to take intersection of all the filtered email ids
            # if collection_predicate is any, then we need to take union of all the filtered email ids
            logger.info(f"field_name: {field_name}, predicate: {predicate}, value: {value}  Filtered email ids: {email_msg_ids}")
            # Initialize self.filtered_email_ids if it's None
            if self.filtered_email_ids is None:
                self.filtered_email_ids = set(email_msg_ids)
            else:
                # Perform the appropriate operation based on self.collection_predicate
                if self.collection_predicate == 'all':
                    self.filtered_email_ids &= set(email_msg_ids)  # Intersection operation
                else:
                    self.filtered_email_ids |= set(email_msg_ids)  # Union operation
        return self

    def perform_action(self, email_manager):
        for msg_id in self.filtered_email_ids:
            for action in self.actions:
                logger.info(f"Performing action: {action.action_name} on email: {msg_id}")
                action.perform(msg_id, email_manager)
