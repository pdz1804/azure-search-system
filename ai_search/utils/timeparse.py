from datetime import datetime

def parse_sql_datetime(s: str) -> datetime:
    """Parse 'YYYY-MM-DD HH:MM:SS' strings from Cosmos data."""
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")



