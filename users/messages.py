"""
Centralized message repository for user-facing communications

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

Usage Guidelines:
-----------------
1. Always reference these constants instead of hardcoding messages
2. Add new messages here rather than in views/forms/tests
3. Use clear, descriptive constant names (e.g., ACCOUNT_CREATED_SUCCESS)
4. Keep messages concise but actionable
5. Add translation markers (_())

Example:
--------
In views.py:
    from users.messages import users_messages
    messages.success(request, users_messages['ACCOUNT_CREATED_SUCCESS'])

In forms.py (with placeholder keys):
    from users.messages import users_messages
    self.add_error('city', users_massage['LOCATION_OUTSIDE_CITY_ERROR'] % {
                        'actual': actual_city.name, 
                        'selected': city.name
                    })
    NOTE: make sure the string contains correct placehoders
    like in this example : 
    {LOCATION_OUTSIDE_CITY_ERROR: _('Location is in %(actual)s, not %(selected)s')}

In tests.py:
    from users.messages import users_messages
    self.assertContains(response, users_messages['INVALID_CREDENTIALS'])

NOTE: Never modify constant names after they're used in tests, as this would
break test validation. Only update message strings when necessary.
"""
from django.utils.translation import gettext_lazy as _

users_messages = {
    # views
    'ALREAD_HAVE_PROFILE' : _('You already have beautiful profile'),
    'ACCOUNT_CREATED_SUCCESS' : _('Account created successfully'),
    'UNCOMPLETE_SIGN_UP_WARNING': _('You did not complete your sign up, please finish it to access all the features in the platform.'),
    'PROFILE_UPDATE_SUCCESS' : _('Profile updated successfully'),

    # forms
    'LOCATION_OUTSIDE_COUNTRY': _('Location must be within Algeria'),
    'LOCATION_UNKNOWN_CITY': _('Location not within any known city'),
    'LOCATION_OUTSIDE_CITY' : _('Location is in %(actual)s, not %(selected)s'),
    'COULD_NOT_GENERATE_LOCATION_FOR_CITY': _('Could not generate location for selected city'),
    'SELECT_CITY_OR_LOCATION': _('Please select either a location on the map or a city')
}