# bookmarks/services/metadata_extractor.py
import httpx
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import asyncio
from typing import Dict, Any, Optional, Tuple
import ssl

# Configure logging
logger = logging.getLogger(__name__)

class MetadataExtractor:
    """
    Service for extracting metadata from URLs including title, description,
    preview image, favicon, and content type detection.
    """
    
    def __init__(self, timeout = 10):
        """
        Initialize the extractor with configurable timeout.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.url_validator = URLValidator()
    
    async def extract_metadata(self, url):
        """
        Asynchronously extract metadata from a given URL.
        
        Args:
            url: The URL to extract metadata from
            
        Returns:
            Dictionary containing extracted metadata
        """
        # Validate URL
        try:
            self.url_validator(url)
        except ValidationError:
            logger.error(f"Invalid URL provided: {url}")
            return {
                'title': None,
                'description': None,
                'preview_image': None,
                'favicon': None,
                'content_type': None,
                'error': 'Invalid URL format'
            }
        
        try:
            # Create SSL context that ignores certificate errors for cases where sites have invalid certs
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Use httpx for async HTTP requests with a timeout
            async with httpx.AsyncClient(timeout=self.timeout, verify=ssl_context) as client: # set httpx.A... to client
                # Asynch sends an HTTP request to the specified url using the client object.
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code != 200:
                    logger.warning(f"Non-200 response ({response.status_code}) from URL: {url}")
                    return {
                        'title': None,
                        'description': None,
                        'preview_image': None,
                        'favicon': None,
                        'content_type': None,
                        'error': f'Request failed with status {response.status_code}'
                    }
                
                # Check content type from headers
                content_type_header = response.headers.get('content-type', '').lower()
                detected_type = self._detect_content_type(url, content_type_header)
                
                # For non-HTML content, return minimal metadata
                if detected_type != 'article' and 'text/html' not in content_type_header:
                    return {
                        'title': self._extract_title_from_url(url),
                        'description': None,
                        'preview_image': None, 
                        'favicon': self._get_favicon_from_domain(url),
                        'content_type': detected_type
                    }
                
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract metadata
                title = self._extract_title(soup, url)
                description = self._extract_description(soup)
                preview_image = self._extract_preview_image(soup, url)
                favicon = self._extract_favicon(soup, url)
                
                # Final content type detection with HTML content info
                content_type = self._refine_content_type(detected_type, soup)
                
                return {
                    'title': title,
                    'description': description,
                    'preview_image': preview_image,
                    'favicon': favicon,
                    'content_type': content_type
                }
                
        except httpx.TimeoutException:
            logger.warning(f"Request timed out for URL: {url}")
            return {
                'title': self._extract_title_from_url(url),
                'description': None,
                'preview_image': None,
                'favicon': self._get_favicon_from_domain(url),
                'content_type': None,
                'error': 'Request timed out'
            }
        except Exception as e:
            logger.exception(f"Error extracting metadata from {url}: {str(e)}")
            return {
                'title': self._extract_title_from_url(url),
                'description': None,
                'preview_image': None,
                'favicon': self._get_favicon_from_domain(url),
                'content_type': None,
                'error': str(e)
            }
    
    def _extract_title(self, soup, url):
        """Extract page title from HTML"""
        # Try Open Graph title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Try Twitter card title
        twitter_title = soup.find('meta', {'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content'].strip()
        
        # Try HTML title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Fallback to URL-based title
        return self._extract_title_from_url(url)
    
    def _extract_title_from_url(self, url):
        """Generate a title from the URL when no title is found"""
        parsed_url = urlparse(url)
        
        # Extract the last meaningful part of the path
        path_parts = [p for p in parsed_url.path.split('/') if p]
        if path_parts:
            # Replace hyphens and underscores with spaces and capitalize
            page_name = path_parts[-1].replace('-', ' ').replace('_', ' ')
            # Remove file extensions if present
            page_name = re.sub(r'\.\w+$', '', page_name)
            if page_name:
                return page_name.capitalize()
        
        # Fallback to domain name
        domain = parsed_url.netloc
        return domain
    
    def _extract_description(self, soup):
        """Extract page description from HTML"""
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try Twitter card description
        twitter_desc = soup.find('meta', {'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content'].strip()
        
        # Try meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try to extract from first paragraph
        first_p = soup.find('p')
        if first_p and first_p.text:
            # Limit to reasonable length
            desc = first_p.text.strip()
            return desc[:300] + ('...' if len(desc) > 300 else '')
        
        return None
    
    def _extract_preview_image(self, soup, url):
        """Extract preview image URL from HTML"""
        # Try Open Graph image
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            return self._make_absolute_url(og_img['content'], url)
        
        # Try Twitter card image
        twitter_img = soup.find('meta', {'name': 'twitter:image'})
        if twitter_img and twitter_img.get('content'):
            return self._make_absolute_url(twitter_img['content'], url)
        
        # Look for a large image in the page
        main_img = None
        min_size = 100  # Minimum dimensions to consider
        
        # Find images with width and height attributes
        for img in soup.find_all('img', src=True):
            width = img.get('width')
            height = img.get('height')
            
            if width and height:
                try:
                    width, height = int(width), int(height)
                    if width >= min_size and height >= min_size:
                        main_img = img
                        break
                except (ValueError, TypeError):
                    pass
        
        # If found, return the image URL
        if main_img and main_img.get('src'):
            return self._make_absolute_url(main_img['src'], url)
        
        # Fallback: just get the first image of reasonable size
        for img in soup.find_all('img', src=True):
            if not img.get('src').endswith(('.ico', '.svg')) and 'logo' not in img.get('src').lower():
                return self._make_absolute_url(img['src'], url)
        
        return None
    
    def _extract_favicon(self, soup, url):
        """Extract favicon URL from HTML"""
        # Check for link tags that specify favicon
        for link in soup.find_all('link', rel=True):
            if any(rel in link.get('rel') for rel in ['icon', 'shortcut icon']):
                if link.get('href'):
                    return self._make_absolute_url(link['href'], url)
        
        # Fallback to default favicon location
        return self._get_favicon_from_domain(url)
    
    def _get_favicon_from_domain(self, url):
        """Generate default favicon URL from domain"""
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
    
    def _make_absolute_url(self, url_path, base_url):
        """Convert relative URLs to absolute URLs"""
        if url_path.startswith(('http://', 'https://')):
            return url_path
        
        parsed_base = urlparse(base_url)
        
        if url_path.startswith('//'):
            # Protocol-relative URL
            return f"{parsed_base.scheme}:{url_path}"
        
        if url_path.startswith('/'):
            # Root-relative URL
            return f"{parsed_base.scheme}://{parsed_base.netloc}{url_path}"
        
        # Path-relative URL
        base_path = parsed_base.path
        if not base_path.endswith('/'):
            base_path = '/'.join(base_path.split('/')[:-1]) + '/'
        
        return f"{parsed_base.scheme}://{parsed_base.netloc}{base_path}{url_path}"
    
    def _detect_content_type(self, url, content_type_header):
        """
        Detect content type based on URL and content-type header
        
        Returns one of: 'article', 'video', 'image', 'audio', 'document', 'unknown'
        """
        # Check URL patterns for common platforms
        url_lower = url.lower()
        
        # YouTube
        if any(pattern in url_lower for pattern in ['youtube.com/watch', 'youtu.be/', 'youtube.com/shorts']):
            return 'video'
        
        # TikTok
        if 'tiktok.com' in url_lower:
            return 'video'
        
        # Instagram
        if 'instagram.com' in url_lower:
            if '/p/' in url_lower:
                return 'image'
            if '/reel/' in url_lower:
                return 'video'
        
        # Twitter/X
        if any(pattern in url_lower for pattern in ['twitter.com', 'x.com']):
            return 'social'
        
        # Reddit
        if 'reddit.com' in url_lower:
            return 'social'
        
        # Check file extensions for media types
        path = urlparse(url).path.lower()
        
        # Images
        if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            return 'image'
        
        # Videos
        if path.endswith(('.mp4', '.webm', '.mov', '.avi')):
            return 'video'
        
        # Audio
        if path.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
            return 'audio'
        
        # Documents
        if path.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx')):
            return 'document'
        
        # Check content type header
        if 'image/' in content_type_header:
            return 'image'
        if 'video/' in content_type_header:
            return 'video'
        if 'audio/' in content_type_header:
            return 'audio'
        if any(doc_type in content_type_header for doc_type in ['application/pdf', 'application/msword', 'application/vnd.ms']):
            return 'document'
        
        # Default for HTML content
        if 'text/html' in content_type_header:
            return 'article'
        
        return 'unknown'
    
    def _refine_content_type(self, initial_type, soup):
        """
        Refine content type detection using HTML content analysis
        """
        if initial_type != 'article' and initial_type != 'unknown':
            return initial_type
        
        # Check for video embeds
        video_elements = soup.find_all(['video', 'iframe'])
        for video in video_elements:
            # Check for common video platforms in iframes
            if video.name == 'iframe' and video.get('src'):
                src = video['src'].lower()
                if any(platform in src for platform in ['youtube', 'vimeo', 'dailymotion']):
                    return 'video'
            
            # Check for HTML5 video element
            if video.name == 'video':
                return 'video'
        
        # Check if the page seems to be primarily an image
        if soup.find('meta', {'property': 'og:type', 'content': 'image'}):
            return 'image'
        
        # Check if the page seems to be primarily social media content
        social_meta = soup.find('meta', {'property': 'og:site_name'})
        if social_meta and social_meta.get('content'):
            site_name = social_meta['content'].lower()
            if site_name in ['twitter', 'instagram', 'facebook', 'reddit', 'linkedin']:
                return 'social'
        
        # Default to article for HTML content
        return 'article'


# Function to use in views directly
async def extract_url_metadata(url):
    """
    Convenience function to extract metadata from a URL.
    
    Args:
        url: The URL to extract metadata from
        
    Returns:
        Dictionary containing extracted metadata
    """
    extractor = MetadataExtractor()
    return await extractor.extract_metadata(url)


# For synchronous contexts (like Django views that aren't async)
def extract_url_metadata_sync(url):
    """
    Synchronous wrapper for the async metadata extractor
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(extract_url_metadata(url))
    finally:
        loop.close()