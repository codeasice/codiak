"""
Configuration helper for YNAB Categorizer tool.
Handles saving/loading of categorization rules.
"""

import json
import os
from typing import List, Dict
from datetime import datetime

CONFIG_FILE = "ynab_categorizer_rules.json"

def get_config_path():
    """Get the path to the config file."""
    return os.path.join(os.path.dirname(__file__), "..", CONFIG_FILE)

def add_dates_to_rule(rule: Dict) -> Dict:
    """Add create and update dates to a rule if they don't exist."""
    current_time = datetime.now().isoformat()

    if 'created_at' not in rule:
        rule['created_at'] = current_time
    if 'updated_at' not in rule:
        rule['updated_at'] = current_time

    return rule

def load_rules() -> List[Dict]:
    """Load rules from config file."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                rules = json.load(f)
                # Add dates to existing rules that don't have them
                updated_rules = []
                for rule in rules:
                    updated_rule = add_dates_to_rule(rule)
                    updated_rules.append(updated_rule)

                # Save updated rules if any were modified
                if updated_rules != rules:
                    save_rules(updated_rules)

                return updated_rules
        except (json.JSONDecodeError, IOError):
            pass

    # Return default rules if file doesn't exist or is invalid
    default_rules = [
        {"match": "Amazon", "type": "contains", "category_id": ""},
        {"match": "Starbucks", "type": "contains", "category_id": ""},
        {"match": "Uber", "type": "contains", "category_id": ""},
        {"match": "Netflix", "type": "contains", "category_id": ""},
        {"match": "Spotify", "type": "contains", "category_id": ""},
    ]

    # Add dates to default rules
    for rule in default_rules:
        add_dates_to_rule(rule)

    return default_rules

def save_rules(rules: List[Dict], changed_rule_indices: List[int] = None):
    """Save rules to config file."""
    config_path = get_config_path()
    try:
        current_time = datetime.now().isoformat()

        # Only update the updated_at timestamp for rules that were actually changed
        if changed_rule_indices is not None:
            for index in changed_rule_indices:
                if 0 <= index < len(rules):
                    rules[index]['updated_at'] = current_time
        else:
            # Fallback: update all rules (for backward compatibility)
            for rule in rules:
                rule['updated_at'] = current_time

        with open(config_path, 'w') as f:
            json.dump(rules, f, indent=2)
        return True
    except IOError:
        return False

def format_date(date_string: str) -> str:
    """Format a date string for display."""
    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return "Unknown"