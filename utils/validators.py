from datetime import date, datetime


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Invalid request data")


def validate_trip_payload(payload, partial=False):
    if not isinstance(payload, dict):
        raise ValidationError({"body": "Request body must be a JSON object"})

    required = ["origin", "destination", "travel_date", "fuel_consumption", "fuel_price", "tolls"]
    errors = {}
    if not partial:
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                errors[field] = "This field is required"

    text_fields = ("origin", "destination")
    for field in text_fields:
        if field in payload and (not isinstance(payload[field], str) or not payload[field].strip()):
            errors[field] = "Must be a non-empty string"

    if "travel_date" in payload:
        value = payload["travel_date"]
        if not isinstance(value, str):
            errors["travel_date"] = "Must use YYYY-MM-DD"
        else:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                errors["travel_date"] = "Must use YYYY-MM-DD"

    numeric_rules = {
        "fuel_consumption": lambda value: value > 0,
        "fuel_price": lambda value: value > 0,
        "tolls": lambda value: value >= 0,
    }
    for field, rule in numeric_rules.items():
        if field not in payload:
            continue
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors[field] = "Must be a number"
        else:
            try:
                if not rule(value):
                    errors[field] = "Has an invalid value"
            except TypeError:
                errors[field] = "Must be a number"

    if errors:
        raise ValidationError(errors)

    normalized = dict(payload)
    for field in text_fields:
        if field in normalized:
            normalized[field] = normalized[field].strip()
    if "travel_date" in normalized:
        normalized["travel_date"] = date.fromisoformat(normalized["travel_date"])
    return normalized
