"""
Data cleaning utilities for Amazon product & review batch ETL.
"""
import pandas as pd


def clean_price(val):
    """
    Cleans price strings with currency symbols and commas.
    Example: '₹1,099' -> 1099.0
    """
    if pd.isna(val) or val is None:
        return None
    cleaned = str(val).replace("₹", "").replace(",", "").replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_pct(val):
    """
    Cleans percentage strings into floats.
    Example: '64%' -> 64.0
    """
    if pd.isna(val) or val is None:
        return None
    cleaned = str(val).replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_count(val):
    """
    Cleans count numbers formatted with commas.
    Example: '24,269' -> 24269
    """
    if pd.isna(val) or val is None:
        return 0
    cleaned = str(val).replace(",", "").strip()
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def clean_rating(val):
    """
    Cleans rating floats, handling comma-decimal variants.
    Example: '4.2' or '4,2' -> 4.2
    """
    if pd.isna(val) or val is None:
        return None
    cleaned = str(val).replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
