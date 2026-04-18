"""Web scraping functions for URL content extraction."""

# Standard library imports
import re

# Third-party imports
import requests

# Local imports
from freedomcli.constants import console

# Check for optional scraping dependencies
try:
    from bs4 import BeautifulSoup
    import html2text
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False


def scrape_url(url: str, timeout: int = 30) -> tuple:
    """
    Scrape web content from a URL and convert to readable text/markdown.
    
    Args:
        url: The URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        tuple: (success: bool, content: str or error_message: str)
    """
    if not HAS_SCRAPING:
        return False, "Web scraping dependencies not installed. Run: pip install beautifulsoup4 html2text"
    
    try:
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Set user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the webpage
        with console.status(f"[bold cyan]Fetching content from {url}...[/bold cyan]"):
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Handle non-HTML content
        if 'application/json' in content_type:
            return True, f"```json\n{response.text}\n```"
        elif 'text/plain' in content_type:
            return True, response.text
        elif 'text/html' not in content_type and 'application/xhtml' not in content_type:
            return False, f"Unsupported content type: {content_type}"
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
            element.decompose()
        
        # Remove SVG and excessive images (keep main content images)
        for svg in soup.find_all('svg'):
            svg.decompose()
        
        # Convert to markdown using html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True  # Ignore images in markdown conversion
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines
        
        # Get the main content or fallback to body
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            markdown_content = h.handle(str(main_content))
        else:
            markdown_content = h.handle(response.text)
        
        # Clean up excessive whitespace
        lines = [line.rstrip() for line in markdown_content.split('\n')]
        markdown_content = '\n'.join(lines)
        
        # Remove excessive blank lines (more than 2 consecutive)
        while '\n\n\n\n' in markdown_content:
            markdown_content = markdown_content.replace('\n\n\n\n', '\n\n\n')
        
        # Add metadata header
        title = soup.find('title')
        title_text = title.get_text().strip() if title else url
        
        result = f"# Web Content: {title_text}\n\n"
        result += f"**Source:** {url}\n\n"
        result += "---\n\n"
        result += markdown_content.strip()
        
        return True, result
        
    except requests.exceptions.Timeout:
        return False, f"Request timed out after {timeout} seconds"
    except requests.exceptions.RequestException as e:
        return False, f"Error fetching URL: {str(e)}"
    except Exception as e:
        return False, f"Error processing webpage: {str(e)}"


def is_url(text: str) -> bool:
    """Check if text contains a URL pattern."""
    url_pattern = r'https?://[^\s]+'
    return bool(re.search(url_pattern, text))


def extract_urls(text: str) -> list:
    """Extract all URLs from text."""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)