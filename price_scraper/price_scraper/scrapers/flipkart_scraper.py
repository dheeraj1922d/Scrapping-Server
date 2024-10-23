import requests
from bs4 import BeautifulSoup

class FlipkartScraper:
    def get_price(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract price (modify according to the page structure)
        price = soup.find('div', {'class': '_30jeq3'}).get_text()
        return float(price.replace('₹', '').replace(',', '')) if price else None
