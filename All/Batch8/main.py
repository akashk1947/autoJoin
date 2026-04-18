import os
import subprocess

def launch_monitored_scripts():
    # Base directory
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    found_scripts = []

    # 1. Collect all paths first
    for root, dirs, files in os.walk(base_path):
        if "autojoin.py" in files:
            # We want the folder name (e.g., 'Farukh') to use as a title
            folder_name = os.path.basename(root)
            script_path = os.path.join(root, "autojoin.py")
            found_scripts.append((folder_name, root, script_path))

    print(f"[*] Found {len(found_scripts)} scripts. Launching windows...")

    # 2. Launch them
    for folder_name, folder_path, script_full_path in found_scripts:
        # Construct the Windows 'start' command
        # /D sets the directory, "title" sets the window name
        # 'cmd /k' keeps the window open even if the script crashes
        command = f'start "{folder_name}" /D "{folder_path}" cmd /k python autojoin.py'
        
        try:
            # shell=True is required to use the 'start' command
            subprocess.Popen(command, shell=True)
            print(f"  [>] Started: {folder_name}")
        except Exception as e:
            print(f"  [!] Failed to start {folder_name}: {e}")

    print("\n[+] All windows dispatched.")

if __name__ == "__main__":
    launch_monitored_scripts()