#!/usr/bin/env python3
"""Test script to verify firewall blocking/unblocking works"""

import sys
import os
import platform
import subprocess

# Add parent directory to path so we can import from App folder
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_netsh_commands():
    """Test if netsh commands work on Windows"""
    print("[TEST] Testing netsh commands...")
    
    # Test 1: List existing rules
    print("\n[TEST 1] Listing firewall rules...")
    try:
        result = subprocess.run(
            'netsh advfirewall firewall show rule name=all',
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        if result.returncode == 0:
            print("[PASS] netsh command works")
            # Count rules
            rule_count = result.stdout.count("Rule Name:")
            print(f"[INFO] Found {rule_count} firewall rules")
        else:
            print(f"[FAIL] netsh returned error: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test 2: Try to add a test rule
    print("\n[TEST 2] Adding a test firewall rule...")
    test_rule_name = "AppNetSwitch_TEST_12345"
    test_app_path = "C:\\Windows\\System32\\notepad.exe"
    
    try:
        cmd = (
            f'netsh advfirewall firewall add rule name="{test_rule_name}" '
            f'dir=out action=block program="{test_app_path}" enable=yes'
        )
        print(f"[DEBUG] Command: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
        
        if result.returncode == 0 or "Ok" in result.stdout:
            print("[PASS] Rule added successfully")
            
            # Test 3: Delete the test rule
            print("\n[TEST 3] Deleting the test rule...")
            delete_cmd = f'netsh advfirewall firewall delete rule name="{test_rule_name}"'
            result = subprocess.run(delete_cmd, capture_output=True, text=True, shell=True, timeout=5)
            
            if result.returncode == 0 or "Ok" in result.stdout:
                print("[PASS] Rule deleted successfully")
            else:
                print(f"[FAIL] Delete failed: {result.stderr}")
        else:
            print(f"[FAIL] Add rule failed: {result.stderr}")
            print(f"[INFO] stdout: {result.stdout}")
    except Exception as e:
        print(f"[ERROR] {e}")

def test_firewall_module():
    """Test the firewall module"""
    print("\n\n[TEST] Testing firewall module...")
    
    try:
        from app.core.firewall import block_app, unblock_app
        print("[PASS] Firewall module imported successfully")
        
        # Test with a dummy path
        test_path = "C:\\Windows\\System32\\calc.exe"
        print(f"\n[TEST] Attempting to block: {test_path}")
        
        try:
            block_app(test_path)
            print("[INFO] block_app() executed without error")
            
            print(f"\n[TEST] Attempting to unblock: {test_path}")
            unblock_app(test_path)
            print("[INFO] unblock_app() executed without error")
        except Exception as e:
            print(f"[ERROR] Firewall operation failed: {e}")
            import traceback
            traceback.print_exc()
    except ImportError as e:
        print(f"[ERROR] Failed to import firewall module: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("AppNetSwitch Firewall Test Suite")
    print("=" * 60)
    
    os_name = platform.system().lower()
    print(f"[INFO] OS: {os_name}")
    
    if os_name == "windows":
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"[INFO] Admin rights: {is_admin}")
        
        if not is_admin:
            print("\n[WARNING] Not running as admin - some tests may fail")
            print("Please run this script as Administrator for full testing")
        
        test_netsh_commands()
        test_firewall_module()
    else:
        print("[ERROR] This test is designed for Windows")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
