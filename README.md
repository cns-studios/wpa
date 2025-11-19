# Web Page Archiver

A Git-like web page archival system that stores only deltas between versions, providing an efficient and scalable solution for tracking website changes over time.

## Features

- **Efficient Delta Storage:** Instead of storing full copies of each page version, the archiver stores only the differences (deltas) between them. This significantly reduces storage requirements, especially for frequently updated sites.
- **HTTP Conditional Requests:** The archiver uses `ETag` and `Last-Modified` headers to avoid re-downloading pages that have not changed, minimizing bandwidth usage and improving performance.
- **Ad and Tracker Stripping:** A built-in mechanism removes common ad and tracker scripts from archived pages, providing a cleaner and more secure offline reading experience.
- **Automatic Asset Embedding:** All external assets, such as CSS, JavaScript, and images, are automatically embedded into the HTML as data URIs. This creates a complete, self-contained offline archive of each page.
- **SQLite Backend:** The system uses a simple and portable SQLite database to store all page data, including versions, metadata, and deltas.
- **Dockerized and Automated:** The entire application is containerized for easy deployment and management. The archiver runs on an automated cron schedule, ensuring that websites are regularly checked for updates.
- **Web Interface:** A Flask-based web interface allows you to view archived pages, compare versions, and monitor the status of all tracked sites.

## Technology Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Containerization:** Docker, Docker Compose
- **Libraries:**
  - `requests` for HTTP requests
  - `BeautifulSoup` for HTML parsing
  - `diff-match-patch` for generating deltas
  - `gzip` for data compression

## How It Works

The application is divided into two main services:

- **`web`:** A Flask web server that provides a user-friendly interface to view the archived pages.
- **`archiver`:** A Python script that runs on a cron schedule (e.g., every 15 minutes) to fetch and archive the pages listed in `sites.json`.

When the `archiver` runs, it performs the following steps for each URL:
1. It sends a conditional HTTP request to check if the page has been modified since the last backup.
2. If the page has changed, it downloads the new content and strips out any ads or trackers.
3. It generates a "delta" by comparing the new version with the last archived version.
4. This delta is then compressed and stored in the SQLite database.

This delta-based approach ensures that only the changes are stored, making the system highly efficient.

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

## Roadmap

- [ ] **Improved diff visualization:** Implement a more user-friendly side-by-side diff view in the web interface.
- [ ] **Full-text search:** Add the ability to search the content of all archived pages.
- [ ] **User authentication:** Add a login system to protect the web interface.
- [ ] **Support for more content types:** Add support for archiving PDFs, images, and other file types.
