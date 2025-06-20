import requests
from bs4 import BeautifulSoup
import re
from colorama import Fore, Style, init
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import tkinter as tk
from tkinter import messagebox
import os

init(autoreset=True)

STORE_URLS = [
    "https://store.playstation.com/it-it/product/",
    "https://store.playstation.com/tr-tr/product/",
    "https://store.playstation.com/en-in/product/",    
    "https://store.playstation.com/en-za/product/",
    "https://store.playstation.com/en-ae/product/",
    "https://store.playstation.com/en-gb/product/",
    "https://store.playstation.com/de-ch/product/",
    "https://store.playstation.com/en-au/product/",
    "https://store.playstation.com/en-ca/product/",
    "https://store.playstation.com/en-il/product/",
    "https://store.playstation.com/es-mx/product/",
    "https://store.playstation.com/en-nz/product/",
    "https://store.playstation.com/en-hk/product/",
    "https://store.playstation.com/ja-jp/product/",
    "https://store.playstation.com/en-us/product/",
    "https://store.playstation.com/en-id/product/",
    "https://store.playstation.com/pt-br/product/",
    "https://store.playstation.com/es-ar/product/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

known_languages = [
    "italiano", "english", "francese", "spanish", "portuguese", "deutsch", "nederlands", "svenska", "danish", "norwegian", "finnish", "russian", "polski", "čeština", "magyar", "română", "slovenčina", "български", "hrvatski", "srpski", "slovenski", "ukrainian", "العربية", "עברית", "हिन्दी", "ภาษาไทย", "tiếng việt", "bahasa indonesia", "filipino", "malay", "korean", "中文", "日本語", "rusский", "български", "hrvatski", "srpski", "slovenski", "ukrainian", "العربية", "עברית", "हिन्दी", "ภาษาไทย", "tiếng việt", "bahasa indonesia", "filipino", "malay", "korean", "中文", "日本語"
]

lang_regex = re.compile(r'\b(' + '|'.join(known_languages) + r')\b', re.IGNORECASE)

# Dizionario con i tassi di cambio rispetto all'EURO
EXCHANGE_RATES = {
    "TRY": 0.029,  # Lira turca
    "INR": 11.00,  # Rupia indiana    
    "ZAR": 0.049,  # Rand sudafricano
    "AED": 0.25,   # Dirham UAE
    "GBP": 1.17,   # Sterlina britannica
    "CHF": 1.04,   # Franco svizzero
    "AUD": 0.57,   # Dollaro australiano
    "CAD": 0.68,   # Dollaro canadese
    "ILS": 0.25,   # Shekel israeliano
    "MXN": 0.054,  # Peso messicano
    "NZD": 0.53,   # Dollaro neozelandese
    "HKD": 0.12,   # Dollaro di Hong Kong
    "JPY": 0.062,  # Yen giapponese
    "USD": 0.92,   # Dollaro USA
    "IDR": 0.059,  # Rupia indonesiana
    "BRL": 0.15,   # Real brasiliano
    "ARS": 0.001   # Peso argentino
}

sinonimi_lingue = {
    "italiano": [
        "italiano", "italian", "italienisch", "italiana", "italienne",
        "italien", "italienische", "italienisch (italien)", "italiano (italia)",
        "italian (italy)", "italien (italie)", "italienisch (italien)", "italian (italien)", "italiano (italy)",
        "イタリア",  # Giapponese
        "이탈리아",  # Coreano
        "意大利",    # Cinese semplificato
        "義大利",    # Cinese tradizionale
        "Италия",   # Russo
        "İtalyanca" # Turco
        "Italiensk",  # Danese
        "Italienisch", # Tedesco
        "Italien",    # Svedese
    ],
    "inglese": [
        "inglese", "english", "englisch", "anglais", "inglês", "inglés"
    ],
    "tedesco": [
        "tedesco", "deutsch", "alemão", "alemán", "allemand"
    ],
    "francese": [
        "francese", "french", "français", "francês", "französisch"
    ],
    "spagnolo": [
        "spagnolo", "spanish", "español", "espanhol", "spanisch"
    ],
    "portoghese": [
        "portoghese", "portuguese", "português", "portugiesisch"
    ],
    "giapponese": [
        "giapponese", "japanese", "japonais", "japonês", "japanisch"
    ],
    "cinese": [
        "cinese", "chinese", "chinesisch", "chinês", "chinois"
    ],
    "olandese": [
        "olandese", "dutch", "nederlands", "neerlandês", "holländisch"
    ],
    "polacco": [
        "polacco", "polish", "polonês", "polonais", "polnisch"
    ],
    # aggiungi altre lingue se vuoi
}

def extract_languages(soup):
    # Cerca direttamente i tag con gli attributi data-qa specifici
    audio_tag = soup.find(attrs={"data-qa": "gameInfo#releaseInformation#voice-value"})
    screen_tag = soup.find(attrs={"data-qa": "gameInfo#releaseInformation#subtitles-value"})

    # Estrai e pulisci le lingue
    audio_langs = []
    screen_langs = []
    if audio_tag and audio_tag.text.strip():
        audio_langs = [l.strip() for l in audio_tag.text.split(",") if l.strip()]
    if screen_tag and screen_tag.text.strip():
        screen_langs = [l.strip() for l in screen_tag.text.split(",") if l.strip()]

    return audio_langs, screen_langs

def extract_price_and_currency(price_str, store_url=None):
    if price_str == 'N/A':
        return None, None

    price_str = price_str.strip()

    currency_symbols = {
        '€': 'EUR', 
        '$': 'USD', 
        '£': 'GBP', 
        '¥': 'JPY', 
        '₹': 'INR', 
        'R$': 'BRL', 
        'A$': 'AUD',
        'HK$': 'HKD', 
        'CA$': 'CAD', 
        'NZ$': 'NZD', 
        'CHF': 'CHF', 
        'AED': 'AED', 
        'MXN': 'MXN',
        'TL': 'TRY', 
        'TRY': 'TRY', 
        '₺': 'TRY', 
        'ILS': 'ILS',
        'Rs.': 'INR', 
        'Rs': 'INR', 
        '₨': 'INR', 
        'ARS$': 'ARS', 
        'Rp': 'IDR', 
        'IDR': 'IDR',
        'kr': 'SEK', 
        'Kr.': 'DKK', 
        'Kr': 'SEK', 
        'US$' : 'USD', 
        'MX$': 'MXN', 
        'NZ$': 'NZD',
    }

    price_patterns = [
        r'(A\$)\s*([0-9.,]+)',
        r'(NZ\$)\s*([0-9.,]+)',
        r'(CA\$)\s*([0-9.,]+)',
        r'(US\$)\s*([0-9.,]+)',
        r'([0-9.,]+)\s*([A-Za-z₹£$€¥₨₺]+)',      # 29.99 USD, 29,99 €, 29.99 ₺
        r'([A-Za-z₹£$€¥₨₺]+)\s*([0-9.,]+)',      # USD 29.99, € 29,99, ₺ 29.99
        r'([₹£$€¥₨₺])\s*([0-9.,]+)',             # $ 29.99, ₺ 29.99
        r'Rp\s*([0-9.,]+)',                      # Rp 299.000 (Indonesia)
        r'R\$\s*([0-9.,]+)',                     # R$ 299,99 (Brasile)
        r'HK\$\s*([0-9.,]+)',                    # HK$ 299.99 (Hong Kong)
        r'₺\s*([0-9.,]+)',                       # ₺ 299,99 (Turchia)
        r'₹\s*([0-9.,]+)',                       # ₹ 1,999.00 (India)
        r'Rs\.*\s*([0-9.,]+)',                   # Rs. 1,999.00 (India)
        r'([0-9.,]+)\s*₹',                       # 1,999.00 ₹ (India)
        r'(A\$)\s*([0-9.,]+)',                   # A$ 19.99 → AUD
        r'(NZ\$)\s*([0-9.,]+)',                  # NZ$ 24.99 → NZD

        
    ]

    for pattern in price_patterns:
        match = re.search(pattern, price_str)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                price = groups[0]
                if store_url:
                    if '/tr-tr/' in store_url:
                        currency_symbol = 'TRY'
                    elif '/en-in/' in store_url:
                        currency_symbol = 'INR'
                    elif '/en-id/' in store_url:
                        currency_symbol = 'IDR'
                    elif '/pt-br/' in store_url:
                        currency_symbol = 'BRL'
                    elif '/ja-jp/' in store_url:
                        currency_symbol = 'JPY'
                    elif '/en-au/' in store_url:
                        currency_symbol = 'AUD'
                    elif '/en-nz/' in store_url:
                        currency_symbol = 'NZD'
                    elif '/en-ca/' in store_url:
                        currency_symbol = 'CAD'
                    elif '/en-us/' in store_url:
                        currency_symbol = 'USD'
                    else:
                        currency_symbol = None
                else:
                    currency_symbol = None
            else:
                if groups[0].replace(',', '').replace('.', '').isdigit():
                    price, currency_symbol = groups
                else:
                    currency_symbol, price = groups

            # Se il simbolo è "$" e lo store è noto, correggi la valuta
            if currency_symbol == '$' and store_url:
                    if '/en-au/' in store_url:
                        currency_symbol = 'AUD'
                    elif '/en-nz/' in store_url:
                        currency_symbol = 'NZD'
                    elif '/en-ca/' in store_url:
                        currency_symbol = 'CAD'
                    elif '/en-us/' in store_url:
                        currency_symbol = 'USD'

            price = price.strip()
            # Gestione separatori decimali
            if currency_symbol == 'INR':
                # Per INR: rimuovi tutte le virgole (migliaia), non toccare il punto
                price = price.replace(',', '')
            else:
                if ',' in price and '.' in price:
                    if price.find(',') < price.find('.'):
                        price = price.replace(',', '')
                    else:
                        price = price.replace('.', '').replace(',', '.')
                elif ',' in price:
                    price = price.replace(',', '.')

            try:
                return float(price), currency_symbols.get(currency_symbol, currency_symbol)
            except ValueError:
                continue

    return None, None

def get_exchange_rate(currency):
    """Restituisce il tasso di cambio per una data valuta."""
    if currency == 'EUR':
        return 1.0
    return EXCHANGE_RATES.get(currency)

def fetch_game_info(game_id):
    results = []
    for store_url in STORE_URLS:
        url = f"{store_url}{game_id}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            results.append({'store': store_url, 'title': 'N/A', 'price': 'N/A', 'price_eur': 'N/A', 'audio_languages': [], 'screen_languages': [], 'cover': None})
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Titolo
        title = 'N/A'
        h1_tag = soup.find('h1', {'data-qa': 'mfe-game-title#name'})
        if h1_tag and h1_tag.text.strip():
            title = h1_tag.text.strip()
        else:
            span_tag = soup.find('span', class_="psw-m-b-5 psw-t-title-l psw-t-size-8 psw-l-line-break-word")
            if span_tag and span_tag.text.strip():
                title = span_tag.text.strip()
            else:
                title_tag = soup.find('title')
                if title_tag and title_tag.text.strip():
                    title = title_tag.text.replace("su PlayStation™Store", "").replace("| Acquista online", "").strip(" -|")

        # Prezzo
        price_tag = soup.find('span', {'data-qa': 'mfeCtaMain#offer0#finalPrice'})
        price = price_tag.text.strip() if price_tag else 'N/A'

        # Conversione in euro
        price_value, currency = extract_price_and_currency(price)
        price_eur = 'N/A'
        if price_value and currency:
            rate = get_exchange_rate(currency)
            if rate:
                price_eur = round(price_value * rate, 2)

        # Lingue audio e a schermo
        audio_langs, screen_langs = extract_languages(soup)

        # Copertina
        cover_url = None
        # 1. Prova con <img> classico
        img_tag = soup.find('img', src=lambda x: x and 'image.api.playstation.com' in x)
        if img_tag and img_tag.get('src'):
            cover_url = img_tag['src']
        else:
            # 2. Prova con JSON-LD
            script_ld = soup.find('script', type='application/ld+json')
            if script_ld:
                try:
                    data_ld = json.loads(script_ld.string)
                    if isinstance(data_ld, dict) and "image" in data_ld:
                        cover_url = data_ld["image"]
                except Exception:
                    pass
        # Rimuovi la query string se presente
        if cover_url and "?w=54&thumb=true" in cover_url:
            cover_url = cover_url.split("?w=54&thumb=true")[0]

        results.append({
            'store': store_url,
            'title': title,
            'price': price,
            'price_eur': price_eur,
            'audio_languages': audio_langs,
            'screen_languages': screen_langs,
            'cover': cover_url
        })
    return results

def search_generic(query, max_results=5):
    """Cerca qualsiasi gioco nel PlayStation Store"""
    try:
        base_url = "https://store.playstation.com/it-it/search/"
        search_url = f"{base_url}{query.replace(' ', '%20')}"
        
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        products = soup.find_all('a', {'class': 'psw-link psw-content-link'})
        
        results = []
        
        for i, product in enumerate(products):
            if i >= max_results:
                break
                
            # Extract product ID from href
            href = product.get('href', '')
            product_id = href.split('/product/')[-1] if '/product/' in href else None
            
            # Extract title
            title_element = product.find('span', {'data-qa': re.compile(r'product-name')})
            title = title_element.get_text(strip=True) if title_element else "N/A"
            
            # Extract price
            price_element = product.find('span', {'data-qa': re.compile(r'display-price')})
            price = price_element.get_text(strip=True) if price_element else "N/A"
            
            # Extract platform
            platform_element = product.find('span', {'data-qa': re.compile(r'game-art#tag0')})
            platform = platform_element.get_text(strip=True) if platform_element else "N/A"
            
            # Extract image URL
            img_element = product.find('img', {'data-qa': re.compile(r'game-art#image#image')})
            image_url = img_element.get('src') if img_element else "N/A"
            
            # Build full link
            link = "https://store.playstation.com" + href if href.startswith('/') else href
            
            if product_id and title != "N/A":
                results.append({
                    'product_id': product_id,
                    'title': title,
                    'price': price,
                    'platform': platform,
                    'image_url': image_url,
                    'link': link
                })
        
        return results
    
    except Exception as e:
        print(f"{Fore.RED}Errore durante la ricerca generica: {e}{Style.RESET_ALL}")
        return None

def mostra_ricerca_generica():
    print(f"{Fore.CYAN}{'🟦'*20}")
    print(f"{Fore.YELLOW}🔍 Ricerca generica nel PlayStation Store{Style.RESET_ALL}")
    
    query = input(f"{Fore.YELLOW}🎮 Inserisci il nome del gioco da cercare: {Fore.WHITE}").strip()
    if not query:
        print(f"{Fore.RED}❗ Nessun termine di ricerca inserito.{Style.RESET_ALL}")
        return

    results = search_generic(query, max_results=5)
    if not results:
        print(f"{Fore.RED}❌ Nessun risultato trovato per '{query}'.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}📋 Risultati per '{query}':{Style.RESET_ALL}")
    for idx, result in enumerate(results, 1):
        print(f"{Fore.WHITE}{idx}. 📌 {result['title']} ({result['platform']})")
        print(f"   💰 Prezzo: {result['price']}")
        print(f"   🆔 ID: {result['product_id']}")
        print("🔻" * 30)

    scelta = input(f"{Fore.YELLOW}🎯 Seleziona un gioco (1-{len(results)}) o invio per tornare: {Fore.WHITE}").strip()
    if not scelta or not scelta.isdigit() or not (1 <= int(scelta) <= len(results)):
        return

    selected_game = results[int(scelta) - 1]
    game_infos = fetch_game_info(selected_game['product_id'])

    # Richiesta filtri
    print(f"\n{Fore.YELLOW}🧩 Ricerca avanzata con filtri (invio per saltare ciascun filtro):{Style.RESET_ALL}")
    prezzo_min_str = input(f"{Fore.YELLOW}💶 Prezzo minimo in EUR: {Fore.WHITE}").strip()
    prezzo_max_str = input(f"{Fore.YELLOW}💶 Prezzo massimo in EUR: {Fore.WHITE}").strip()
    lingua_richiesta = input(f"{Fore.YELLOW}🈯 Lingua richiesta (audio o testo): {Fore.WHITE}").strip().lower()
    regione = input(f"{Fore.YELLOW}🌍 Regione/paese: {Fore.WHITE}").strip().lower()

    try:
        prezzo_min = float(prezzo_min_str) if prezzo_min_str else None
    except ValueError:
        prezzo_min = None
    try:
        prezzo_max = float(prezzo_max_str) if prezzo_max_str else None
    except ValueError:
        prezzo_max = None

    filtered_infos = []
    for info in game_infos:
        try:
            store = info.get('store', '').lower()
            prezzo_eur = info.get('price_eur')
            prezzo_eur = float(prezzo_eur) if prezzo_eur and prezzo_eur != 'N/A' else None

            if prezzo_eur is None:
                continue
            if prezzo_min is not None and prezzo_eur < prezzo_min:
                continue
            if prezzo_max is not None and prezzo_eur > prezzo_max:
                continue

            if regione and regione not in store:
                continue

            lingue = [l.lower() for l in info.get('audio_languages', []) + info.get('screen_languages', [])]
            if lingua_richiesta:
                sinonimi = sinonimi_lingue.get(lingua_richiesta, [lingua_richiesta])
                if not any(any(s in l for s in sinonimi) for l in lingue):
                    continue

            filtered_infos.append(info)

        except Exception as e:
            print(f"{Fore.RED}⚠️ Errore durante il filtraggio: {e}{Style.RESET_ALL}")

    if not filtered_infos:
        print(f"{Fore.RED}🚫 Nessun risultato trovato con i filtri selezionati.{Style.RESET_ALL}")
        return

    # Ordina per prezzo crescente
    filtered_infos.sort(key=lambda x: x['price_eur'])

    print(f"\n{Fore.GREEN}📦 Risultati per '{selected_game['title']}':{Style.RESET_ALL}")
    for idx, info in enumerate(filtered_infos, 1):
        print(f"{Fore.CYAN}{'🟦'*20}")
        print(f"{Fore.YELLOW}🌍 Store: {Fore.WHITE}{info['store']}")
        print(f"{Fore.GREEN}🎮 Titolo: {Fore.WHITE}{info['title']}")
        print(f"{Fore.MAGENTA}💰 Prezzo: {Fore.WHITE}{info['price']} {Fore.LIGHTBLACK_EX}| 💶 Prezzo in EUR: {Fore.WHITE}{info['price_eur']}")
        print(f"{Fore.BLUE}🔊 Lingue audio: {Fore.WHITE}{', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}")
        print(f"{Fore.BLUE}📝 Lingue a schermo: {Fore.WHITE}{', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}")
        if info['cover']:
            print(f"{Fore.RED}🎨 Copertina: {Fore.WHITE}{info['cover']}")
    print(f"{Fore.CYAN}{'🟦'*20}{Style.RESET_ALL}")
    
def mostra_ultimi_giochi():

    # Pre-ordini: solo giochi con "Pre-Order" nel titolo
    url = "https://store.playstation.com/it-it/latest"
    print(f"{Fore.CYAN}{'🟦'*20}")
    print(f"{Fore.YELLOW}Estrazione dei Pre-Ordini dal PlayStation Store...{Style.RESET_ALL}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        giochi = []
        LIMITE_GIOCHI = 20
        for a in soup.find_all('a', href=True):
            href = a['href']
            titolo = a.text.strip()
            
            if '/product/' in href and "Pre-Order" in titolo:
                id_gioco = href.split('/product/')[-1]
                if titolo and id_gioco:
                    giochi.append((titolo, id_gioco))
            if len(giochi) >= LIMITE_GIOCHI:
                break
        if not giochi:
            print(f"{Fore.RED}Nessun pre-ordine trovato!{Style.RESET_ALL}")
            return
        print(f"{Fore.YELLOW}Ecco alcuni Pre-Ordini disponibili su PlayStation Store:{Style.RESET_ALL}")
        for idx, (nome, id_gioco) in enumerate(giochi, 1):
            piattaforma = ""
            prezzo = ""
            nome_gioco = nome

            # Inserisce uno spazio dopo PS5/PS4 e Pre-Order se attaccati
            nome_gioco = re.sub(r'(PS[45])', r'\1 ', nome_gioco)
            nome_gioco = re.sub(r'(Pre-Order)', r'\1 ', nome_gioco)

            # Estrai piattaforma e Pre-Order se presenti all'inizio
            piattaforma_match = re.match(r"^(PS[45])\s?(Pre-Order)?\s?(.*)", nome_gioco)
            if piattaforma_match:
                piattaforma = piattaforma_match.group(1)
                pre_order = piattaforma_match.group(2) or ""
                nome_gioco = piattaforma_match.group(3).strip()
                piattaforma = f"{piattaforma} {pre_order}".strip()
            # Estrai il prezzo se presente
            prezzo_match = re.search(r"(€\s?\d+[\.,]\d{2})", nome_gioco)
            if prezzo_match:
                prezzo = prezzo_match.group(1)
                nome_gioco = nome_gioco.replace(prezzo, "").strip()
            # Stampa in formato leggibile
            print(f"{Fore.WHITE}{idx}. {piattaforma} {nome_gioco} {prezzo} - ID: {id_gioco}")
        scelta = input(f"{Fore.YELLOW}Se vuoi vedere i dettagli di un gioco, inserisci il numero (oppure premi invio per tornare al menu): {Fore.WHITE}").strip()
        if scelta.isdigit() and 1 <= int(scelta) <= len(giochi):
            nome, id_gioco = giochi[int(scelta)-1]
            infos = fetch_game_info(id_gioco)
            for info in infos:
                print(f"{Fore.CYAN}{'🟦'*20}")
                print(f"{Fore.YELLOW}🌍 Store: {Fore.WHITE}{info['store']}")
                print(f"{Fore.GREEN}🎮 Titolo: {Fore.WHITE}{info['title']}")
                print(f"{Fore.MAGENTA}💰 Prezzo: {Fore.WHITE}{info['price']} {Fore.LIGHTBLACK_EX}| 💶 Prezzo in EUR: {Fore.WHITE}{info['price_eur']}")
                print(f"{Fore.BLUE}🔊 Lingue audio: {Fore.WHITE}{', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}")
                print(f"{Fore.BLUE}📝 Lingue a schermo: {Fore.WHITE}{', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}")
                if info['cover']:
                    print(f"{Fore.RED}🎨 Copertina: {Fore.WHITE}{info['cover']}")
                print(f"{Fore.CYAN}{'🟦'*20}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Torno al menu principale...{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Errore durante lo scraping: {e}{Style.RESET_ALL}")

def mostra_nuovi_giochi():
    url = "https://store.playstation.com/it-it/pages/latest/"
    print(f"{Fore.CYAN}{'🟦'*20}")
    print(f"{Fore.YELLOW}Estrazione dei Nuovi giochi dal PlayStation Store...{Style.RESET_ALL}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        giochi = []
        LIMITE_GIOCHI = 20

        # Cerca tutti i <a> che puntano a /it-it/concept/
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("/it-it/concept/"):
                # Nome gioco
                nome_tag = a.find('span', attrs={"data-qa": re.compile(r"productTile\d+#product-name")})
                nome = nome_tag.text.strip() if nome_tag else ""
                # Prezzo
                prezzo_tag = a.find('span', attrs={"data-qa": re.compile(r"productTile\d+#price#display-price")})
                prezzo = prezzo_tag.text.strip() if prezzo_tag else ""
                # ID gioco
                id_gioco = href.split("/")[-1]
                if nome and id_gioco:
                    giochi.append((nome, id_gioco, prezzo))
            if len(giochi) >= LIMITE_GIOCHI:
                break

        if not giochi:
            print(f"{Fore.RED}Nessun nuovo gioco trovato!{Style.RESET_ALL}")
            return
        print(f"{Fore.YELLOW}Ecco alcuni Nuovi giochi disponibili su PlayStation Store:{Style.RESET_ALL}")
        for idx, (nome, id_gioco, prezzo) in enumerate(giochi, 1):
            print(f"{Fore.WHITE}{idx}. {nome} {prezzo} - ID: {id_gioco}")
        scelta = input(f"{Fore.YELLOW}Se vuoi vedere i dettagli di un gioco, inserisci il numero (oppure premi invio per tornare al menu): {Fore.WHITE}").strip()
        if scelta.isdigit() and 1 <= int(scelta) <= len(giochi):
            nome, id_gioco, _ = giochi[int(scelta)-1]
            infos = fetch_game_info(id_gioco)
            for info in infos:
                print(f"{Fore.CYAN}{'🟦'*20}")
                print(f"{Fore.YELLOW}🌍 Store: {Fore.WHITE}{info['store']}")
                print(f"{Fore.GREEN}🎮 Titolo: {Fore.WHITE}{info['title']}")
                print(f"{Fore.MAGENTA}💰 Prezzo: {Fore.WHITE}{info['price']} {Fore.LIGHTBLACK_EX}| 💶 Prezzo in EUR: {Fore.WHITE}{info['price_eur']}")
                print(f"{Fore.BLUE}🔊 Lingue audio: {Fore.WHITE}{', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}")
                print(f"{Fore.BLUE}📝 Lingue a schermo: {Fore.WHITE}{', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}")
                if info['cover']:
                    print(f"{Fore.RED}🎨 Copertina: {Fore.WHITE}{info['cover']}")
                print(f"{Fore.CYAN}{'🟦'*20}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Torno al menu principale...{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Errore durante lo scraping: {e}{Style.RESET_ALL}")

def popup_inserisci_id():
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()  # Nasconde la finestra principale
    id_gioco = simpledialog.askstring("Inserisci ID gioco", "🎮 Inserisci l'ID del gioco (es: EP0700-PPSA25381_00-ERSL000000000000):")
    root.destroy()
    return id_gioco

def ricerca_con_filtri():
    print(f"{Fore.CYAN}{'🟦'*20}")
    print(f"{Fore.YELLOW}Ricerca avanzata con filtri...{Style.RESET_ALL}")
    game_id = input(f"{Fore.YELLOW}Inserisci l'ID del gioco: {Fore.WHITE}").strip()
    if not game_id:
        print(f"{Fore.RED}🚨 Nessun ID inserito. Torno al menu.{Style.RESET_ALL}")
        return

    prezzo_min = input(f"{Fore.YELLOW}Prezzo minimo in EUR (invio per nessun filtro): {Fore.WHITE}").strip()
    prezzo_max = input(f"{Fore.YELLOW}Prezzo massimo in EUR (invio per nessun filtro): {Fore.WHITE}").strip()
    lingua = input(f"{Fore.YELLOW}Lingua richiesta (audio o testo, invio per nessun filtro): {Fore.WHITE}").strip().lower()
    regione = input(f"{Fore.YELLOW}Regione/paese (invio per nessun filtro): {Fore.WHITE}").strip().lower()

    try:
        prezzo_min = float(prezzo_min) if prezzo_min else None
    except:
        prezzo_min = None
    try:
        prezzo_max = float(prezzo_max) if prezzo_max else None
    except:
        prezzo_max = None

    infos = fetch_game_info(game_id)
    risultati = []
    for info in infos:
        # Filtro prezzo
        if info['price_eur'] == 'N/A':
            continue
        if prezzo_min and info['price_eur'] < prezzo_min:
            continue
        if prezzo_max and info['price_eur'] > prezzo_max:
            continue
        # Filtro lingua
        lingue = [l.lower() for l in info['audio_languages'] + info['screen_languages']]
        if lingua:
            sinonimi = sinonimi_lingue.get(lingua, [lingua])
            if not any(any(s in l for s in sinonimi) for l in lingue):
                continue
        # Filtro regione
        if regione and regione not in info['store'].lower():
            continue
        risultati.append(info)

    if not risultati:
        print(f"{Fore.RED}📢 Nessun risultato trovato con questi filtri.{Style.RESET_ALL}")
        return

    # Ordina i risultati per prezzo in euro (dal più basso al più alto)
    risultati = sorted(risultati, key=lambda x: x['price_eur'] if x['price_eur'] != 'N/A' else float('inf'))

    for info in risultati:
        print(f"{Fore.CYAN}{'🟦'*20}")
        print(f"{Fore.YELLOW}🌍 Store: {Fore.WHITE}{info['store']}")
        print(f"{Fore.GREEN}🎮 Titolo: {Fore.WHITE}{info['title']}")
        print(f"{Fore.MAGENTA}💰 Prezzo: {Fore.WHITE}{info['price']} {Fore.LIGHTBLACK_EX}| 💶 Prezzo in EUR: {Fore.WHITE}{info['price_eur']}")
        print(f"{Fore.BLUE}🔊 Lingue audio: {Fore.WHITE}{', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}")
        print(f"{Fore.BLUE}📝 Lingue a schermo: {Fore.WHITE}{', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}")
        if info['cover']:
            print(f"{Fore.RED}🎨 Copertina: {Fore.WHITE}{info['cover']}")
    print(f"{Fore.CYAN}{'🟦'*20}{Style.RESET_ALL}")

def genera_post_telegram(info):
    post = f"""🎮 <b>{info['title']}</b>
🌍 <a href="{info['store']}">Store</a>
💰 <b>Prezzo:</b> {info['price']} | 💶 <b>EUR:</b> {info['price_eur']}
🔊 <b>Audio:</b> {', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}
📝 <b>Testi:</b> {', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}"""
    if info.get('cover'):
        post = f'<a href="{info["cover"]}">&#8205;</a>\n' + post  # anteprima immagine
    return post

def mostra_tutte_le_offerte():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import time
    import re

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-speech-api")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--disable-features=SpeechRecognition")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    offerte_totali = []
    pagina = 1
    while True:
        url = f"https://store.playstation.com/it-it/category/3f772501-f6f8-49b7-abac-874a88ca4897/{pagina}?FULL_GAME=storeDisplayClassification&GAME_BUNDLE=storeDisplayClassification&PREMIUM_EDITION=storeDisplayClassification"
        print(f"{Fore.CYAN}・・・・・ Pagina {pagina} ・・・・・{Style.RESET_ALL}")
        try:
            driver.get(url)
            time.sleep(3)

            giochi = driver.find_elements(By.CSS_SELECTOR, "a.psw-link.psw-content-link")
            if not giochi:
                print(f"{Fore.YELLOW}👉 Nessun'altra offerta trovata. Fine delle pagine.{Style.RESET_ALL}")
                break

            pagina_offerte = []
            for idx, gioco in enumerate(giochi, 1):
                href = gioco.get_attribute("href")
                titolo = ""
                prezzo = ""
                id_gioco = ""

                spans = gioco.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    data_qa = span.get_attribute("data-qa") or ""
                    if "product-name" in data_qa:
                        titolo = span.text.strip()
                    if "price#display-price" in data_qa and "€" in span.text:
                        prezzo = span.text.strip()

                match = re.search(r'/product/([^/?]+)', href)
                if match:
                    id_gioco = match.group(1)
                else:
                    match = re.search(r'/concept/([^/?]+)', href)
                    if match:
                        id_gioco = match.group(1)

                print(f"{Fore.WHITE}{idx}. {titolo} {prezzo} - ID: {id_gioco}")
                pagina_offerte.append({
                    'titolo': titolo,
                    'prezzo': prezzo,
                    'id': id_gioco,
                    'url': href
                })

            offerte_totali.extend(pagina_offerte)

            avanti = input(f"{Fore.YELLOW}Vuoi vedere la pagina successiva? (s/n): {Fore.WHITE}").strip().lower()
            if avanti != 's':
                break
            pagina += 1
        except Exception as e:
            print(f"{Fore.RED}Errore durante lo scraping della pagina {pagina}: {e}{Style.RESET_ALL}")
            break

    driver.quit()

    if offerte_totali:
        termine = input(f"{Fore.YELLOW}Inserisci il nome (o parte) del gioco da cercare tra le offerte trovate: {Fore.WHITE}").strip().lower()
        risultati = [o for o in offerte_totali if termine in o['titolo'].lower()]

        if risultati:
            print(f"{Fore.GREEN}✅ Giochi trovati:{Style.RESET_ALL}")
            for idx, o in enumerate(risultati, 1):
                print(f"{Fore.WHITE}{idx}. {o['titolo']} {o['prezzo']} - ID: {o['id']} - URL: {o['url']}")
            
            scelta = input(f"{Fore.YELLOW}Vuoi avviare lo scraping su tutti gli store per un gioco? Inserisci il numero oppure premi invio per annullare: {Fore.WHITE}").strip()
            if scelta.isdigit() and 1 <= int(scelta) <= len(risultati):
                selezionato = risultati[int(scelta) - 1]
                print(f"{Fore.CYAN}🌍 Avvio scraping su tutti gli store per: {selezionato['titolo']} (ID: {selezionato['id']}){Style.RESET_ALL}")
                infos = fetch_game_info(selezionato['id'])
                for info in infos:
                    print(f"{Fore.CYAN}{'🟦'*20}")
                    print(f"{Fore.YELLOW}🌍 Store: {Fore.WHITE}{info['store']}")
                    print(f"{Fore.GREEN}🎮 Titolo: {Fore.WHITE}{info['title']}")
                    print(f"{Fore.MAGENTA}💰 Prezzo: {Fore.WHITE}{info['price']} {Fore.LIGHTBLACK_EX}| 💶 Prezzo in EUR: {Fore.WHITE}{info['price_eur']}")
                    print(f"{Fore.BLUE}🔊 Lingue audio: {Fore.WHITE}{', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}")
                    print(f"{Fore.BLUE}📝 Lingue a schermo: {Fore.WHITE}{', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}")
                    if info['cover']:
                        print(f"{Fore.RED}🎨 Copertina: {Fore.WHITE}{info['cover']}")
                    print(f"{Fore.CYAN}{'🟦'*20}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Scraping su tutti gli store annullato.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Nessun gioco trovato con quel nome.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Nessuna offerta da cercare.{Style.RESET_ALL}")


VERSIONE_CORRENTE = "1.1.2"
URL_VERSIONE = "https://raw.githubusercontent.com/DotHack88/ps-scraper/main/version.txt"
URL_DOWNLOAD = "https://github.com/DotHack88/ps-scraper/releases/download/v.1.1.2/scraper.1.1.2.exe"

def controlla_aggiornamenti():
    try:
        ultima_versione = requests.get(URL_VERSIONE, timeout=5).text.strip()
        if ultima_versione != VERSIONE_CORRENTE:
            root = tk.Tk()
            root.withdraw()
            risposta = messagebox.askyesno(
                "Aggiornamento disponibile",
                f"È disponibile una nuova versione ({ultima_versione}).\nVuoi scaricarla ora?"
            )
            if risposta:
                scarica_aggiornamento()
            root.destroy()
        else:
            print(f"{Fore.GREEN}✅ Il programma è già aggiornato all'ultima versione ({VERSIONE_CORRENTE}).{Style.RESET_ALL}")
    except Exception:
        print(f"{Fore.RED}Impossibile controllare la presenza di aggiornamenti.{Style.RESET_ALL}")

def scarica_aggiornamento():
    try:
        response = requests.get(URL_DOWNLOAD, stream=True)
        nome_file = os.path.basename(URL_DOWNLOAD)
        with open(nome_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        messagebox.showinfo("Download completato", f"Nuova versione scaricata come {nome_file}.\nChiudi il programma e avvia il nuovo file.")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante il download: {e}")

def stampa_sfondo():
    larghezza = 80
    titolo = "🎮 PlayStation Store Scraper 🎮"
    print(f"{Fore.BLUE}╭{'─' * (larghezza - 2)}╮")
    print(f"{Fore.BLUE}│{' ' * (larghezza - 2)}│")
    print(f"{Fore.BLUE}│{titolo.center(larghezza - 4)}│")
    print(f"{Fore.BLUE}│{' ' * (larghezza - 2)}│")
    print(f"{Fore.BLUE}╰{'─' * (larghezza - 2)}╯{Style.RESET_ALL}")

def pulisci_schermo():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    controlla_aggiornamenti()
    while True:
        stampa_sfondo()
        print(f"{Fore.LIGHTRED_EX}⚠️  Questo programma è opera di DotHack88. Ne è vietata la vendita e la distribuzione non autorizzata!{Style.RESET_ALL}")

        print(f"{Fore.GREEN}Cosa vuoi fare?")
        print(f"{Fore.WHITE}1. 🔎 Cerca per ID gioco (consigliato)")
        print(f"{Fore.WHITE}2. 🔍 Cerca con filtri avanzati")
        print(f"{Fore.WHITE}3. 🔤 Cerca per nome gioco")
        print(f"{Fore.WHITE}4. 💥 Tutte le offerte")
        print(f"{Fore.WHITE}5. 🆕 Pre-ordini")
        print(f"{Fore.WHITE}6. 🆕 Nuovi giochi")
        print(f"{Fore.WHITE}7. 📌 Info sul programma")
        print(f"{Fore.WHITE}8. ❌ Esci")
        scelta = input(f"{Fore.YELLOW}Seleziona un'opzione (1-8): {Fore.WHITE}").strip()

        if scelta == "1":
            game_id = input(f"{Fore.YELLOW}🎮 Inserisci l'ID del gioco (es: EP0700-PPSA25381_00-ERSL000000000000): {Fore.WHITE}").strip()
            if not game_id:
                print(f"{Fore.RED}🚨 Nessun ID inserito.{Style.RESET_ALL}")
            else:
                infos = fetch_game_info(game_id)
                for info in infos:
                    print(f"{Fore.CYAN}{'🟦'*20}")
                    print(f"{Fore.YELLOW}🌍 Store: {Fore.WHITE}{info['store']}")
                    print(f"{Fore.GREEN}🎮 Titolo: {Fore.WHITE}{info['title']}")
                    print(f"{Fore.MAGENTA}💰 Prezzo: {Fore.WHITE}{info['price']} {Fore.LIGHTBLACK_EX}| 💶 Prezzo in EUR: {Fore.WHITE}{info['price_eur']}")
                    print(f"{Fore.BLUE}🔊 Lingue audio: {Fore.WHITE}{', '.join(info['audio_languages']) if info['audio_languages'] else 'N/A'}")
                    print(f"{Fore.BLUE}📝 Lingue a schermo: {Fore.WHITE}{', '.join(info['screen_languages']) if info['screen_languages'] else 'N/A'}")
                    if info['cover']:
                        print(f"{Fore.RED}🎨 Copertina: {Fore.WHITE}{info['cover']}")
                    print(f"{Fore.CYAN}{'🟦'*20}{Style.RESET_ALL}")
        elif scelta == "2":
            ricerca_con_filtri()
        elif scelta == "3":
            mostra_ricerca_generica()
        elif scelta == "4":
            mostra_tutte_le_offerte()
        elif scelta == "5":
            mostra_ultimi_giochi()
        elif scelta == "6":
            mostra_nuovi_giochi()
        elif scelta == "7":
            print(f"{Fore.CYAN}ℹ️  Versione: {VERSIONE_CORRENTE}")
            print(f"{Fore.CYAN}🌎 Repository: https://github.com/DotHack88/ps-scraper{Style.RESET_ALL}")
            print(f"{Fore.CYAN}ℹ️  Questo programma ti permette di confrontare prezzi e lingue dei giochi PlayStation Store nei vari paesi!{Style.RESET_ALL}")
            print(f"{Fore.LIGHTRED_EX}⚠️  Questo programma è opera di DotHack88. Ne è vietata la vendita e la distribuzione non autorizzata!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🔜 Prossimamente: ricerca per nome, filtri avanzati e molto altro!{Style.RESET_ALL}")
        elif scelta == "8":
            print(f"{Fore.RED}👋 Uscita dal programma. Arrivederci!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Opzione non valida. Riprova!{Style.RESET_ALL}")
        
        # Chiedi se continuare
        continua = input(f"\n{Fore.YELLOW}Vuoi fare un'altra ricerca? (s/n): {Fore.WHITE}").strip().lower()
        if continua != 's':
            print(f"{Fore.RED}👋 Uscita dal programma. Arrivederci!{Style.RESET_ALL}")
            break