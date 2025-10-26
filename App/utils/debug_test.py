#!/usr/bin/env python3
"""Debug script to test firewall blocking/unblocking without UI"""

import sys
import os
import platform

# Add parent directory to path so we can import from App folder
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from firewall import block_app, unblock_app
from utils.app_manager import get_running_apps
from utils.settings_manager import load_settings, save_settings

def main():
    print("[DEBUG] Starting firewall test...")
    print(f"[DEBUG] OS: {platform.system()}")
    
    # Check admin rights
    if platform.system().lower() == "windows":
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"[DEBUG] Admin rights: {is_admin}")
        if not is_admin:
            print("[ERROR] Not running as admin!")
            return
    
    # Get running apps
    print("\n[DEBUG] Fetching running apps...")
    apps = get_running_apps()
    print(f"[DEBUG] Found {len(apps)} apps:")
    for app in apps[:5]:  # Show first 5
        print(f"  - {app['name']} ({app['path']})")
    
    if not apps:
        print("[ERROR] No apps found!")
        return
    
    # Test blocking the first app
    test_app = apps[0]
    print(f"\n[DEBUG] Testing block on: {test_app['name']}")
    print(f"[DEBUG] App path: {test_app['path']}")
    
    try:
        print("[DEBUG] Calling block_app()...")
        block_app(test_app['path'])
        print("[DEBUG] block_app() completed")
    except Exception as e:
        print(f"[ERROR] block_app failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test unblocking
    print(f"\n[DEBUG] Testing unblock on: {test_app['name']}")
    try:
        print("[DEBUG] Calling unblock_app()...")
        unblock_app(test_app['path'])
        print("[DEBUG] unblock_app() completed")
    except Exception as e:
        print(f"[ERROR] unblock_app failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[DEBUG] Test complete!")

if __name__ == "__main__":
    main()
