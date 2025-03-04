from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import Scraper
from crawler import WebsiteCrawler

app = FastAPI()

scraper = Scraper()

class ScrapeRequest(BaseModel):
    url: str
    max_pages: int = 100

@app.post("/scrape")
async def scrape_website(request: ScrapeRequest):
    try:
        # Use the crawler to scrape the website
        crawler = WebsiteCrawler(request.url, max_pages=request.max_pages)
        results = crawler.crawl()
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))