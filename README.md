# Web Page Archiver

A Git-like web page archival system that stores only deltas between versions.

## Features

- **Efficient Storage:** Stores only the differences between page versions, minimizing storage space.
- **HTTP Conditional Requests:** Uses `ETag` and `Last-Modified` headers to avoid downloading unchanged pages.
- **Ad and Tracker Stripping:** Removes common ad and tracker scripts from archived pages.
- **Asset Embedding:** Embeds CSS, JavaScript, and images directly into the HTML for a complete offline archive.
- **SQLite Backend:** Uses a simple and portable SQLite database to store all data.
- **Dockerized:** The entire application is containerized for easy deployment and management.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/web-page-archiver.git
   cd web-page-archiver
   ```

2. **Configure the archiver:**
   - Add the URLs you want to monitor to the `sites.json` file.
   - (Optional) Create a `.env` file to configure the subdomain limit:
     ```
     SUBDOMAIN_LIMIT=10
     ```

3. **Build and run the Docker containers:**
   ```bash
   docker-compose up --build
   ```

## Usage

- The archiver will automatically run every 15 minutes to fetch and archive the pages.
- The web interface will be available at `http://localhost:4444`.

## How It Works

The application consists of two main services:

- **`web`:** A Flask web server that provides a web interface to view the archived pages.
- **`archiver`:** A Python script that runs on a cron schedule to fetch and archive the pages.
