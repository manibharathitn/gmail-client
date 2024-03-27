from rule_engine.rule_engine import RuleEngine
from email_manager.email_manager import EmailManager

def process_rule_json(rules_file_path):
    # Initialize the RuleEngine with the path to the rules file
    rule_engine = RuleEngine(rules_file_path)

    # Initialize the EmailManager
    email_manager = EmailManager('credentials.json', 'token.pickle')

    # Sync the emails to database
    email_manager.sync_emails()

    # Filter the emails based on the rules
    rule_engine.filter()

    # Perform the actions on the filtered emails
    rule_engine.perform_action(email_manager)


if __name__ == "__main__":
    process_rule_json('rules/mark_as_read_rule.json')
    process_rule_json('rules/move_yt_or_mani.json')