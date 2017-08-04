def as_number(num, default):
    try:
        return float(num)
    except ValueError:
        return default