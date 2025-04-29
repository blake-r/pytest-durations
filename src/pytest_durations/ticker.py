"""Helper module to get original time module functions when a time travelling package is used."""
from time import time

monotonic_impl = time

try:
    # if freezegun is installed, use its stored real function
    import freezegun
except ImportError:
    pass
else:
    freezegun.configure(extend_ignore_list=[__name__])

try:
    # if time_machine is installed, use its stored real function
    from time_machine import escape_hatch
except ImportError:
    pass
else:

    def monotonic_impl() -> float:
        """Use escape_hatch if time_machine is currently travelling, original time module otherwise."""
        return escape_hatch.time.time() if escape_hatch.is_travelling() else time()


def get_current_ticks() -> float:
    """Return uniformly increasing value in seconds."""
    return monotonic_impl()
