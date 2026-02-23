from django.core.exceptions import ValidationError


def has_special_char(text):
    return any(c for c in text if not c.isalnum() and not c.isspace())


def has_upper_case(text):
    return any(letter.isupper() for letter in text)


def has_lower_case(text):
    return any(letter.islower() for letter in text)


def has_numbers(text):
    return any(char.isdigit() for char in text)


class PasswordValidator(object):
    """
        + Upper case (e.g. “A”)
        + Lower case (e.g. “a”)
        + Number (e.g. “1”)
        + Special character from a specific set (e.g. “@”)
    """
    def validate(self, password, user=None):
        if not has_upper_case(password):
            raise ValidationError(
                "This password does not contain any upper case characters.",
            )
        if not has_lower_case(password):
            raise ValidationError(
                "This password does not contain any lower case characters.",
            )
        if not has_numbers(password):
            raise ValidationError(
                "This password does not contain any numbers.",
            )
        if not has_special_char(password):
            raise ValidationError(
                "This password does not contain any special characters eg. @.",
            )

    def get_help_text(self):
        return "Your password must contain a lower case character, upper case character number and a special character eg @"
