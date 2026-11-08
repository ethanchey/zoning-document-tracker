import json;
import sys;
from pathlib import Path
import urllib.request;
import os;

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
    jurisdiction_name = jurisdiction["name"]

    # Check for empty string
    if jurisdiction["document_url"] == "":
        print(f"{jurisdiction_name}'s document URL is empty!")
        return None;

    # Mask urllib as a user so we don't get 403s
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')]
    urllib.request.install_opener(opener)

    try:
        with urllib.request.urlopen(jurisdiction["document_url"], timeout=timeout_seconds) as response:
            # Check content & make sure it's a PDF
            if not 'application/pdf' in response.info()['content-type']:
                print(f"{jurisdiction_name}: FAILURE. Error: download link for {jurisdiction_name} is not a PDF!")
                return None;
            if not (file_bytes := response.read(16)).startswith(b'%PDF-'):
                print(f"{jurisdiction_name}: FAILURE. Error: download link for {jurisdiction_name} is not a PDF!")
                return None; 

            # Increment bytes_downloaded first
            bytes_downloaded += len(file_bytes)

            # Start reading file
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                file_bytes += chunk;
                # Record size of file
                bytes_downloaded += len(chunk)

    except urllib.error.URLError as e:
        print(f"{jurisdiction_name}: FAILURE. Error: download timed out/errored for {jurisdiction_name}! {e}")
        return None;
    except FileNotFoundError:
        print(f"{jurisdiction_name}: FAILURE. Error: file not found for {jurisdiction_name}!")
        return None;
    except Exception as e:
        print(f"{jurisdiction_name}: FAILURE. Error: file not processed for {jurisdiction_name}! {e}")
        return None;

    # Make sure the bytes downloaded matches what we expect before writing
    if (bytes_downloaded != len(file_bytes)):
        print(f"{jurisdiction_name}: FAILURE. Downloaded byte count does not match collected content.")
        return None;

    # Return downloaded bytes
    return file_bytes

def save_pdf(file_bytes, jurisdiction_id, jurisdiction_name):
    # Set directory & path
    output_dir = script_dir / "data" / "documents" / jurisdiction_id
    output_path = output_dir / f"{jurisdiction_id}_zoning.pdf"
    # Temp file
    temp_path = output_dir / f"{jurisdiction_id}_zoning_temp.pdf"

    try:
        # Make directory if it doesn't exist yet
        output_dir.mkdir(parents=True, exist_ok=True)
        # Write to temp file to check the file's byte size
        with open(temp_path, "wb") as file:
            file.write(file_bytes)

        # Time to check the file written
        if (len(file_bytes) != temp_path.stat().st_size):
            raise OSError(f"{jurisdiction_name}: ERROR. Saved file size mismatch: expected {len(file_bytes)} bytes but saved {temp_path.stat().st_size} bytes instead!")

        # Remove _temp from name
        os.replace(temp_path, output_path)

    except OSError as e:
        print(f"{jurisdiction_name}: ERROR. Could not save file. {e}")
        return False;
    
    else:
        # No errors, so success!        
        print(f"{jurisdiction_name}: SUCCESS. File saved successfully to: {output_path} - {len(file_bytes)} bytes")
        return True;

    finally:
        try:
            # Delete temp file
            temp_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"{jurisdiction_name}: WARNING. Could not remove temporary file. {e}")


def main():
    jurisdictions = load_jurisdictions("jurisdictions.json")
    success_downloads = 0;

    for jurisdiction in jurisdictions:
        pdf_download = download_pdf(jurisdiction)

        # If download did not fail AND save_pdf went well
        if (pdf_download is not None and save_pdf(pdf_download, jurisdiction["id"], jurisdiction["name"])):
            success_downloads += 1;
        

    print(f"Number of successful downloads: {success_downloads}")
    print(f"Number of failed downloads: {len(jurisdictions) - success_downloads}")


if __name__ == "__main__":
    main()