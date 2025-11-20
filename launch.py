# launch.py
import json
from archiver import WebPageArchiver

def load_sites():
    """Load sites from sites.json."""
    with open('sites.json', 'r') as f:
        return json.load(f)

def save_sites(sites):
    """Save sites to sites.json."""
    with open('sites.json', 'w') as f:
        json.dump(sites, f, indent=4)

def main():
    """Main function to run the archiver."""
    archiver = WebPageArchiver('websites.db')
    sites_data = load_sites()

    print("=" * 70)
    print("Web Page Archiver - Launch")
    print("=" * 70)

    # Process each base URL
    for base_url, sub_urls in sites_data.items():
        if sub_urls is None:  # Discovery mode
            print(f"\n📄 Discovering and Archiving: {base_url}")
            result = archiver.archive_page(base_url, strip_ads=True, visited_urls=set(), max_depth=1, discovery_mode=True)
            print_status(result, archiver)

            # Update sites.json with discovered sub-URLs
            base_page_id = archiver._get_page_id(base_url)
            child_pages = archiver.get_child_pages(base_page_id)
            sites_data[base_url] = [child['url'] for child in child_pages]
            save_sites(sites_data)
            print(f"\n✅ {base_url} has been updated with discovered sub-URLs.")

        else:  # Update mode
            print(f"\n📄 Updating: {base_url}")
            urls_to_update = [base_url] + sub_urls
            for url in urls_to_update:
                print(f"\n🔗 Processing: {url}")
                result = archiver.archive_page(url, strip_ads=True, visited_urls=set(), max_depth=1, discovery_mode=False)

def print_status(result, archiver):
    """Prints the status of the archival process."""
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'archived':
        print(f"✓ Version: {result.get('version')} ({result.get('storage_type')})")
        print(f"  Original size: {result.get('original_size'):,} bytes")
        print(f"  Stored size: {result.get('stored_size'):,} bytes")
        print(f"  Compression: {result.get('compression_ratio')}")
        print(f"  Timestamp: {result.get('timestamp')}")
    elif result.get('status') == 'unchanged':
        print(f"○ {result.get('message')}")
        print(f"  Current version: {result.get('version')}")
    else:
        print(f"✗ {result.get('message', 'Unknown error')}")


    # Show all monitored pages
    print("\n" + "=" * 70)
    print("All Monitored Pages")
    print("=" * 70)

    pages = archiver.get_all_pages()
    for page in pages:
        print(f"\n{page['url']}")
        print(f"  ID: {page['id']} | Versions: {page['versions']} | Added: {page['created_at']}")

        history = archiver.get_version_history(page['url'])
        for ver in history[:5]:
            print(f"    v{ver['version']} [{ver['type']}] - {ver['timestamp']} ({ver['stored_size']:,} bytes)")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)

if __name__ == '__main__':
    main()
