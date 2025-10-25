"""
Application sorting functionality.
Provides various sorting options for the application list.
"""

def sort_apps(apps: list, sort_type: str, blocked_apps: set = None) -> list:
    """
    Sort apps based on the specified sort type.
    
    Args:
        apps: List of app dictionaries with 'name' and 'path' keys
        sort_type: Type of sorting to apply
        blocked_apps: Set of blocked app paths (for status sorting)
        
    Returns:
        Sorted list of apps
    """
    if not apps:
        return apps
    
    blocked_apps = blocked_apps or set()
    
    # Create a copy to avoid modifying the original list
    sorted_apps = apps.copy()
    
    if sort_type == "Name (A-Z)":
        sorted_apps.sort(key=lambda app: app.get("name", "").lower())
    
    elif sort_type == "Name (Z-A)":
        sorted_apps.sort(key=lambda app: app.get("name", "").lower(), reverse=True)
    
    elif sort_type == "Status (Blocked First)":
        # Blocked apps first, then allowed apps (both sorted by name)
        sorted_apps.sort(key=lambda app: (
            app.get("path", "") not in blocked_apps,  # False (blocked) comes before True (allowed)
            app.get("name", "").lower()
        ))
    
    elif sort_type == "Status (Allowed First)":
        # Allowed apps first, then blocked apps (both sorted by name)
        sorted_apps.sort(key=lambda app: (
            app.get("path", "") in blocked_apps,  # False (allowed) comes before True (blocked)
            app.get("name", "").lower()
        ))
    
    return sorted_apps


def get_sort_options() -> list:
    """
    Get available sorting options.
    
    Returns:
        List of sort option strings
    """
    return [
        "Name (A-Z)",
        "Name (Z-A)",
        "Status (Blocked First)",
        "Status (Allowed First)"
    ]


def get_default_sort() -> str:
    """
    Get the default sort option.
    
    Returns:
        Default sort option string
    """
    return "Name (A-Z)"
