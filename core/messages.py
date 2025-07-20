"""
Centralized message repository for user-facing communications in core app

Purpose:
--------
This module serves as a single source of truth for all user-facing messages
(success, error, warning, info) used throughout the users app. Centralizing
messages provides:

1. Consistency: Ensures uniform terminology and formatting across all views,
   forms, and templates
2. Test Reliability: Enables safe message validation in tests without fragile
   string matching
3. Maintainability: Simplifies message updates and translations
4. Typo Prevention: Eliminates duplicate strings that could diverge or contain errors
5. Audit Trail: Provides one location to review all user communications

NOTE: Never modify constant names after they're used in tests, as this would
break test validation. Only update message strings when necessary.
"""
from django.utils.translation import gettext_lazy as _

core_messages = {
    # forms
    'DATE_IN_THE_PAST': _('Invalid date. Please schedule your initiative in the future.'),
    'DATE_TOO_CLOSE': _('Invalid date. Please schedule your initiative at least one week in advance.'),

    # views
    'MANAGERS_ONLY' : _('You have to be a manager to create initiatives.'),
    'INITIATIVE_CREATED_SUCCESS': _('Your initiative has been created successfully.')
}