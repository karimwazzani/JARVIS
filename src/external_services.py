import requests
import logging

logger = logging.getLogger(__name__)

def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        return f"${float(data['price']):,.2f}"
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
        return "No disponible"

def get_weather(city="Buenos Aires"):
    try:
        # Usamos wttr.in que es gratuito y no requiere API KEY para usos simples
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url, timeout=10)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return "No disponible"

def get_top_news():
    try:
        # Usamos un feed de noticias general si no tenemos API Key, 
        # o podemos usar una API de noticias gratuita si el usuario provee key.
        # Por ahora, simularemos o buscaremos un feed RSS simple.
        # Una opción es usar 'newsapi.org' si el usuario la agrega luego.
        # Como no tenemos Key, intentaremos un resumen muy básico o pediremos al LLM que lo genere si tuviera búsqueda.
        # Por ahora, dejaremos el hook para ser llenado o usaremos un scraping ligero de un RSS.
        url = "https://news.google.com/rss?hl=es-419&gl=AR&ceid=AR:es-419"
        import xml.etree.ElementTree as ET
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        news_items = []
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            news_items.append(title)
        return news_items
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []
