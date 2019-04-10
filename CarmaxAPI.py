import json
import logging
import re
import time
from enum import Enum
from typing import List

import selenium
from bs4 import BeautifulSoup, Tag
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helper import list_to_str_list

from CarmaxBrowser import CarmaxBrowser

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    first = 'F'
    second = 'S'
    other = 'O'

    @staticmethod
    def parse(s: str):
        _f = s[0]
        if _f == '1':
            return ConnectionType.first
        if _f == '2':
            return ConnectionType.second
        # if _f == '3':
        return ConnectionType.other
        # raise ValueError('"{}" not recognized as a connection type str')


CARMAX_URL = 'https://www.carmax.com'


class CarmaxAPI:

    def __init__(self, driver: CarmaxBrowser):
        self.driver = driver

    def search_model_headless(self, search='/cars/camry/toyota', start_n=0, load_n=50, zip_code=15206, radius=50):
        url = 'https://www.carmax.com/cars/api/get'
        params = {
            'uri': search,
            'skip': start_n,
            'take': load_n,
            'radius': radius,
            'zipCode': zip_code,
            'sort': 20
        }
        r = self.driver.headless_get(url, params=params)
        return r.json()

    def search_model_headless_all(self, search, zip_code=15206, radius=50, _each_n=20):
        start_n = 0

        data = self.search_model_headless(search, zip_code=zip_code, radius=radius, load_n=_each_n, start_n=start_n)
        item_arr = data['items']

        for i in range(data['totalCount'] // _each_n):
            start_n += _each_n
            data = self.search_model_headless(search, zip_code=zip_code, radius=radius, load_n=_each_n, start_n=start_n)
            item_arr += data['items']

        return item_arr

    def search_model(self, search_term='') -> List['CarModel']:
        url_tpl = CARMAX_URL + '/cars/{keywords}'
        url = url_tpl.format(keywords=search_term)

        r = self.iterate_search_result(url)
        return r

    def iterate_search_result(self, url):

        record_dict = {}

        def load_page(_url):
            self.driver.get(_url)

            # Scroll to bottom to force load all content
            self.driver.driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            time.sleep(1)  # fix me

            # process 'see more'
            while True:
                try:
                    element = WebDriverWait(self.driver.driver, timeout=1).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "see-more"))
                    )
                    self.driver.driver.execute_script('document.querySelector("button.see-more").click();')
                    print('"see more" clicked')
                except TimeoutException:
                    break

            return

        def proc_page_result(page_html: str):
            # parse the return html
            root = BeautifulSoup(page_html, 'html.parser')  # , parser='HTML')
            rst_list = root.find(id='cars-listing')
            rst_list = rst_list.find_all('article')

            print(f'len(rst_list)={len(rst_list)}')

            for i in rst_list:
                car_info = i.find('div', class_='car-info')
                if not car_info:
                    continue
                car_title = car_info.find(class_='car-title')
                if car_title:
                    _1st, _, _2nd = car_title.contents
                    year, make = _1st.split(' ')
                    model, trim = _2nd.split(' ')
                    car = CarModel(make, model, trim, year)

                    car_price = car_info.find(class_='car-price')
                    car_price = car_price.text.replace('*', '').replace(',', '')
                    car_mileage = car_info.find(class_='car-mileage')
                    if car_mileage:
                        car_mileage = car_mileage.text
                    record = CarMaxRecord(car, car_price, car_mileage)

                    car_key = str(car)
                    if car_key not in record_dict:
                        print(f'Found new model: {car}')
                        record_dict[car_key] = [record]
                    else:
                        print(f'append model: {car}')
                        record_dict[car_key].append(record)

        load_page(url)
        html = self.driver.driver.page_source

        # pagination
        nd = BeautifulSoup(html, 'html.parser')
        ap = nd.find('artdeco-pagination')
        pl = nd.find('li', class_='page-list')
        # todo Handle see more
        proc_page_result(html)

        return record_dict


class CarModel:
    def __init__(self, make, model, trim, year):
        self.year = year
        self.trim = trim
        self.model = model
        self.make = make

    def __hash__(self):
        # return int(''.join([str(ord(i)) for i in self.__str__()]))
        return hash((self.year, self.trim, self.model, self.make))

    def __str__(self):
        return f'{self.year}-{self.trim}-{self.model}-{self.make}'

    def __repr__(self):
        return self.__str__()


class CarMaxRecord:
    def __init__(self, car: CarModel, price, mileage):
        self.price = price
        self.mileage = mileage
        self.car = car


if __name__ == '__main__':
    b = CarmaxBrowser()
    api = CarmaxAPI(b)

    # records = api.search_model_headless(search='/cars?search=civic')
    records = api.search_model_headless(search='/cars/camry/toyota')
    open('data/sample_search_model_headless.json', 'w').write(json.dumps(records))

    records = api.search_model_headless_all(search='/cars?search=civic')
    open('data/sample_search_model_headless_all.json', 'w').write(json.dumps(records))

    # records = api.search_model('camry/toyota')
    # records = api.search_model('focus')

    print(records)
    b.close_browser()
