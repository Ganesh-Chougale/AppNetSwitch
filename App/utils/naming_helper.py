import platform
import ctypes
import re
from ctypes import wintypes


def parse_executable_name(exe_name: str) -> str:
    """
    Intelligently parse executable name to extract meaningful words.
    Examples:
    - RtkAudioService64.exe -> Realtek Audio Service
    - RAVBg64.exe -> Realtek Audio Console
    - mysqld.exe -> MySQL Server
    - RtkNGUI64.exe -> Realtek Audio Manager
    """
    # Remove .exe extension
    name = exe_name.replace('.exe', '').replace('.dll', '')
    
    # Known abbreviation mappings
    abbrev_map = {
        'rtk': 'Realtek',
        'rav': 'Realtek Audio',
        'mysql': 'MySQL',
        'svc': 'Service',
        'srv': 'Server',
        'ui': 'UI',
        'ux': 'Experience',
        'bg': 'Background',
        'gui': 'GUI',
        'ngui': 'Audio Manager',
    }
    
    # Try to split camelCase and snake_case
    # Insert space before uppercase letters (except at start)
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    # Replace underscores with spaces
    spaced = spaced.replace('_', ' ')
    # Remove numbers and special characters at the end
    spaced = re.sub(r'\d+$', '', spaced).strip()
    
    # Split into words
    words = spaced.split()
    
    # Process each word
    processed_words = []
    for word in words:
        word_lower = word.lower()
        
        # Check if word matches abbreviation
        matched = False
        for abbrev, full_form in abbrev_map.items():
            if word_lower == abbrev or word_lower.startswith(abbrev):
                processed_words.append(full_form)
                matched = True
                break
        
        # If no abbreviation match and word is meaningful (not just numbers/symbols)
        if not matched and word and not word.isdigit():
            # Capitalize first letter
            processed_words.append(word.capitalize())
    
    # Join and clean up
    result = ' '.join(processed_words)
    
    # Remove duplicates while preserving order
    seen = set()
    final_words = []
    for word in result.split():
        word_lower = word.lower()
        if word_lower not in seen:
            final_words.append(word)
            seen.add(word_lower)
    
    result = ' '.join(final_words)
    
    # Return original if parsing didn't help
    return result if result and len(result) > 2 else exe_name


def get_app_display_name(exe_path: str, fallback_name: str) -> str:
    """
    Extracts the product name from Windows executable metadata using Windows API.
    Falls back to intelligent parsing of the executable name if metadata is unavailable.
    """
    if platform.system().lower() != "windows":
        return fallback_name
    
    try:
        # Windows API functions
        GetFileVersionInfoSize = ctypes.windll.version.GetFileVersionInfoSizeW
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoW
        VerQueryValue = ctypes.windll.version.VerQueryValueW
        
        # Get version info size
        size = GetFileVersionInfoSize(exe_path, None)
        if size == 0:
            # No version info, try intelligent parsing
            return parse_executable_name(fallback_name)
        
        # Get version info
        version_info = ctypes.create_string_buffer(size)
        GetFileVersionInfo(exe_path, None, size, version_info)
        
        # Query for ProductName
        product_name_ptr = ctypes.c_wchar_p()
        product_name_len = wintypes.UINT()
        
        if VerQueryValue(version_info, r'\StringFileInfo\040904B0\ProductName', 
                        ctypes.byref(product_name_ptr), ctypes.byref(product_name_len)):
            product_name = product_name_ptr.value
            if product_name and product_name.strip() and product_name.lower() != 'unknown':
                return product_name.strip()
        
        # Query for FileDescription
        file_desc_ptr = ctypes.c_wchar_p()
        file_desc_len = wintypes.UINT()
        
        if VerQueryValue(version_info, r'\StringFileInfo\040904B0\FileDescription', 
                        ctypes.byref(file_desc_ptr), ctypes.byref(file_desc_len)):
            file_desc = file_desc_ptr.value
            if file_desc and file_desc.strip() and file_desc.lower() != 'unknown':
                return file_desc.strip()
    
    except Exception:
        pass
    
    # Fallback to intelligent parsing
    return parse_executable_name(fallback_name)
