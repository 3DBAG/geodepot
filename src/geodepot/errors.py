class GeodepotRuntimeError(Exception):
    """General error related to Geodepot's operation."""


class GeodepotInvalidRepository(Exception):
    """Invalid repository, possibly due to missing contents."""


class GeodepotInvalidConfiguration(Exception):
    """Invalid configuration value."""


class GeodepotIndexError(Exception):
    """Raised when reading or writing the index file fails."""


class GeodepotDataError(Exception):
    """Raised when processing a data item fails."""


class GeodepotSyncError(Exception):
    """Raised when a push or pull operation fails."""
