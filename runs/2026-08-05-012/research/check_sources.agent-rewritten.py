import re
import requests
import sys

def extract_urls(text):
    # Regex to match URLs in markdown: [text](url) or <url> or plain http/https links
    # Focus on common patterns: [text](url)
    pattern = r'\[.*?\]\((https?://[^\s)]+)\)'
    # Also catch plain urls starting with http/https
    plain_pattern = r'(?<!\( )(https?://[^\s<>"]+)'
    
    urls = re.findall(pattern, text)
    # Find all matches for plain patterns and filter out those already caught by the markdown link pattern
    plain_urls = re.findall(plain_pattern, text)
    
    # Use a set to avoid duplicates and maintain basic order by returning a list
    seen = set()
    all_urls = []
    for url in urls + plain_urls:
        if url not in seen:
            all_urls.append(url)
            seen.add(url)
    return all_urls

def validate_url(url):
    try:
        # Use HEAD request first for efficiency
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code >= 400:
            # Fallback to GET if HEAD is not allowed (405 Method Not Allowed)
            response = requests.get(url, allow_redirects=True, timeout=10)
        
        return response.status_code < 400
    except requests.RequestException:
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_sources.py <markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    urls = extract_urls(content)
    if not urls:
        # If no URLs are found, the condition "all are reachable" is vacuously true, 
        # but typically we should print the success marker.
        print("ALL_URLS_VALID")
        return

    all_valid = True
    for url in urls:
        if not validate_url(url):
            all_valid = False
            break
    
    if all_valid:
        print("ALL_URLS_VALID")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
