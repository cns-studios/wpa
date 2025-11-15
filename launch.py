# launch.py
from archiver import WebPageArchiver

# Initialize archiver
archiver = WebPageArchiver('websites.db')

import json

# List of URLs to monitor
with open('sites.json', 'r') as f:
    urls_to_monitor = json.load(f)

print("=" * 70)
print("Web Page Archiver - Launch")
print("=" * 70)

# Archive each URL
for url in urls_to_monitor:
    print(f"\n📄 Archiving: {url}")
    print("-" * 70)
    
    result = archiver.archive_page(url, strip_ads=True, visited_urls=set(), max_depth=1)
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'archived':
        print(f"✓ Version: {result['version']} ({result['storage_type']})")
        print(f"  Original size: {result['original_size']:,} bytes")
        print(f"  Stored size: {result['stored_size']:,} bytes")
        print(f"  Compression: {result['compression_ratio']}")
        print(f"  Timestamp: {result['timestamp']}")
    elif result['status'] == 'unchanged':
        print(f"○ {result['message']}")
        print(f"  Current version: {result['version']}")
    else:
        print(f"✗ {result['message']}")

# Show all monitored pages
print("\n" + "=" * 70)
print("All Monitored Pages")
print("=" * 70)

pages = archiver.get_all_pages()
for page in pages:
    print(f"\n{page['url']}")
    print(f"  ID: {page['id']} | Versions: {page['versions']} | Added: {page['created_at']}")
    
    # Show version history
    history = archiver.get_version_history(page['url'])
    for ver in history[:5]:  # Show last 5 versions
        print(f"    v{ver['version']} [{ver['type']}] - {ver['timestamp']} ({ver['stored_size']:,} bytes)")

print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
