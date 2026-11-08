import json;
import sys;
from pathlib import Path
import urllib.request;
import os;
import hashlib;

script_dir = Path(__file__).parent

def load_jurisdictions(config_path):
    try:
        with open(f'{config_path}', 'r', encoding='utf-8') as file:
            jurisdictions = json.load(file)
            print(f"Loaded {len(jurisdictions)} jurisdictions from '{config_path}'")
            return jurisdictions;
    except FileNotFoundError:
        sys.exit(f"ERROR - file '{config_path}' could not be found")
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR - Invalid JSON syntax: line {e.lineno}, column {e.colno}: {e.msg}")

def looks_like_pdf(file_bytes):
    return (file_bytes[:16]).startswith(b'%PDF-');

def download_pdf(jurisdiction):
    timeout_seconds = 10;
    file_bytes = b""
    bytes_downloaded = 0;
    jurisdiction_name = jurisdiction["name"]

    # Check for empty string
    if jurisdiction["document_url"] == "":
        print(f"{jurisdiction_name}: FAILED - document URL is empty!")
        return None;

    # Mask urllib as a user so we don't get 403s
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')]
    urllib.request.install_opener(opener)

    try:
        with urllib.request.urlopen(jurisdiction["document_url"], timeout=timeout_seconds) as response:
            # Check content & make sure it's a PDF
            if not 'application/pdf' in response.info()['content-type']:
                print(f"{jurisdiction_name}: FAILED - downloaded content for {jurisdiction_name} is not a PDF!")
                return None;

            # Start reading file
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                file_bytes += chunk;
                # Record size of file
                bytes_downloaded += len(chunk)

            if not looks_like_pdf(file_bytes):
                print(f"{jurisdiction_name}: FAILED - downloaded content for {jurisdiction_name} is not a PDF!")
                return None;

    except urllib.error.URLError as e:
        print(f"{jurisdiction_name}: FAILED - download timed out/errored for {jurisdiction_name}! {e}")
        return None;
    except FileNotFoundError:
        print(f"{jurisdiction_name}: FAILED - file not found for {jurisdiction_name}!")
        return None;
    except Exception as e:
        print(f"{jurisdiction_name}: FAILED - file not processed for {jurisdiction_name}! {e}")
        return None;

    # Make sure the bytes downloaded matches what we expect before writing
    if (bytes_downloaded != len(file_bytes)):
        print(f"{jurisdiction_name}: FAILED - downloaded byte count does not match collected content.")
        return None;

    # Return downloaded bytes
    return file_bytes

def save_pdf(file_bytes, output_dir, output_path, jurisdiction_name, jurisdiction_id):
    # Temp file
    temp_path = output_dir / f"{jurisdiction_id}_temp.pdf"

    try:
        # Make directory if it doesn't exist yet
        output_dir.mkdir(parents=True, exist_ok=True)
        # Write to temp file to check the file's byte size
        with open(temp_path, "wb") as file:
            file.write(file_bytes)

        # Time to check the file written
        if (len(file_bytes) != temp_path.stat().st_size):
            raise OSError(f"File size mismatch: expected {len(file_bytes)} bytes but saved {temp_path.stat().st_size} bytes instead!")

        # Remove _temp from name
        os.replace(temp_path, output_path)

    except OSError as e:
        print(f"{jurisdiction_name}: FAILED - could not save file. {e}")
        return False;
    
    else:
        # No errors, so success!        
        return True;

    finally:
        try:
            # Delete temp file
            temp_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"{jurisdiction_name}: WARNING - could not remove temporary file. {e}")

def compute_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def main():
    jurisdictions = load_jurisdictions("jurisdictions.json")
    download_counts = {"NEW": 0, "UNCHANGED": 0, "CHANGE_DETECTED": 0, "FAILED": 0}

    for jurisdiction in jurisdictions:
        # Set output directory & path
        OUTPUT_DIR = script_dir / "data" / "documents" / jurisdiction["id"]
        OUTPUT_PATH = OUTPUT_DIR / f"{jurisdiction["id"]}_zoning.pdf"

        # Grab this info once
        jurisdiction_name = jurisdiction["name"]
        jurisdiction_id = jurisdiction["id"]

        # Download PDF
        pdf_download = download_pdf(jurisdiction)

        # Check if nothing was downloaded
        if (pdf_download is None):
            download_counts["FAILED"] += 1;
            continue;

        # Grab hash
        pdf_download_hash = compute_hash(pdf_download)

        # Check hashes now, but only if the file exists
        if Path(OUTPUT_PATH).is_file():
            try:
                with open(OUTPUT_PATH, "rb") as file:
                    current_data = file.read()
                    if not looks_like_pdf(current_data):
                        print(f"{jurisdiction_name}: FAILED - previously downloaded content for {jurisdiction_name} is not a PDF!")
                        download_counts["FAILED"] += 1;
                        continue;
                    if pdf_download_hash == compute_hash(current_data):
                        print(f"{jurisdiction_name}: UNCHANGED - skipping file writing of {jurisdiction_name} as file has not changed")
                        download_counts["UNCHANGED"] += 1;
                        continue;
                    else:
                        print(f"{jurisdiction_name}: CHANGE_DETECTED - change detected in file of {jurisdiction_name}!")
                        download_counts["CHANGE_DETECTED"] += 1;
            except OSError as e:
                print(f"{jurisdiction_name}: FAILED - Failed to open/read file. {e}")
                download_counts["FAILED"] += 1;
                continue;
        # Save pdf as it doesn't exist
        elif (save_pdf(pdf_download, OUTPUT_DIR, OUTPUT_PATH, jurisdiction_name, jurisdiction_id)):
            print(f"{jurisdiction_name}: NEW - PDF saved!")
            download_counts["NEW"] += 1;
        else:
            download_counts["FAILED"] += 1;
        
    if not (sum(download_counts.values()) == len(jurisdictions)):
        print("ERROR - number of counted downloads does not match length of JSON input!")

    print(f"Number of new files: {download_counts['NEW']}")
    print(f"Number of unchanged files: {download_counts['UNCHANGED']}")
    print(f"Number of changes detected: {download_counts['CHANGE_DETECTED']}")
    print(f"Number of failed file checks: {download_counts['FAILED']}")
    print(f"Total number of files processed: {sum(download_counts.values())}")


if __name__ == "__main__":
    main()