import os
import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional


def get_env_variable(name: str, default: Optional[str] = None) -> str:
    """
    Retrieves an environment variable or returns default if not set.
    Raises an exception if not found and no default provided.

    Parameters:
        name (str): Environment variable name.
        default (Optional[str]): Default value if env var is not set.

    Returns:
        str: Environment variable value or default.
    """
    value = os.getenv(name)
    if value is None:
        if default is None:
            raise EnvironmentError(f"Required environment variable '{name}' not set.")
        return default
    return value


def is_valid_uuid(value: str) -> bool:
    """
    Validates if the provided string is a valid UUID.

    Parameters:
        value (str): String to validate as UUID.

    Returns:
        bool: True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def parse_uuid(value: str) -> Optional[uuid.UUID]:
    """
    Parses a string into a UUID object, returns None if invalid.

    Parameters:
        value (str): String to parse as UUID.

    Returns:
        Optional[uuid.UUID]: Parsed UUID or None.
    """
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def format_datetime_iso(dt: datetime) -> str:
    """
    Formats a datetime object to ISO 8601 string (UTC).

    Parameters:
        dt (datetime): Datetime object to format.

    Returns:
        str: ISO 8601 formatted string in UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def clean_text(text: str) -> str:
    """
    Cleans input text by removing extra whitespace and control characters.
    Useful for sanitizing queries or responses.

    Parameters:
        text (str): Input string to clean.

    Returns:
        str: Cleaned string.
    """
    if not text:
        return ""

    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', text)
   
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


async def async_repeat_retry(func, retries: int = 3, delay_sec: int = 2, *args, **kwargs):
    """
    Async utility to retry calling a coroutine function multiple times with delay on failure.

    Parameters:
        func: Async function to call.
        retries (int): Number of retry attempts.
        delay_sec (int): Delay between retries in seconds.
        *args, **kwargs: Arguments to pass to func.

    Returns:
        The return value of func if successful.

    Raises:
        Exception raised by func after all retries.
    """
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay_sec)
