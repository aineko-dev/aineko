"""Functions for validation checks used in pydantic models."""


def check_power_of_2(x: int) -> int:
    """Check that value is a power of 2 using bit manipulation."""
    if not ((x & (x - 1) == 0) and x != 0):
        raise ValueError("Value must be a power of 2")
    return x
