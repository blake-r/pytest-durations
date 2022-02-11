from time import monotonic

try:
    # if freezegun is installed, use its stored real function
    import freezegun
except ImportError:
    pass
else:
    freezegun.configure(extend_ignore_list=[__name__])


def get_current_ticks():
    """Return uniformly increasing value in seconds."""
    return monotonic()
