try:
    # if freezegun is installed, use its stored real function
    from freezegun.api import real_monotonic as monotonic
except ImportError:
    from time import monotonic


# Return uniformly increasing value in seconds.
get_current_ticks = monotonic
