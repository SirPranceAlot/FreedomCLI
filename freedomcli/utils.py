"""Utility functions for formatting and common operations."""


def format_time_delta(delta_seconds: float) -> str:
    """Format time delta into human-readable string."""
    if delta_seconds < 1:
        return f"{delta_seconds*1000:.0f}ms"
    elif delta_seconds < 60:
        return f"{delta_seconds:.1f}s"
    else:
        mins, secs = divmod(delta_seconds, 60)
        return f"{int(mins)}m {secs:.1f}s"


def format_file_size(size_bytes: int) -> str:
    """Format file size into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def clear_terminal():
    """Clear the terminal screen using ANSI escape codes."""
    print("\x1b[2J\x1b[H")