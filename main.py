import requests
import time
import csv
import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found.")
        exit()
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def scan():
    config = load_config()
    start_id = config.get("start_id")
    # We now take a list of folders or a range to check
    current_folder = config.get("folder_id") 
    scan_range = config.get("range", 2000) # Default to large range
    templates = config.get("url_templates", [])
    output_file = config.get("output_file", "all_videos.csv")
    headers = config.get("headers", {})

    print(f"--- STARTING MASSIVE SCAN ---")
    print(f"Video IDs: {start_id} to {start_id + scan_range}")
    print(f"Starting Folder: {current_folder} (Will auto-adjust)")

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Video ID", "Folder ID", "Type", "Stream URL"])

        with requests.Session() as session:
            session.headers.update(headers)

            # Loop through a HUGE range of video IDs
            for video_id in range(start_id, start_id + scan_range + 1):
                found_flag = False
                
                # ADAPTIVE FOLDER LOGIC:
                # We check the 'current' folder first. 
                # If that fails, we quickly check neighbor folders (current-1, current+1, current+2)
                # If we find a video in a new folder, we update 'current_folder' to stick to it.
                
                # Define which folders to check for THIS video ID
                folders_to_check = [current_folder, current_folder + 1, current_folder - 1, current_folder + 2]
                
                for folder_try in folders_to_check:
                    if found_flag: break # Stop if we already found it

                    for template in templates:
                        url = template.format(folder=folder_try, id=video_id)
                        
                        try:
                            # Fast check (HEAD request or stream=True)
                            response = session.get(url, stream=True, timeout=1.5)
                            
                            if response.status_code == 200:
                                # Determine type
                                link_type = "Recorded" if "recordedvideos" in url else "Livestream"
                                if "amazonaws" in url: link_type = "AWS Backup"

                                print(f"[+] FOUND: Video {video_id} | Folder {folder_try} | {link_type}")
                                writer.writerow([video_id, folder_try, link_type, url])
                                
                                # CRITICAL: If the folder changed (e.g. from 645 to 646),
                                # update 'current_folder' so the next video checks 646 first!
                                if folder_try != current_folder:
                                    print(f"    >>> Switching main folder to {folder_try}")
                                    current_folder = folder_try
                                
                                found_flag = True
                                break # Found correct template

                        except Exception:
                            pass
                
                if not found_flag:
                    # Optional: Print only every 10 misses to keep logs clean
                    if video_id % 10 == 0:
                        print(f"[-] Scanned {video_id}... (No hit)")

                # Very short delay to speed up processing
                time.sleep(0.05)

    print(f"\nScan complete. Check {output_file}")

if __name__ == "__main__":
    scan()
