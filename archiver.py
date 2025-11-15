import requests
import sqlite3
import gzip
import json
from datetime import datetime
from typing import Optional, Dict, Tuple
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
import hashlib


class WebPageArchiver:
    """
    A Git-like web page archival system that stores only deltas between versions.
    Uses HTTP conditional requests for efficient fetching.
    """
    
    # Common ad/tracker domains and patterns
    AD_DOMAINS = [
        'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
        'adservice.google.com', 'advertising.com', 'ads.', 'ad.',
        'facebook.net', 'analytics.', 'tracker.', 'pixel.'
    ]
    
    AD_CLASSES = [
        'ad', 'ads', 'advertisement', 'banner', 'sponsored',
        'promo', 'advert', 'ad-container', 'google-ad'
    ]
    
    def __init__(self, db_path: str = 'web_archive.db'):
        """Initialize the archiver with a database."""
        self.db_path = db_path
        self.dmp = diff_match_patch()
        self._init_database()
    
    def _init_database(self):
        """Create database schema for storing page versions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for tracking pages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for storing versions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                is_base BOOLEAN DEFAULT 0,
                content BLOB,  -- Compressed full content (base) or patch
                content_hash TEXT,
                etag TEXT,
                last_modified TEXT,
                http_status INTEGER,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (page_id) REFERENCES pages(id),
                UNIQUE(page_id, version_number)
            )
        ''')
        
        # Index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_page_versions 
            ON versions(page_id, version_number DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def _compress(self, data: str) -> bytes:
        """Compress string data using gzip."""
        return gzip.compress(data.encode('utf-8'))
    
    def _decompress(self, data: bytes) -> str:
        """Decompress gzip data to string."""
        return gzip.decompress(data).decode('utf-8')
    
    def _hash_content(self, content: str) -> str:
        """Generate SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _strip_ads(self, html: str) -> str:
        """Remove ads and tracking scripts from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts from ad domains
        for script in soup.find_all('script', src=True):
            if any(domain in script['src'] for domain in self.AD_DOMAINS):
                script.decompose()
        
        # Remove iframes from ad domains
        for iframe in soup.find_all('iframe', src=True):
            if any(domain in iframe['src'] for domain in self.AD_DOMAINS):
                iframe.decompose()
        
        # Remove elements with ad-related classes/ids
        for element in soup.find_all(class_=True):
            classes = element.get('class', [])
            if any(ad_class in ' '.join(classes).lower() for ad_class in self.AD_CLASSES):
                element.decompose()
        
        for element in soup.find_all(id=True):
            if any(ad_class in element.get('id', '').lower() for ad_class in self.AD_CLASSES):
                element.decompose()
        
        # Remove common ad containers
        for tag in ['ins', 'ad', 'advertisement']:
            for element in soup.find_all(tag):
                element.decompose()
        
        return str(soup)
    
    def fetch_page(self, url: str, etag: Optional[str] = None, 
                   last_modified: Optional[str] = None) -> Tuple[Optional[str], Dict]:
        """
        Fetch page with conditional GET request.
        
        Returns:
            Tuple of (content, metadata) where content is None if 304 Not Modified
        """
        headers = {
            'User-Agent': 'WebArchiver/1.0 (Educational Purpose)'
        }
        
        # Add conditional request headers
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            metadata = {
                'status': response.status_code,
                'etag': response.headers.get('ETag'),
                'last_modified': response.headers.get('Last-Modified'),
                'content_type': response.headers.get('Content-Type', '')
            }
            
            # 304 Not Modified - no content changed
            if response.status_code == 304:
                return None, metadata
            
            # Only process HTML content
            if 'text/html' not in metadata['content_type']:
                print(f"Warning: Non-HTML content type: {metadata['content_type']}")
            
            return response.text, metadata
            
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None, {'status': 0, 'error': str(e)}
    
    def _get_page_id(self, url: str) -> int:
        """Get or create page ID for URL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM pages WHERE url = ?', (url,))
        result = cursor.fetchone()
        
        if result:
            page_id = result[0]
        else:
            cursor.execute('INSERT INTO pages (url) VALUES (?)', (url,))
            page_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return page_id
    
    def _get_latest_version(self, page_id: int) -> Optional[Dict]:
        """Get the latest version metadata for a page."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version_number, etag, last_modified, content_hash
            FROM versions
            WHERE page_id = ?
            ORDER BY version_number DESC
            LIMIT 1
        ''', (page_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'version_number': result[0],
                'etag': result[1],
                'last_modified': result[2],
                'content_hash': result[3]
            }
        return None
    
    def archive_page(self, url: str, strip_ads: bool = True) -> Dict:
        """
        Archive a page, storing only the delta if it changed.
        
        Returns:
            Dictionary with archival status and details
        """
        page_id = self._get_page_id(url)
        latest = self._get_latest_version(page_id)
        
        # Fetch with conditional GET
        etag = latest['etag'] if latest else None
        last_modified = latest['last_modified'] if latest else None
        
        content, metadata = self.fetch_page(url, etag, last_modified)
        
        # 304 Not Modified - no change
        if content is None and metadata['status'] == 304:
            return {
                'status': 'unchanged',
                'message': 'Page not modified (HTTP 304)',
                'page_id': page_id,
                'version': latest['version_number'] if latest else 0
            }
        
        # Failed to fetch
        if content is None:
            return {
                'status': 'error',
                'message': metadata.get('error', 'Failed to fetch'),
                'page_id': page_id
            }
        
        # Strip ads if requested
        if strip_ads:
            content = self._strip_ads(content)
        
        # Check if content actually changed (hash comparison)
        content_hash = self._hash_content(content)
        if latest and latest['content_hash'] == content_hash:
            return {
                'status': 'unchanged',
                'message': 'Content hash unchanged (no actual change)',
                'page_id': page_id,
                'version': latest['version_number']
            }
        
        # Store the new version
        return self._store_version(page_id, content, metadata, latest)
    
    def _store_version(self, page_id: int, content: str, 
                       metadata: Dict, latest: Optional[Dict]) -> Dict:
        """Store a new version as base or delta."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        version_number = 1 if not latest else latest['version_number'] + 1
        is_base = (version_number == 1)
        
        if is_base:
            # Store full content for base version
            compressed_content = self._compress(content)
            storage_type = 'base'
        else:
            # Generate and store delta/patch
            old_content = self.get_version_content(page_id, latest['version_number'])
            patches = self.dmp.patch_make(old_content, content)
            patch_text = self.dmp.patch_toText(patches)
            compressed_content = self._compress(patch_text)
            storage_type = 'delta'
        
        content_hash = self._hash_content(content)
        
        cursor.execute('''
            INSERT INTO versions 
            (page_id, version_number, is_base, content, content_hash, 
             etag, last_modified, http_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            page_id, version_number, is_base, compressed_content, content_hash,
            metadata.get('etag'), metadata.get('last_modified'), metadata['status']
        ))
        
        conn.commit()
        conn.close()
        
        original_size = len(content.encode('utf-8'))
        compressed_size = len(compressed_content)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        return {
            'status': 'archived',
            'page_id': page_id,
            'version': version_number,
            'storage_type': storage_type,
            'original_size': original_size,
            'stored_size': compressed_size,
            'compression_ratio': f'{compression_ratio:.1f}%',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_version_content(self, page_id: int, version_number: int) -> Optional[str]:
        """
        Reconstruct content for a specific version by applying patches.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get base version
        cursor.execute('''
            SELECT content FROM versions
            WHERE page_id = ? AND is_base = 1
            ORDER BY version_number ASC
            LIMIT 1
        ''', (page_id,))
        
        base_result = cursor.fetchone()
        if not base_result:
            conn.close()
            return None
        
        content = self._decompress(base_result[0])
        
        # If requesting base version, return it
        if version_number == 1:
            conn.close()
            return content
        
        # Get all patches up to requested version
        cursor.execute('''
            SELECT version_number, content, is_base
            FROM versions
            WHERE page_id = ? AND version_number > 1 AND version_number <= ?
            ORDER BY version_number ASC
        ''', (page_id, version_number))
        
        patches_data = cursor.fetchall()
        conn.close()
        
        # Apply patches sequentially
        for ver_num, patch_data, is_base in patches_data:
            if is_base:
                # Another base version (shouldn't happen but handle it)
                content = self._decompress(patch_data)
            else:
                patch_text = self._decompress(patch_data)
                patches = self.dmp.patch_fromText(patch_text)
                content, success = self.dmp.patch_apply(patches, content)
                
                if not all(success):
                    print(f"Warning: Some patches failed for version {ver_num}")
        
        return content
    
    def get_version_history(self, url: str) -> list:
        """Get version history for a URL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.version_number, v.is_base, v.http_status, 
                   v.fetched_at, v.content_hash,
                   LENGTH(v.content) as stored_size
            FROM versions v
            JOIN pages p ON v.page_id = p.id
            WHERE p.url = ?
            ORDER BY v.version_number DESC
        ''', (url,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'version': row[0],
                'type': 'base' if row[1] else 'delta',
                'status': row[2],
                'timestamp': row[3],
                'hash': row[4][:16] + '...',  # Shortened hash
                'stored_size': row[5]
            })
        
        conn.close()
        return history
    
    def compare_versions(self, url: str, version1: int, version2: int) -> str:
        """Get a unified diff between two versions."""
        page_id = self._get_page_id(url)
        
        content1 = self.get_version_content(page_id, version1)
        content2 = self.get_version_content(page_id, version2)
        
        if not content1 or not content2:
            return "Error: Could not retrieve one or both versions"
        
        # Generate unified diff
        import difflib
        diff = difflib.unified_diff(
            content1.splitlines(keepends=True),
            content2.splitlines(keepends=True),
            fromfile=f'Version {version1}',
            tofile=f'Version {version2}',
            lineterm=''
        )
        
        return ''.join(diff)


