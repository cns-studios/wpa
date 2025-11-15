# Web Page Archiver

A Git-like web page archival system that stores only deltas between versions.

## Features

- **Efficient Storage:** Stores only the differences between page versions, minimizing storage space.
- **HTTP Conditional Requests:** Uses `ETag` and `Last-Modified` headers to avoid downloading unchanged pages.
- **Ad and Tracker Stripping:** Removes common ad and tracker scripts from archived pages.
- **Asset Embedding:** Embeds CSS, JavaScript, and images directly into the HTML for a complete offline archive.
- **SQLite Backend:** Uses a simple and portable SQLite database to store all data.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/web-page-archiver.git
   cd web-page-archiver
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Add URLs to `launch.py`:**
   Open `launch.py` and add the URLs you want to monitor to the `urls_to_monitor` list.

2. **Run the archiver:**
   ```bash
   python3 launch.py
   ```

   The archiver will fetch the pages, store them in the `my_archive.db` database, and print a summary of its actions.
