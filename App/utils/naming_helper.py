import platform
import ctypes
from ctypes import wintypes


def get_app_display_name(exe_path: str, fallback_name: str) -> str:
    """
    Extracts the product name from Windows executable metadata using Windows API.
    Falls back to the executable name if metadata is unavailable.
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
            return fallback_name
        
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
    
    return fallback_name
