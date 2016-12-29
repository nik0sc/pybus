class StopNotInRouteError(ValueError):
    """Can't find the stop in this route"""

class NoTimingsError(RuntimeError):
    """LTADM didn't return any timings"""
