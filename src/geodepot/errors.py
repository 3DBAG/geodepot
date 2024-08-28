class GeodepotRuntimeError(Exception):
    """General error related to Geodepot's operation."""


class GeodepotInvalidRepository(Exception):
    """Invalid repository, possibly due to missing contents."""
