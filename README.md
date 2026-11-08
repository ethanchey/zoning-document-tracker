# Michigan Zoning Document Tracker: a prototype

A small Python prototype that downloads zoning ordinance PDFs and compares them with previously saved documents to detect changes

I built this prototype in response to a research opportunity involving automated collection and tracking of zoning documents for data center sites. In this regard, it is unfinished; I built this simply to test my Python skills.

The code covers three manually configured Michigan jurisdictions:
- Dexter Township, Washtenaw County
- Webster Township, Washtenaw County
- Lyon Township, Roscommon County

While my code can handle downloading, validation, saving, and detecting changes, it does not include source discovery or an agentic pipeline.

## Features

- Loads jurisdictions and document URLs from a JSON file.
- Downloads documents and checks HTTP content type & PDF signature.
- Processes jurisdictions independently so handled failures do not stop the run.
- Writes new documents to a temporary file and verifies their saved size before replacing the destination.
- Compares document bytes using hashes and skips rewriting unchanged documents.
- Reports individual outcomes and summary counts.

## Requirements

- Python 3.12 or later (for formatted string literals)
- Internet access

## Project Structure

```text
zoning-tracker/
├── README.md
├── tracker.py
├── jurisdictions.json
└── data/
    └── documents/
        └── <jurisdiction_id>/
            └── <jurisdiction_id>_zoning.pdf
```

## Configuration

Create `jurisdictions.json` containing a list of jurisdiction objects.

```json
[
  {
    "id": "dexter_township_washtenaw_mi",
    "name": "Dexter Township",
    "document_url": "<direct zoning PDF URL>"
  }
]
```

Required:
- `id`: A unique, filesystem-safe identifier.
- `name`: The jurisdiction name used in status messages.
- `document_url`: The URL of the PDF to download.

Additional (unused) source documentation can be included:

```json
{
  "id": "dexter_township_washtenaw_mi",
  "name": "Dexter Township",
  "document_url": "<direct zoning PDF URL>",
  "county": "Washtenaw",
  "state": "MI",
  "official_source_page": "<official government source page>",
  "document_title": "Zoning Ordinance"
}
```

## Usage

From the directory containing `jurisdictions.json`, run:

```bash
python tracker.py
```

Other systems (like macOS devices), may require using `python3` instead.

## Outcomes

Each jurisdiction receives one outcome:

- `NEW`: No existing document was found, and the downloaded PDF was saved successfully.
- `UNCHANGED`: Downloaded content matches the existing document. No file is rewritten.
- `CHANGE_DETECTED`: Downloaded content differs from the existing document. The existing document is preserved; the new version is not saved yet.
- `FAILED`: Downloading, validation, reading, or saving failed.

e.g.:

```text
Dexter Township: UNCHANGED - existing document retained
Webster Township: NEW - PDF saved!
Lyon Township: FAILED - HTTP Error 403: Forbidden
```

Setup failures are labeled `ERROR`. Secondary issues, such as unsuccessful temporary-file cleanup, are labeled `WARNING`. The final summary counts each outcome and checks that the total matches the number of configured jurisdictions.

## Change Detection

The script computes a SHA-256 hash of the downloaded bytes and compares it with a hash of the existing local PDF. Identical hashes are treated as unchanged documents; different hashes indicate a change. Note that a different hash does not always imply new zoning policy; document structure, metadata, or elements can also modify the hash.

## AI Declaration

Artificial intelligence was used to turn the research project overview provided into a list of requirements for this project, as well as to help build this README.md file. No generative AI was used in the creation of tracker.py.