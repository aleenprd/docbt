"""Data warehouse provider connectors for docbt."""

from typing import TYPE_CHECKING

# Import availability flags
try:
    from .conn_snowflake import SNOWFLAKE_AVAILABLE, ConnSnowflake
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    if TYPE_CHECKING:
        from .conn_snowflake import ConnSnowflake

try:
    from .conn_bigquery import BIGQUERY_AVAILABLE, ConnBigQuery
except ImportError:
    BIGQUERY_AVAILABLE = False
    if TYPE_CHECKING:
        from .conn_bigquery import ConnBigQuery

__all__ = [
    "SNOWFLAKE_AVAILABLE",
    "BIGQUERY_AVAILABLE",
]

# Only export classes if they're available
if SNOWFLAKE_AVAILABLE:
    __all__.append("ConnSnowflake")

if BIGQUERY_AVAILABLE:
    __all__.append("ConnBigQuery")
