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
    folder_id = config.get("folder_id")
    scan_range = config.get("range", 50)
    templates = config.get("url_templates", [])
    output_file = config.get("output_file", "found_videos.csv")
    headers = config.get("headers", {})

    print(f"Scanning ID: {start_id} +/- {scan_range}")
    print(f"Fixed Folder: {folder_id}")

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Folder", "Type", "Working URL"])

        with requests.Session() as session:
            session.headers.update(headers)

            for video_id in range(start_id - scan_range, start_id + scan_range + 1):
                found_for_this_id = False

                # Loop through every URL template you provided
                for template in templates:
                    # Inject Folder ID and Video ID into the link
                    url = template.format(folder=folder_id, id=video_id)

                    try:
                        # Use stream=True to check headers without downloading
                        response = session.get(url, stream=True, timeout=2)

                        if response.status_code == 200:
                            # Identify the type based on the URL text
                            link_type = "Unknown"
                            if "recordedvideos" in url: link_type = "Recorded"
                            elif "livestream" in url: link_type = "Livestream"
                            elif "amazonaws" in url: link_type = "AWS Backup"

                            print(f"[+] FOUND: {video_id} ({link_type})")
                            writer.writerow([video_id, folder_id, link_type, url])
                            found_for_this_id = True
                            break # Found one working link, stop checking others for this ID

                    except Exception:
                        pass 

                if not found_for_this_id:
                    print(f"[-] Missing: {video_id}")

                time.sleep(0.1)

    print(f"\nScan complete. Results saved to {output_file}")

if __name__ == "__main__":
    scan()
