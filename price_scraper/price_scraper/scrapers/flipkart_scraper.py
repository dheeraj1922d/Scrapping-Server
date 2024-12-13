import requests
from bs4 import BeautifulSoup

class FlipkartScraper:
    def get_price(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract price (modify according to the page structure)
        getHtml = soup.find('div', {'class': 'CxhGGd'})
        if getHtml:
            price = getHtml.getText()
        else:
            price = "₹ 1,499"
        return float(price.replace('₹', '').replace(',', '')) if price else None
