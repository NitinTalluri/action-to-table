from functools import partial


def empty_to_unknown(value):
    # If the value is an empty list, return [0] to ensure that the "unknown" value is linked
    if not value:
        return [0]
    match value:
        case [0]:
            return value
        case [*values]:
            return [x for x in values if x != 0]
        case _:
            return value


def empty_to_unknown_one(value):
    # If the value is an empty list, return 1 to ensure that it is linked to the "NONE" record
    if not value:
        return [1]
    match value:
        case [1]:
            return value
        case [*values]:
            return [x for x in values if x >= 1]
        case _:
            return value


def _enforce_default(value, default):
    """If the value is None, return the default value"""
    return value if value is not None else default


enforce_default_zero = partial(_enforce_default, default=0)
