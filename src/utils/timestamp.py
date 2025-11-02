"""Timestamp utilities for consistent time formatting."""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo


def get_current_time_utc() -> datetime:
    """Get current time in UTC timezone.
    
    Returns:
        Current datetime in UTC
    """
    return datetime.now(timezone.utc)


def get_current_time_local() -> datetime:
    """Get current time in local timezone.
    
    Returns:
        Current datetime in local timezone
    """
    return datetime.now()


def format_timestamp(dt: datetime, include_timezone: bool = True) -> str:
    """Format datetime in readable format.
    
    Args:
        dt: Datetime object to format
        include_timezone: Whether to include timezone info
        
    Returns:
        Formatted timestamp string: YYYY-MM-DD HH:MM:SS [TZ]
    """
    if include_timezone:
        if dt.tzinfo is None:
            # Assume local time if no timezone
            return dt.strftime("%Y-%m-%d %H:%M:%S Local")
        elif dt.tzinfo == timezone.utc:
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_timestamp_short(dt: datetime) -> str:
    """Format datetime in short format for display.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        Formatted timestamp string: HH:MM:SS
    """
    return dt.strftime("%H:%M:%S")


def format_timestamp_for_filename(dt: Optional[datetime] = None) -> str:
    """Format datetime for use in filenames.
    
    Args:
        dt: Datetime object to format (defaults to current UTC time)
        
    Returns:
        Formatted timestamp string: YYYYMMDD_HHMMSS
    """
    if dt is None:
        dt = get_current_time_utc()
    return dt.strftime("%Y%m%d_%H%M%S")


def get_time_display() -> dict:
    """Get current time in multiple formats for display.
    
    Returns:
        Dictionary with UTC and local time strings
    """
    now_utc = get_current_time_utc()
    now_local = get_current_time_local()
    
    return {
        'utc': format_timestamp(now_utc),
        'local': format_timestamp(now_local),
        'utc_iso': now_utc.isoformat(),
        'local_iso': now_local.isoformat(),
        'utc_short': format_timestamp_short(now_utc),
        'local_short': format_timestamp_short(now_local),
    }


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string in ISO format
        
    Returns:
        Datetime object
    """
    return datetime.fromisoformat(timestamp_str)


def timestamp_to_local(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to local timezone.
    
    Args:
        utc_dt: UTC datetime object
        
    Returns:
        Datetime in local timezone
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone()


def seconds_to_readable(seconds: int) -> str:
    """Convert seconds to readable duration.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Readable duration string (e.g., "2h 30m", "45m 30s")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"

