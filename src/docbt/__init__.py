"""docbt - Documentation Build Tool for dbt projects."""

__version__ = "0.1.8"

# Export availability flags from providers
from .providers import BIGQUERY_AVAILABLE, SNOWFLAKE_AVAILABLE

__all__ = [
    "__version__",
    "SNOWFLAKE_AVAILABLE",
    "BIGQUERY_AVAILABLE",
]


def check_dependencies():
    """Check which optional dependencies are installed.

    Returns:
        dict: A dictionary with availability status of optional dependencies
    """
    return {
        "snowflake": SNOWFLAKE_AVAILABLE,
        "bigquery": BIGQUERY_AVAILABLE,
    }


def print_dependencies():
    """Print a formatted report of available dependencies."""
    deps = check_dependencies()

    print("docbt - Available Data Warehouse Connectors")
    print("=" * 50)

    for name, available in deps.items():
        status = "✓ Installed" if available else "✗ Not installed"
        install_cmd = f"pip install docbt[{name}]"

        print(f"\n{name.capitalize()}:")
        print(f"  Status: {status}")
        if not available:
            print(f"  Install: {install_cmd}")

    print("\n" + "=" * 50)
