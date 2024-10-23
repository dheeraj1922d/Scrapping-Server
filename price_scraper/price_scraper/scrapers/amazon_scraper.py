import requests
from bs4 import BeautifulSoup

class AmazonScraper:
    def get_price(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract price (modify according to the page structure)
        price = soup.find('span', {'class': 'a-price-whole'}).get_text()
        return float(price.replace(',', '')) if price else None
