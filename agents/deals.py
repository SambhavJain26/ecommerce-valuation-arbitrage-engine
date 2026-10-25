from pydantic import BaseModel
from typing import List, Dict, Self, Optional
from bs4 import BeautifulSoup
import re
import feedparser
from tqdm import tqdm
import requests
import time

feeds = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/c238/Automotive/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
    "https://www.dealnews.com/c196/Home-Garden/?rss=1",
]

def extract(html_snippet: str) -> str:
    """
    Use Beautiful Soup to clean up this HTML snippet and extract useful text
    """
    if not html_snippet:
        return ""
    soup = BeautifulSoup(html_snippet, 'html.parser')
    snippet_div = soup.find('div', class_='snippet summary')
    
    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, 'html.parser').get_text()
        description = re.sub('<[^<]+?>', '', description)
        result = description.strip()
    else:
        result = soup.get_text(strip=True)
    return result.replace('\n', ' ')

class ScrapedDeal:
    """
    A class to represent a Deal retrieved from an RSS feed
    """
    category: str
    title: str
    summary: str
    url: str
    details: str
    features: str

    def __init__(self, entry: Dict[str, str]):
        """
        Populate this instance based on the provided dict
        """
        self.title = entry.get('title', 'Deal Listing')
        self.summary = extract(entry.get('summary', ''))
        links = entry.get('links', [])
        self.url = links[0]['href'] if links and 'href' in links[0] else entry.get('link', '')
        self.details = ""
        self.features = ""

        if self.url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                resp = requests.get(self.url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    content_sec = soup.find('div', class_='content-section')
                    content = content_sec.get_text() if content_sec else ''
                    content = content.replace('\nmore', '').replace('\n', ' ').strip()
                    if "Features" in content:
                        parts = content.split("Features", 1)
                        self.details = parts[0].strip()
                        self.features = parts[1].strip()
                    else:
                        self.details = content
                else:
                    self.details = self.summary
            except Exception:
                self.details = self.summary
        else:
            self.details = self.summary

    def __repr__(self):
        """
        Return a string to describe this deal
        """
        return f"<{self.title}>"

    def describe(self):
        """
        Return a longer string to describe this deal for use in calling a model
        """
        return f"Title: {self.title}\nDetails: {self.details.strip()}\nFeatures: {self.features.strip()}\nURL: {self.url}"

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        """
        Retrieve all deals from the selected RSS feeds
        """
        deals = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    try:
                        deals.append(cls(entry))
                    except Exception:
                        continue
                    time.sleep(0.3)
            except Exception:
                continue
        return deals

class Deal(BaseModel):
    """
    A class to Represent a Deal with a summary description
    """
    product_description: str
    price: float
    url: str

class DealSelection(BaseModel):
    """
    A class to Represent a list of Deals
    """
    deals: List[Deal]

class Opportunity(BaseModel):
    """
    A class to represent a possible opportunity: a Deal where we estimate
    it should cost more than it is being offered
    """
    deal: Deal
    estimate: float
    discount: float
