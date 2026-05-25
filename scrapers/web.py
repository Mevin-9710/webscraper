"""
Playwright automation script - launches a persistent headed Chrome browser with a profile.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from config_helper import load_profile_config, copy_dir_incremental


def main():
    # Load profile configuration from config.json or OS defaults
    src_profile_dir, src_profile_name, use_real_profile = load_profile_config()

    if use_real_profile:
        # We copy to a temp directory to bypass Chrome's SingletonLock
        profile_dir = os.path.join(os.path.dirname(__file__), "chrome-profile-temp")
        profile_name = src_profile_name

        # Prepare temporary profile
        import shutil

        temp_profile_path = os.path.join(profile_dir, src_profile_name)
        os.makedirs(temp_profile_path, exist_ok=True)

        # Copy Local State
        src_local_state = os.path.join(src_profile_dir, "Local State")
        if os.path.exists(src_local_state):
            try:
                shutil.copy2(src_local_state, os.path.join(profile_dir, "Local State"))
            except Exception:
                pass

        # Sync Profile folder (cross-platform copy_dir_incremental)
        src_profile_path = os.path.join(src_profile_dir, src_profile_name)
        try:
            copy_dir_incremental(
                src_profile_path,
                temp_profile_path,
                ["Cache*", "*Cache*", "Service Worker", "component_crx_cache"]
            )
        except Exception:
            pass

        # Clean locks
        for root, dirs, files in os.walk(profile_dir):
            for file in files:
                if "Singleton" in file or file == "LOCK":
                    try:
                        os.remove(os.path.join(root, file))
                    except OSError:
                        pass
    else:
        profile_dir = os.path.join(os.path.dirname(__file__), "chrome-profile")
        profile_name = None
        os.makedirs(profile_dir, exist_ok=True)

    playwright = sync_playwright().start()

    launch_args = []
    if profile_name:
        launch_args.append(f"--profile-directory={profile_name}")

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        channel="chrome" if use_real_profile else None,
        args=launch_args,
    )

    browser = context.browser

    profile_desc = f"{profile_dir} (Profile: {profile_name})" if profile_name else profile_dir
    print(f"Browser launched with profile at: {profile_desc}")
    print("Browser will stay open. Press Ctrl+C to exit.")

    try:
        input()
    except KeyboardInterrupt:
        print("\nClosing browser...")

    context.close()
    playwright.stop()


if __name__ == "__main__":
    main()