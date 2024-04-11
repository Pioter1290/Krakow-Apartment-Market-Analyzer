import requests
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
import geopandas as gpd
import zipfile, re, os
from bs4 import BeautifulSoup
from urllib import request
import time

url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?viewType=listing"
pages = []

# Pobieranie stron
for page_number in range(1, 3):
    req = request.Request(f'{url}&page={page_number}', headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Pobieranie strony {page_number}')
    with request.urlopen(req) as resp:
        processed_page = BeautifulSoup(resp.read().decode('utf-8'), "html.parser")
        pages.append(processed_page)

data = []
for page in pages:
    data += page.find_all(class_="css-136g1q2 e88tro00")
flats = []
#oprócz dzielnic dodałem również Wieliczkę
dzielnice = {'Stare Miasto', 'Grzegórzki', 'Prądnik Czerwony', 'Prądnik Biały', 'Krowodrza', 'Bronowice', 'Zwierzyniec', 'Dębniki', 'Łagiewniki-Borek Fałęcki', 'Swoszowice', 'Podgórze Duchackie', 'Bieżanów-Prokocim', 'Podgórze', 'Czyżyny', 'Mistrzejowice', 'Bieńczyce', 'Wzgórza Krzesławickie', 'Nowa Huta','Wieliczka'}


for flat_html in data:
    flat = {}
    flat['adres'] = flat_html.find(class_="css-12h460e efr035y1").text.strip()

    pattern_pokoje = r'<dt>Liczba pokoi</dt><dd>(.*?) pok[oó]j[ie]?</dd>'
    pattern_powierzchnia = r'<dt>Powierzchnia</dt><dd>(.*?)<!-- --> <!-- -->m²</dd>'
    pattern_cena = r'<dt>Cena za metr kwadratowy</dt><dd>(.*?)\s*zł<!-- -->/<!-- -->m²</dd>'
    pattern_pietro = r'<dt>Piętro</dt><dd>(.*?)</dd>'

    flat_data = str(flat_html.find(class_="css-uki0wd e12r8p6s1"))

    pokoje_match = re.search(pattern_pokoje, flat_data)
    powierzchnia_match = re.search(pattern_powierzchnia, flat_data)
    cena_match = re.search(pattern_cena, flat_data)
    pietro_match = re.search(pattern_pietro, flat_data)

    if pokoje_match:
        flat['Liczba pokoi'] = pokoje_match.group(1)
    if powierzchnia_match:
        flat['Powierzchnia'] = powierzchnia_match.group(1)
    if cena_match:
        flat['Cena za metr kwadratowy'] = cena_match.group(1)
    if pietro_match:
        flat['Piętro'] = pietro_match.group(1)

    price = flat_html.find(class_="css-1uwck7i").text.strip()
    if price == 'Zapytaj o cenę':
        flat['cena'] = None
    else:
        price = price.replace('\xa0zł', '').replace(' ', '')
        price = price.replace('\xa0', '')
        price = price.replace(',', '.')
        flat['cena'] = float(price)
        url_element = flat_html.find('a', attrs={'data-cy': 'listing-item-link'}).get('href')
        flat['url'] = 'https://www.otodom.pl' + url_element if url_element else 'NONE'
    # Wyszukiwanie dzielnicy
    for dzielnica in dzielnice:
        if dzielnica in flat['adres']:
            flat['dzielnica'] = dzielnica
            break
    else:
        flat['dzielnica'] = 'Nieznana'

    flats.append(flat)


flats_info = pd.DataFrame.from_dict(flats)

flats_info.head(20)


flats_over_50sqm = flats_info[flats_info['Powierzchnia'].str.replace(',', '.').str.extract('(\d+\.?\d*)', expand=False).astype(float) > 50]

flats_over_50sqm_sorted = flats_over_50sqm.sort_values(by='cena', ascending=True)

cheapest_flat_over_50sqm = flats_over_50sqm_sorted
cheapest_flats_info = pd.DataFrame.from_dict(cheapest_flat_over_50sqm)

cheapest_flats_info.head(10)



dzielnice_count = flats_info['dzielnica'].value_counts()

plt.figure(figsize=(14, 6))
dzielnice_count.plot(kind='bar', color='skyblue',edgecolor='black')
plt.title('Liczba ogłoszeń w zależności od dzielnicy')
plt.xlabel('Dzielnica')
plt.ylabel('Liczba ogłoszeń')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()