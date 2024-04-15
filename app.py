from flask import Flask, render_template, request, url_for
import pandas as pd
from bs4 import BeautifulSoup
from urllib import request as urlrequest
import re

from matplotlib import pyplot as plt

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/generate_chart')
def generate_chart_bar():
    url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?viewType=listing"
    pages = []
    for page_number in range(1, 5):
        req = urlrequest.Request(f'{url}&page={page_number}', headers={'User-Agent': 'Mozilla/5.0'})
        with urlrequest.urlopen(req) as resp:
            processed_page = BeautifulSoup(resp.read().decode('utf-8'), "html.parser")
            pages.append(processed_page)

    flats = []
    districts = {'Stare Miasto', 'Grzegórzki', 'Prądnik Czerwony', 'Prądnik Biały', 'Krowodrza', 'Bronowice',
                 'Zwierzyniec', 'Dębniki', 'Łagiewniki-Borek Fałęcki', 'Swoszowice', 'Podgórze Duchackie',
                 'Bieżanów-Prokocim', 'Podgórze', 'Czyżyny', 'Mistrzejowice', 'Bieńczyce', 'Wzgórza Krzesławickie',
                 'Nowa Huta', 'Wieliczka'}

    for page in pages:
        for flat_html in page.find_all(class_="css-136g1q2 e88tro00"):
            flat = {}
            flat['adres'] = flat_html.find(class_="css-12h460e efr035y1").text.strip()
            flat_data = str(flat_html.find(class_="css-uki0wd e12r8p6s1"))
            parse_flat_details(flat, flat_data)
            if any(district in flat['adres'] for district in districts):
                flat['dzielnica'] = next(district for district in districts if district in flat['adres'])

            url_element = flat_html.find('a', attrs={'data-cy': 'listing-item-link'}).get('href')
            flat['url'] = 'https://www.otodom.pl' + url_element if url_element else 'NONE'
            flats.append(flat)

    flats_info = pd.DataFrame(flats)

    dzielnice_count = flats_info['dzielnica'].value_counts()

    plt.figure(figsize=(14, 6))
    dzielnice_count.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title('Liczba ogłoszeń w zależności od dzielnicy')
    plt.xlabel('Dzielnica')
    plt.ylabel('Liczba ogłoszeń')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    img_path = 'static/dzielnice_chart.png'
    plt.savefig(img_path)
    plt.close()

    img_url = url_for('static', filename='dzielnice_chart.png')
    return f'<img src="{img_url}" alt="Bar Chart of Listings by District"/>'

@app.route('/generate_all_flats')
def generate_all_flats():
    url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?viewType=listing"
    pages = []
    for page_number in range(1, 5):
        req = urlrequest.Request(f'{url}&page={page_number}', headers={'User-Agent': 'Mozilla/5.0'})
        with urlrequest.urlopen(req) as resp:
            processed_page = BeautifulSoup(resp.read().decode('utf-8'), "html.parser")
            pages.append(processed_page)

    flats = []

    for page in pages:
        for flat_html in page.find_all(class_="css-136g1q2 e88tro00"):
            flat = {}
            flat['adres'] = flat_html.find(class_="css-12h460e efr035y1").text.strip()
            flat_data = str(flat_html.find(class_="css-uki0wd e12r8p6s1"))
            parse_flat_details(flat, flat_data)

            url_element = flat_html.find('a', attrs={'data-cy': 'listing-item-link'}).get('href')
            flat['url'] = 'https://www.otodom.pl' + url_element if url_element else 'NONE'
            flats.append(flat)

    flats_info = pd.DataFrame(flats)
    return flats_info.to_html() if not flats_info.empty else "Nie znaleziono mieszkań."

@app.route('/process', methods=['GET', 'POST'])
def process_data_and_plot():
    if request.method == 'POST':
        min_size = request.form.get('metraz', type=float)
        selected_districts = request.form.getlist('dzielnica')

        if not min_size:
            return "Proszę podać metraż mieszkania."

        url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?viewType=listing"
        pages = []
        for page_number in range(1, 5):
            req = urlrequest.Request(f'{url}&page={page_number}', headers={'User-Agent': 'Mozilla/5.0'})
            with urlrequest.urlopen(req) as resp:
                processed_page = BeautifulSoup(resp.read().decode('utf-8'), "html.parser")
                pages.append(processed_page)

        flats = []


        for page in pages:
            for flat_html in page.find_all(class_="css-136g1q2 e88tro00"):
                flat = {}
                flat['adres'] = flat_html.find(class_="css-12h460e efr035y1").text.strip()
                flat_data = str(flat_html.find(class_="css-uki0wd e12r8p6s1"))
                parse_flat_details(flat, flat_data)

                if 'Powierzchnia' in flat and flat['Powierzchnia'] >= min_size:
                    url_element = flat_html.find('a', attrs={'data-cy': 'listing-item-link'}).get('href')
                    flat['url'] = 'https://www.otodom.pl' + url_element if url_element else 'NONE'

                    if any(district in flat['adres'] for district in selected_districts):
                        flat['dzielnica'] = next(district for district in selected_districts if district in flat['adres'])
                        flats.append(flat)

        flats_info = pd.DataFrame(flats)
        return flats_info.to_html() if not flats_info.empty else "Nie znaleziono mieszkań spełniających kryteria."

def parse_flat_details(flat, flat_data):
    patterns = {
        'Liczba pokoi': r'<dt>Liczba pokoi</dt><dd>(.*?) pok[oó]j[ie]?</dd>',
        'Powierzchnia': r'<dt>Powierzchnia</dt><dd>(.*?)<!-- --> <!-- -->m²</dd>',
        'Cena za metr kwadratowy': r'<dt>Cena za metr kwadratowy</dt><dd>(.*?)\s*zł<!-- -->/<!-- -->m²</dd>',
        'Piętro': r'<dt>Piętro</dt><dd>(.*?)</dd>'
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, flat_data)
        if match:
            flat[key] = float(match.group(1).replace(',', '.')) if key == 'Powierzchnia' else match.group(1)

if __name__ == '__main__':
    app.run(debug=True)
