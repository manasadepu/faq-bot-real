import urllib.robotparser
from urllib.parse import urlparse, urljoin
import time
import random
from scraper import Scraper
from collections import deque

class WebsiteCrawler:
    def __init__(self, base_url, max_pages=100, respect_robots=False, delay_range=(1, 3)):
        """
        Initialize the crawler
        
        Args:
            base_url: The starting URL and domain to crawl
            max_pages: Maximum number of pages to crawl
            respect_robots: Whether to respect robots.txt
            delay_range: Range of seconds to delay between requests (min, max)
        """
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self.delay_range = delay_range
        self.visited_urls = set()
        self.queue = deque([base_url])
        self.scraper = Scraper()
        self.results = []
        
        # Set up robots.txt parser
        self.robot_parser = urllib.robotparser.RobotFileParser()
        if self.respect_robots:
            robots_url = urljoin(base_url, "/robots.txt")
            try:
                self.robot_parser.set_url(robots_url)
                self.robot_parser.read()
            except Exception as e:
                print(f"Error reading robots.txt: {e}")
    
    def is_allowed(self, url):
        """Check if scraping the URL is allowed by robots.txt"""
        if not self.respect_robots:
            return True
        return self.robot_parser.can_fetch("*", url)
    
    def is_same_domain(self, url):
        """Check if the URL belongs to the same domain"""
        return urlparse(url).netloc == self.base_domain
    
    def normalize_url(self, url, source_url):
        """Convert relative URLs to absolute and normalize"""
        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            url = urljoin(source_url, url)
        
        # Remove fragments
        url = url.split('#')[0]
        
        # Ensure trailing slash consistency
        if url.endswith('/'):
            url = url[:-1]
            
        return url
    
    def should_crawl(self, url):
        """Determine if a URL should be crawled"""
        # Skip non-http(s) URLs
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Skip already visited URLs
        if url in self.visited_urls:
            return False
            
        # Skip URLs from different domains
        if not self.is_same_domain(url):
            return False
            
        # Skip URLs disallowed by robots.txt
        if not self.is_allowed(url):
            return False
            
        # Skip common non-content file types
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', 
                          '.zip', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
            
        return True
    
    def crawl(self):
        """Crawl the website starting from the base URL"""
        page_count = 0
        
        while self.queue and page_count < self.max_pages:
            # Get the next URL from the queue
            current_url = self.queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling {current_url} ({page_count + 1}/{self.max_pages})")
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            try:
                # Determine if the page is likely static or dynamic
                # This is a simple heuristic - you might want to improve it
                is_likely_dynamic = any(tech in current_url for tech in 
                                       ['#', 'vue', 'react', 'angular', 'spa', 'dashboard'])
                
                # Scrape the page
                if is_likely_dynamic:
                    result = self.scraper.scrape_dynamic(current_url)
                else:
                    result = self.scraper.scrape_static(current_url)
                
                # Store the result
                self.results.append({
                    "url": current_url,
                    "content": result
                })
                
                # Extract links from the page
                links = []
                if result["structured_data"] and "links" in result["structured_data"]:
                    links = [link["url"] for link in result["structured_data"]["links"]]
                
                # Process each link
                for link in links:
                    # Normalize the URL
                    normalized_link = self.normalize_url(link, current_url)
                    
                    # Check if we should crawl this URL
                    if self.should_crawl(normalized_link):
                        self.queue.append(normalized_link)
                
                # Increment page count
                page_count += 1
                
                # Random delay to be polite
                delay = random.uniform(self.delay_range[0], self.delay_range[1])
                time.sleep(delay)
                
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
        
        print(f"Crawling complete. Visited {len(self.visited_urls)} pages.")
        return self.results

def crawl_website(base_url, max_pages=100):
    """
    Crawl a website and return all scraped content
    
    Args:
        base_url: The starting URL and domain to crawl
        max_pages: Maximum number of pages to crawl
    
    Returns:
        List of dictionaries with URL and content
    """
    crawler = WebsiteCrawler(base_url, max_pages=max_pages)
    results = crawler.crawl()
    return results