# Example usage and testing
def main():
    """Demonstration of the web archiver."""
    
    archiver = WebPageArchiver('web_archive.db')
    
    # Example URLs to monitor
    test_urls = [
        'https://example.com',
        'https://news.ycombinator.com',
    ]
    
    print("=" * 70)
    print("Web Page Archival System - Demo")
    print("=" * 70)
    
    for url in test_urls:
        print(f"\n📄 Archiving: {url}")
        print("-" * 70)
        
        # First archive
        result = archiver.archive_page(url, strip_ads=True)
        print(f"Status: {result['status']}")
        
        if result['status'] == 'archived':
            print(f"Version: {result['version']} ({result['storage_type']})")
            print(f"Original size: {result['original_size']:,} bytes")
            print(f"Stored size: {result['stored_size']:,} bytes")
            print(f"Compression: {result['compression_ratio']}")
        
        # Show version history
        print("\n📚 Version History:")
        history = archiver.get_version_history(url)
        for ver in history:
            print(f"  v{ver['version']} [{ver['type']}] - {ver['timestamp']} "
                  f"({ver['stored_size']:,} bytes) - {ver['hash']}")
        
        print()
    
    print("\n" + "=" * 70)
    print("Demonstration: Monitoring for changes")
    print("=" * 70)
    
    # Simulate monitoring by fetching again
    test_url = test_urls[0]
    print(f"\n🔍 Re-checking: {test_url}")
    result = archiver.archive_page(test_url)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    # Demonstrate version retrieval
    if history:
        print(f"\n📖 Retrieving version 1 content (first 500 chars):")
        print("-" * 70)
        content = archiver.get_version_content(result['page_id'], 1)
        if content:
            print(content[:500])
            print("...")


if __name__ == '__main__':
    main()
