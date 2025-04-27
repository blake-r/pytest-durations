"""Helper module to get original time module functions when a time travelling package is used."""
from time import monotonic

try:
    # if freezegun is installed, use its stored real function
    from freezegun import api as freezegun_api
except ImportError:
    pass
else:
    monotonic = real_monotonic = freezegun_api.real_monotonic

try:
    # if time_machine is installed, use its stored real function
    from time_machine import escape_hatch
except ImportError:
    pass
else:

    def real_monotonic() -> float:
        """Use escape_hatch if time_machine is currently travelling, original time module otherwise."""
        return escape_hatch.time.monotonic() if escape_hatch.is_travelling() else monotonic()


def get_current_ticks() -> float:
    """Return uniformly increasing value in seconds."""
    return real_monotonic()
