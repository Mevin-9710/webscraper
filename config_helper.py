import os
import json
import platform
import shutil
import fnmatch

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def get_default_chrome_profile():
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Profile 1")
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Profile 1")
    else:  # Linux
        return os.path.join(home, ".config", "google-chrome", "Profile 1")

def load_profile_config():
    """Load profile configuration from config.json, falling back to defaults by OS."""
    profile_path = None
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                profile_path = data.get("chrome_profile_path")
        except Exception:
            pass

    if profile_path:
        profile_path = os.path.expanduser(profile_path)
    else:
        profile_path = get_default_chrome_profile()

    src_profile_dir = os.path.dirname(profile_path)
    src_profile_name = os.path.basename(profile_path)
    use_real_profile = os.path.exists(profile_path)

    return src_profile_dir, src_profile_name, use_real_profile

def copy_dir_incremental(src, dest, ignore_patterns_list):
    """Recursively copy files from src to dest incrementally (cross-platform alternative to rsync)."""
    if not os.path.exists(dest):
        os.makedirs(dest, exist_ok=True)
    
    try:
        items = os.listdir(src)
    except Exception:
        return
        
    for item in items:
        should_ignore = False
        for pattern in ignore_patterns_list:
            if fnmatch.fnmatch(item, pattern):
                should_ignore = True
                break
        if should_ignore:
            continue
            
        s = os.path.join(src, item)
        d = os.path.join(dest, item)
        
        if os.path.isdir(s):
            copy_dir_incremental(s, d, ignore_patterns_list)
        else:
            if not os.path.exists(d) or os.path.getmtime(s) > os.path.getmtime(d) or os.path.getsize(s) != os.path.getsize(d):
                try:
                    shutil.copy2(s, d)
                except Exception:
                    pass
