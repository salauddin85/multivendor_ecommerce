import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SimplePasswordValidator:
    """
    Password must be at least 6 characters long,
    contain at least one uppercase letter, one lowercase letter, and one digit.
    Special characters are NOT allowed.
    """

    pattern = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{6,}$'
    )

    def validate(self, password, user=None):
        if not re.match(self.pattern, password):
            raise ValidationError(_(
                "Password must be at least 6 characters long and contain at least one uppercase letter, "
                "one lowercase letter, and one digit. Special characters are not allowed."
            ))

    def get_help_text(self):
        return _(
            "Your password must be at least 6 characters long, include one uppercase letter, "
            "one lowercase letter, and one digit. Special characters are not allowed."
        )



