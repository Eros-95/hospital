def mask_id_card(value):
    if not value:
        return value
    if len(value) <= 10:
        return "*" * len(value)
    return value[:6] + "*" * (len(value) - 10) + value[-4:]
