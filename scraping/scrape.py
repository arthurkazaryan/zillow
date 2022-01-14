from bs4 import BeautifulSoup
import requests
import pandas as pd
from tqdm import tqdm
import json
from pathlib import Path

zillow = 'https://www.zillow.com'
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.5",
           "Accept-Encoding": "gzip, deflate",
           "DNT": "1",
           "Connection": "close",
           "Upgrade-Insecure-Requests": "1"}


def prepare_reponses():

    responses = []
    for i in range(len([x for x in Path.cwd().joinpath('responses').iterdir()])):
        with open(Path.cwd().joinpath('responses', f'raw_response ({i}).json'), 'r') as resp:
            one_response = json.load(resp)
        for resp in one_response['cat1']['searchResults']['mapResults']:
            if resp not in all_responses:
                responses.append(resp)

    return responses


def homedetails_info(bs_apartment):

    apartment_info = {'Latitude': 'no_data', 'Longitude': 'no_data',
                      'Address': bs_apartment.h1.text.replace('\xa0', ' ').strip(), 'Calendar': 'no_data',
                      'Building': 'no_data', 'Snowflake': 'no_data', 'Heating': 'no_data', 'Pets': 'no_data',
                      'Parking': 'no_data', 'Laundry': 'no_data', 'Deposit and Fees': 'no_data', 'Bedrooms': 'no_data',
                      'Bathrooms': 'no_data', 'Price': bs_apartment.find('div', 'ds-summary-row').span.text,
                      'Overview': 'no_data'}

    parameters = bs_apartment.find('ul', 'dpf__sc-xzpkxd-0 jHoFQf').find_all('li')
    for parameter in parameters:
        apartment_info[parameter.span.text] = parameter.text.split(':')[-1]
    apartment_info['Overview'] = bs_apartment.find('div', 'ds-overview-section').text.replace(',Read less', '')
    block = bs_apartment.find('ul', 'List-c11n-8-62-4__sc-1smrmqp-0 dpf__sc-1j9xcg4-1 fiomyP bNyGAI')
    if block:
        data = block.find_all('li')
        for idx, elem in enumerate(data):
            info = elem.text.split(': ')
            apartment_info[info[0]] = info[1]

    return apartment_info


def homedetails_houses(house_link):

    all_links = []
    response_house = requests.get(house_link, headers=headers)
    bs_house = BeautifulSoup(response_house.content, 'lxml')

    house_cards = bs_house.find_all('a', class_='unit-card-link')
    for card in house_cards:
        all_links.append(zillow + card['href'])

    return all_links


if __name__ == '__main__':
    apartment_dataframe = {'Latitude': [],
                           'Longitude': [],
                           'Address': [],
                           'Calendar': [],
                           'Building': [],
                           'Snowflake': [],
                           'Heating': [],
                           'Pets': [],
                           'Parking': [],
                           'Laundry': [],
                           'Deposit and Fees': [],
                           'Bedrooms': [],
                           'Bathrooms': [],
                           'Price': [],
                           'Overview': []
                           }

    all_responses = prepare_reponses()
    for response in tqdm(all_responses):
        link_list = [zillow + response['detailUrl']]
        if 'homedetails' not in link_list[0]:
            link_list = homedetails_houses(link_list[0])
        if link_list:
            for link in link_list:
                try:
                    response_apartment = requests.get(link, headers=headers)
                    if response_apartment.status_code < 400:
                        apartment = BeautifulSoup(response_apartment.content, 'lxml')
                        apartment_data = homedetails_info(apartment)
                        apartment_data['Latitude'] = response['latLong']['latitude']
                        apartment_data['Longitude'] = response['latLong']['longitude']
                        for key, value in apartment_data.items():
                            apartment_dataframe[key].append(value)
                except:
                    pass

    pd.DataFrame(apartment_dataframe).to_excel('toronto_zillow.xlsx')
