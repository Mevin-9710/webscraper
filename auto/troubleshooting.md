# Automation & Troubleshooting Guide

This document compiles the major technical hurdles encountered during the development of this web scraper, specifically regarding Google Chrome profile automation, cross-platform persistence, and security restrictions. Refer to this guide to resolve profile-related and session errors.

---

## 1. Google Chrome Singleton Locks
### Problem
When Chrome is active, it creates lock files (`SingletonLock`, `SingletonCookie`, `SingletonSocket`, `LOCK`) in the user data directory. Launching Chrome via automation on the active profile fails with:
```
Failed to create a ProcessSingleton for your profile directory. This usually means that the profile is already in use by another instance of Chromium.
```

### Solution
1. **Incremental Sync to Temp Folder**: We copy the profile folder to a temporary directory (`chrome-profile-temp`) inside the workspace root.
2. **Lock Purging**: Before launching, the script recursively walks the temporary folder and deletes any file matching `Singleton*` or named `LOCK`.
3. **Implementation**: Handled automatically in `base_scraper.py` and `config_helper.py`.

---

## 2. Syncing Hangs (Unix Sockets & Named Pipes)
### Problem
When copying the active Chrome profile directory, python’s standard file utilities (e.g. `shutil.copy2`) block and hang indefinitely.
- **Cause**: Active profiles contain UNIX domain sockets (such as `SingletonSocket`), FIFOs, and symbolic links. Standard copy utilities attempt to read from them, causing the script to wait forever for input.

### Solution
Modified `copy_dir_incremental` to check the file mode using `os.lstat` before reading or copying.
- **Rules**: Explicitly skip symbolic links, socket files, named pipes (FIFOs), and special block/character devices. Copy only regular files and subdirectories.

---

## 3. Slow Startup & Disk Space Constraints (< 100MB)
### Problem
Full Google Chrome user profiles can exceed **900 MB** of data. Copying this:
1. Takes **10–15 seconds** to boot.
2. Fails immediately on disk space constraints if the target drive has low available storage (e.g. < 100MB).

### Solution
We implemented a strict **Session Allowlist**. Instead of copying the entire profile directory, we only sync files crucial for active authentication sessions:
- `Local Storage/` (HTML5 LocalStorage databases)
- `Network/` (modern cookie storage)
- `Cookies` (legacy cookie database)
- `Preferences` and `Secure Preferences` (profile state and configurations)
- `Login Data` and `Web Data` (saved credentials and form histories)

**Outcome**: Reduced profile copy size from **877 MB to 1.98 MB** and startup copy latency from **12 seconds to under 50ms**.

---

## 4. Cross-Platform Directory Paths
### Problem
User profile directories are located in vastly different default locations depending on the OS, and config files might use absolute or relative paths with home shortcuts (e.g. `~`).

### Solution
Created `load_profile_config()` in `config_helper.py`:
1. Expands user paths natively using `os.path.expanduser`.
2. Automatically falls back to standard defaults if the configuration path doesn't exist:
   - **Linux**: `~/.config/google-chrome/Profile 1`
   - **macOS**: `~/Library/Application Support/Google/Chrome/Profile 1`
   - **Windows**: `~/AppData/Local/Google/Chrome/User Data/Profile 1`

---

## 5. Chrome 136+ Remote Debugging Restrictions
### Problem
Starting with Google Chrome 136, you cannot launch Chrome with `--remote-debugging-port` using the default user data directory. It exits immediately with:
```
DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.
```
However, using a non-default directory (like our temp folder) prevents the Linux system keyring (GNOME Keyring/KWallet) from decrypting the copied login session cookies because the application path/identity has changed. The browser starts logged out.

### Solution
1. Use the temporary data directory to bypass the debugging check and allow the browser to launch successfully.
2. Direct the automation tool (`playwright-cli`) to navigate to the website's sign-in page (e.g. `indiehackers.com/sign-in`).
3. Since Chrome still has access to the credentials database (`Login Data`), the form fields (Email and Password) will be autofilled by the browser.
4. Programmatically click the "Sign In" button to re-authenticate and restore the logged-in session automatically.
