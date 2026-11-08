import json;
import sys;
from pathlib import Path
import urllib.request;

script_dir = Path(__file__).parent

def load_jurisdictions(config_path):
    try:
        with open(f'{config_path}', 'r', encoding='utf-8') as file:
            jurisdictions = json.load(file)
            print(f"File '{config_path}' opened successfully")
            return jurisdictions;
    except FileNotFoundError:
        sys.exit(f"Error: file '{config_path}' could not be found")
    except json.JSONDecodeError as e:
        sys.exit(f"Error: Invalid JSON syntax: line {e.lineno}, column {e.colno}: {e.msg}")

def download_pdf(jurisdiction):
    timeout_seconds = 10;
    bytes_downloaded = 0;

    # Check for empty string
    if jurisdiction["document_url"] == "":
        print(f"{jurisdiction["name"]}'s document URL is empty!")
        return 0;

    # Make folder if it doesn't exist
    output_dir = script_dir / "data" / "documents" / f"{jurisdiction["id"]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{jurisdiction["id"]}_zoning.pdf"

    # Mask urllib as a user so we don't get 403s
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')]
    urllib.request.install_opener(opener)

    try:
        with urllib.request.urlopen(jurisdiction["document_url"], timeout=timeout_seconds) as response:
            # Check content & make sure it's a PDF
            if not 'application/pdf' in response.info()['content-type']:
                print(f"{jurisdiction["name"]}: FAILURE. Error: download link for {jurisdiction["name"]} is not a PDF!")
                return 0;
            if not (file_bytes := response.read(16)).startswith(b'%PDF-'):
                print(f"{jurisdiction["name"]}: FAILURE. Error: download link for {jurisdiction["name"]} is not a PDF!")
                return 0; 

            # Start reading file
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                file_bytes += chunk;
                # Record size of file
                bytes_downloaded += len(chunk)

            # After download finishes, write to file
            with open(output_path, "wb") as file:
                file.write(file_bytes)

        # Make sure the bytes downloaded matches what we expect
        if (bytes_downloaded == Path(output_path).stat().st_size):
            # Make sure the file is readable
            with open(output_path, 'r', encoding='utf-8') as file:
                test_read = file.read()
            # No errors, so success!        
            print(f"{jurisdiction["name"]}: SUCCESS. File saved successfully to: {output_path} - {bytes_downloaded} bytes")
            return 1;
        print(f"{jurisdiction["name"]}: FAILURE. File size does not match expected size.")
        return 0;

    except urllib.error.URLError as e:
        print(f"{jurisdiction["name"]}: FAILURE. Error: download timed out/errored for {jurisdiction["name"]}! {e}")
        return 0;
    except FileNotFoundError:
        print(f"{jurisdiction["name"]}: FAILURE. Error: file not found for {jurisdiction["name"]}!")
        return 0;
    except Exception as e:
        print(f"{jurisdiction["name"]}: FAILURE. Error: file not processed for {jurisdiction["name"]}! {e}")
        return 0;


def main():
    jurisdictions = load_jurisdictions("jurisdictions.json")
    success_downloads = 0;

    for jurisdiction in jurisdictions:
        success_downloads += download_pdf(jurisdiction)

    print(f"Number of successful downloads: {success_downloads}")
    print(f"Number of failed downloads: {len(jurisdictions) - success_downloads}")


if __name__ == "__main__":
    main()