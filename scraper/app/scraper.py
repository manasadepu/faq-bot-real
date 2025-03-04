import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import re
import json

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Regular expression for finding emails
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    def extract_structured_data(self, soup, url):
        """Extract structured data from the page"""
        structured_data = {
            "title": soup.title.string if soup.title else "",
            "links": [],
            "forms": [],
            "emails": [],
            "dropdowns": [],
            "headings": [],
            "paragraphs": [],
            "lists": [],
            "tables": [],
            "images": [],
            "base_url": url
        }
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            if href.startswith('/'):
                if url.endswith('/'):
                    href = url + href[1:]
                else:
                    href = url + href
            
            structured_data["links"].append({
                "text": link.get_text(strip=True),
                "url": href
            })
        
        # Extract forms
        for form in soup.find_all('form'):
            form_data = {
                "action": form.get('action', ''),
                "method": form.get('method', 'get'),
                "inputs": []
            }
            
            for input_field in form.find_all(['input', 'textarea', 'select']):
                input_type = input_field.name
                if input_type == 'input':
                    input_type = input_field.get('type', 'text')
                
                input_data = {
                    "type": input_type,
                    "name": input_field.get('name', ''),
                    "id": input_field.get('id', ''),
                    "placeholder": input_field.get('placeholder', ''),
                    "value": input_field.get('value', '')
                }
                
                form_data["inputs"].append(input_data)
            
            structured_data["forms"].append(form_data)
        
        # Extract emails from text
        text_content = soup.get_text()
        emails = self.email_pattern.findall(text_content)
        structured_data["emails"] = list(set(emails))  # Remove duplicates
        
        # Extract dropdowns (select elements)
        for select in soup.find_all('select'):
            dropdown = {
                "name": select.get('name', ''),
                "id": select.get('id', ''),
                "options": []
            }
            
            for option in select.find_all('option'):
                dropdown["options"].append({
                    "value": option.get('value', ''),
                    "text": option.get_text(strip=True),
                    "selected": option.get('selected') is not None
                })
            
            structured_data["dropdowns"].append(dropdown)
        
        # Extract headings
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                structured_data["headings"].append({
                    "level": level,
                    "text": heading.get_text(strip=True)
                })
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            structured_data["paragraphs"].append(p.get_text(strip=True))
        
        # Extract lists
        for list_tag in soup.find_all(['ul', 'ol']):
            list_items = []
            for item in list_tag.find_all('li'):
                list_items.append(item.get_text(strip=True))
            
            structured_data["lists"].append({
                "type": list_tag.name,  # 'ul' or 'ol'
                "items": list_items
            })
        
        # Extract tables
        for table in soup.find_all('table'):
            table_data = {"headers": [], "rows": []}
            
            # Extract headers
            headers = table.find_all('th')
            if headers:
                table_data["headers"] = [th.get_text(strip=True) for th in headers]
            
            # Extract rows
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if cells:
                    table_data["rows"].append([cell.get_text(strip=True) for cell in cells])
            
            structured_data["tables"].append(table_data)
        
        # Extract images
        for img in soup.find_all('img', src=True):
            src = img['src']
            # Convert relative URLs to absolute
            if src.startswith('/'):
                if url.endswith('/'):
                    src = url + src[1:]
                else:
                    src = url + src
            
            structured_data["images"].append({
                "src": src,
                "alt": img.get('alt', '')
            })
        
        return structured_data
    
    def scrape_static(self, url, extract_structure=True):
        """Scrape static websites using requests and BeautifulSoup"""
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract structured data if requested
        structured_data = None
        if extract_structure:
            structured_data = self.extract_structured_data(soup, url)
        
        # Remove script and style elements for plain text extraction
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return {
            "text": text,
            "structured_data": structured_data
        }
    
    def scrape_dynamic(self, url, extract_structure=True, wait_time=5):
        """Scrape dynamic websites using Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=self.headers['User-Agent']
            )
            
            try:
                # Navigate to the URL
                page.goto(url, wait_until='networkidle')
                
                # Wait additional time if specified
                if wait_time > 0:
                    page.wait_for_timeout(wait_time * 1000)
                
                # Get page content
                page_content = page.content()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(page_content, 'html.parser')
                
                # Extract structured data if requested
                structured_data = None
                if extract_structure:
                    structured_data = self.extract_structured_data(soup, url)
                
                # Remove script and style elements for plain text extraction
                for script in soup(["script", "style"]):
                    script.extract()
                    
                # Get text
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return {
                    "text": text,
                    "structured_data": structured_data
                }
            finally:
                browser.close()
    
    def scrape_with_interaction(self, url, interactions=None, extract_structure=True):
        """
        Scrape websites with interactions using Playwright
        
        interactions: List of dictionaries with actions to perform, e.g.:
        [
            {"action": "click", "selector": "button.load-more"},
            {"action": "wait", "time": 2},
            {"action": "fill", "selector": "input#search", "value": "query"},
            {"action": "press", "key": "Enter"},
            {"action": "wait_for_selector", "selector": ".results"}
        ]
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=self.headers['User-Agent']
            )
            
            try:
                # Navigate to the URL
                page.goto(url, wait_until='networkidle')
                
                # Perform interactions if specified
                if interactions:
                    for interaction in interactions:
                        action = interaction.get("action")
                        
                        if action == "click":
                            page.click(interaction["selector"])
                        elif action == "wait":
                            page.wait_for_timeout(interaction["time"] * 1000)
                        elif action == "fill":
                            page.fill(interaction["selector"], interaction["value"])
                        elif action == "press":
                            page.press(interaction.get("selector", "body"), interaction["key"])
                        elif action == "wait_for_selector":
                            page.wait_for_selector(interaction["selector"])
                        elif action == "scroll":
                            # Scroll to bottom or by a specific amount
                            if interaction.get("to") == "bottom":
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            else:
                                page.evaluate(f"window.scrollBy(0, {interaction.get('amount', 300)})")
                
                # Get page content after interactions
                page_content = page.content()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(page_content, 'html.parser')
                
                # Extract structured data if requested
                structured_data = None
                if extract_structure:
                    structured_data = self.extract_structured_data(soup, url)
                
                # Remove script and style elements for plain text extraction
                for script in soup(["script", "style"]):
                    script.extract()
                    
                # Get text
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Optionally capture a screenshot
                if interaction and any(i.get("capture_screenshot") for i in interactions):
                    screenshot = page.screenshot()
                    return {
                        "text": text,
                        "structured_data": structured_data,
                        "screenshot": screenshot
                    }
                
                return {
                    "text": text,
                    "structured_data": structured_data
                }
            finally:
                browser.close()
