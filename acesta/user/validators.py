from django.core.exceptions import ValidationError


def validate_russian(value):
    def match(text, alphabet=set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя ")):
        return not alphabet.isdisjoint(text.lower())

    if not match(value):
        raise ValidationError(
            "%(value)s не на русском языке",
            params={"value": value},
        )
