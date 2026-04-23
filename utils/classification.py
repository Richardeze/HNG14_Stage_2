def get_age_group(age: int) -> str:
    if age < 0:
        raise ValueError("Age cannot be negative")

    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    else:
        return "senior"