"""The only place the backend imports analytics from.

Uses Sudiksha's backend/analytics package if it exports the three contract
functions; otherwise uses fallback_analytics and says so loudly.
"""
try:
    from analytics import (  # Sudiksha's package
        customer_delay_stats,
        find_inconsistencies,
        get_late_payers,
    )
    USING_FALLBACK = False
except ImportError:
    from fallback_analytics import (
        customer_delay_stats,
        find_inconsistencies,
        get_late_payers,
    )
    USING_FALLBACK = True
    print("USING_FALLBACK: analytics functions come from fallback_analytics.py")