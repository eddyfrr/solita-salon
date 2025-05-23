# booking/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class AlphanumericValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            raise ValidationError(
                _("Your password must contain at least one letter and one number."),
                code='password_not_alphanumeric',
            )

    def get_help_text(self):
        return _("Your password must contain at least one letter and one number.")