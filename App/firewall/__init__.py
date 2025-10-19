import platform

# Detect OS
OS_NAME = platform.system().lower()

# Dynamic import based on OS
if "windows" in OS_NAME:
    from .windows import block_app, unblock_app
elif "linux" in OS_NAME:
    from .linux import block_app, unblock_app
else:
    raise NotImplementedError(f"Unsupported OS: {OS_NAME}")
