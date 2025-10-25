"""
Real-time application searching functionality.
Provides case-insensitive search across app names and paths.
"""

def search_apps(apps: list, search_query: str) -> list:
    """
    Filter apps based on search query (case-insensitive).
    
    Args:
        apps: List of app dictionaries with 'name' and 'path' keys
        search_query: Search string to filter by
        
    Returns:
        Filtered list of apps matching the search query
    """
    if not search_query or not search_query.strip():
        return apps
    
    query = search_query.lower().strip()
    
    filtered_apps = []
    for app in apps:
        app_name = app.get("name", "").lower()
        app_path = app.get("path", "").lower()
        
        # Search in both name and path
        if query in app_name or query in app_path:
            filtered_apps.append(app)
    
    return filtered_apps


def highlight_search_match(text: str, search_query: str) -> str:
    """
    Highlight matching text in search results (for future UI enhancement).
    
    Args:
        text: Original text
        search_query: Search query to highlight
        
    Returns:
        Text with HTML highlighting (for QLabel rich text)
    """
    if not search_query or not search_query.strip():
        return text
    
    # Case-insensitive replacement with highlighting
    import re
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f"<b><u>{m.group(0)}</u></b>", text)
    
    return highlighted
