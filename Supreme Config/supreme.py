#!/usr/bin/python3
# Zachary Weeden 2018

import os
import random
import sys
import configparser
import json
import datetime
import requests
import time
from colorCodes import *
import threading
from requests.utils import dict_from_cookiejar
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import platform
import zipfile
import contextlib
import glob

root_directory = os.getcwd()
c = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, 'config.cfg')
c.read(configFilePath)


class Config:
    productNames = list(dict(c.items('productName')).values())
    productColors = list(dict(c.items('productColor')).values())
    productSizes = list(dict(c.items('productSize')).values())
    productQuantities = list(dict(c.items('productQty')).values())
    poll = int(c.get('timeComponents', 'poll'))
    ghostCheckoutPrevention = int(c.get('timeComponents', 'ghostCheckoutPrevention'))
    billingName = c.get('cardInfo', 'firstAndLast')
    email = c.get('cardInfo', 'email')
    phone = c.get('cardInfo', 'phone')
    streetAddress = c.get('cardInfo', 'address')
    zipCode = c.get('cardInfo', 'zip')
    shippingCity = c.get('cardInfo', 'city')
    shippingState = c.get('cardInfo', 'state')
    shippingCountry = c.get('cardInfo', 'country')
    cardType = c.get('cardInfo', 'cardType')
    cardNumber = c.get('cardInfo', 'cardNumber')
    cardMonth = c.get('cardInfo', 'cardMonth')
    cardYear = c.get('cardInfo', 'cardYear')
    cardCVV = c.get('cardInfo', 'cardCVV')


class SupremeProduct:
    def __init__(self, item_name, item_color, item_size, item_quantity, thread_color, local_chromedriver_file):
        self.item_name = item_name
        self.item_color = item_color
        self.item_size = item_size
        self.item_quantity = item_quantity
        self.thread_text_color = thread_color
        self.product_found = 0
        self.product_color_found = 0
        self.product_size_found = 0
        self.driver = webdriver.Chrome(local_chromedriver_file)
        self.find_product()

    def fetch_mobile_stock(self):
        headers = {
            'Host': 'www.supremenewyork.com',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13G34',
            'Referer': 'http://www.supremenewyork.com/mobile',
            'Accept-Language': 'en-us',
            'X-Requested-With': 'XMLHttpRequest'
        }
        return requests.request('GET', 'https://www.supremenewyork.com/mobile_stock.json', headers=headers).json()

    def get_product_information(self, product_id):
        return requests.request('GET', f'https://www.supremenewyork.com/shop/{str(product_id)}.json', headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13G34'}).json()

    def find_product_variant(self, product_name, product_id):
        sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: Selecting [[ {self.thread_text_color}{product_name}{COLOR_END} ]] ( {str(product_id)} )\n')
        product_info = self.get_product_information(product_id)
        for listed_product_colors in product_info['styles']:
            if self.item_color.lower() in listed_product_colors['name'].lower():
                self.product_color_found = 1
                product_color_specific_id = listed_product_colors['id']
                for size in listed_product_colors['sizes']:
                    if self.item_size.lower() == size['name'].lower():
                        self.product_size_found = 1
                        product_size_color_specific_id = size['id']
                        sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: Selecting size for [[ {self.thread_text_color}{product_name}{COLOR_END} ]] - {self.item_size} ( {self.item_color} )  ( {str(product_size_color_specific_id)} )\n')
                if self.product_size_found != 1:
                    # Add functionality to add default size on matching color product
                    pass
        if self.product_color_found != 1:
            # Add functionality to add default color AND size on matching product model
            pass
        return product_color_specific_id, product_size_color_specific_id

    def show_cookies(self, response):
        cookie_dict_wrapper = []
        for key, value in requests.utils.dict_from_cookiejar(response.cookies).items():
            dict_template = {
                'domain': '.supremenewyork.com',
                'expiry': int(time.time() + 7200),
                'httpOnly': False,
                'path': '/',
                'secure': False,
                'name': key,
                'value': value
            }
            cookie_dict_wrapper.append(dict_template)
        print('\tEditThisCookie Import\t')
        print(f'####################################################################################################################################{self.thread_text_color}')
        print(json.dumps(cookie_dict_wrapper, indent=4))
        print(f'{COLOR_END}####################################################################################################################################')

    def checkout(self, webdriver_instance):
        webdriver_instance.get('https://www.supremenewyork.com/checkout')

        # Try multiple selectors
        # TODO actually make javascript get element by selector instead of mix of id, name, css selector
        possible_name_field_selectors = ['order_billing_name']
        element_found = False
        for name_field_selector in  possible_name_field_selectors:
            try:
                #customer_name = webdriver_instance.find_element_by_name('order[billing_name]')
                webdriver_instance.execute_script(f'document.getElementById(\'{name_field_selector}\').value = ""')
                #customer_name.clear()
                webdriver_instance.execute_script(f'document.getElementById(\'{name_field_selector}\').value = "{user_config.billingName}"')
                #customer_name.send_keys(user_config.billingName)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {name_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order billing name field')
            input('Click to continue automation...')

        element_found = False
        possible_email_field_selectors = ['order_email']
        for email_field_selector in  possible_email_field_selectors:
            try:
                #customer_email = webdriver_instance.find_element_by_name('order[email]')
                webdriver_instance.execute_script(f'document.getElementById(\'{email_field_selector}\').value = ""')
                #customer_email.clear()
                webdriver_instance.execute_script(f'document.getElementById(\'{email_field_selector}\').value = "{user_config.email}"')
                #customer_email.send_keys(user_config.email)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {email_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order email field')
            input('Click to continue automation...')

        element_found = False
        possible_phone_field_selectors = ['order_tel']
        for phone_field_selector in  possible_phone_field_selectors:
            try:
                customer_telephone = webdriver_instance.find_element_by_id(phone_field_selector)
                customer_telephone.clear()
                customer_telephone.send_keys(user_config.phone)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {phone_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order tel field')
            input('Click to continue automation...')

        element_found = False
        possible_address_field_selectors = ['bo']
        for address_field_selector in  possible_address_field_selectors:
            try:
                #customer_address = webdriver_instance.find_element_by_name('order[billing_address]')
                webdriver_instance.execute_script(f'document.getElementById(\'{address_field_selector}\').value = ""')
                #customer_address.clear()
                webdriver_instance.execute_script(f'document.getElementById(\'{address_field_selector}\').value = "{user_config.streetAddress}"')
                #customer_address.send_keys(user_config.streetAddress)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {address_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order[billing_address] field (address)')
            input('Click to continue automation...')

        element_found = False
        possible_zip_field_selectors = ['order_billing_zip']
        for zip_field_selector in  possible_zip_field_selectors:
            try:
                #customer_zip = webdriver_instance.find_element_by_name('order[billing_zip]')
                webdriver_instance.execute_script(f'document.getElementById(\'{zip_field_selector}\').value = ""')
                #customer_zip.clear()
                webdriver_instance.execute_script(f'document.getElementById(\'{zip_field_selector}\').value = "{user_config.zipCode}"')
                #customer_zip.send_keys(user_config.zipCode)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {zip_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order billing zip field')
            input('Click to continue automation...')

        element_found = False
        possible_city_field_selectors = ['order_billing_city']
        for city_field_selector in  possible_city_field_selectors:
            try:
                # OLD: # Let zip code auto fill this
                # pass
                # customer_city = webdriver_instance.find_element_by_id('order_billing_city')
                # customer_city.click()
                webdriver_instance.execute_script(f'document.getElementById(\'{city_field_selector}\').value = ""')
                # customer_city.clear()
                webdriver_instance.execute_script(f'document.getElementById(\'{city_field_selector}\').value = "{user_config.shippingCity}"')
                # customer_city.send_keys(user_config.shippingCity)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {city_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order billing city field')
            input('Click to continue automation...')

        element_found = False
        possible_state_field_selectors = ['order_billing_state']
        for state_field_selector in  possible_state_field_selectors:
            try:
                customer_state = Select(webdriver_instance.find_element_by_id(state_field_selector))
                customer_state.select_by_value(user_config.shippingState.upper())  # or visible text
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {state_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find order billing state dropdown/value')
            input('Click to continue automation...')

        element_found = False
        possible_country_field_selectors = ['order[billing_country]']
        for country_field_selector in  possible_country_field_selectors:
            try:
                customer_country = Select(webdriver_instance.find_element_by_name(country_field_selector))
                customer_country.select_by_value(user_config.shippingCountry.upper())  # or visible text (USA or CANADA)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {country_field_selector}')
                continue

        if element_found is False:    
            print('Couldn\'t find order billing country drowpdown/value')
            input('Click to continue automation...')

        element_found = False
        possible_card_number_field_selectors = ['nnaerb']
        for card_number_field_selector in  possible_card_number_field_selectors:
            try:
                customer_card_number = webdriver_instance.find_element_by_id(card_number_field_selector)
                customer_card_number.clear()
                customer_card_number.send_keys(user_config.cardNumber)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {card_number_field_selector}')
                continue

        if element_found is False:   
            print('Couldn\'t find nnaerb field (card number)')
            input('Click to continue automation...')

        element_found = False
        possible_card_month_field_selectors = ['credit_card[month]']
        for card_month_field_selector in  possible_card_month_field_selectors:
            try:
                customer_card_month = Select(webdriver_instance.find_element_by_name(card_month_field_selector))  # month must be padded eg. 09
                customer_card_month.select_by_value(user_config.cardMonth)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {card_month_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find credit card month dropdown/value')
            input('Click to continue automation...')

        element_found = False
        possible_card_year_field_selectors = ['credit_card[year]']
        for card_year_field_selector in  possible_card_year_field_selectors:
            try:
                customer_card_year = Select(webdriver_instance.find_element_by_name(card_year_field_selector))
                customer_card_year.select_by_value(user_config.cardYear)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {card_year_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find credit card year dropdown/value')
            input('Click to continue automation...')

        element_found = False
        possible_card_cvv_field_selectors = ['orcer']
        for card_cvv_field_selector in  possible_card_cvv_field_selectors:
            try:
                #customer_card_cvv = webdriver_instance.find_element_by_name('credit_card[rvv]')
                webdriver_instance.execute_script(f'document.getElementById(\'{card_cvv_field_selector}\').value = ""')
                #customer_card_cvv.clear()
                webdriver_instance.execute_script(f'document.getElementById(\'{card_cvv_field_selector}\').value = "{user_config.cardCVV}"')
                #customer_card_cvv.send_keys(user_config.cardCVV)
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {card_cvv_field_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find credit_card[rvv] field (card cvv)')
            input('Click to continue automation...')

        element_found = False
        possible_accept_terms_radio_selectors = ['#cart-cc > fieldset > p:nth-child(4) > label > div > ins']
        for accept_terms_radio_selector in  possible_accept_terms_radio_selectors:
            try:
                accept_terms = webdriver_instance.find_element_by_css_selector(accept_terms_radio_selector)
                accept_terms.click()
                element_found = True
                break
            except:
                print(f'Couldn\'t find with selector: {accept_terms_radio_selector}')
                continue

        if element_found is False:
            print('Couldn\'t find accept terms radio button')
            input('Click to continue automation...')

        input('NEXT STEP IS TO CHECKOUT')
        """Stubbed for safety"""
        # try:
        #     checkout_button = webdriver_instance.find_element_by_css_selector('#pay > input')
        #     checkout_button.click()
        # except:
        #     print('Couldn\'t find process/pay/checkout button')
        #     input('Click to continue automation...')

    def start_webdriver(self, response):
        #driver = webdriver.Chrome(f'{os.getcwd()}/chromedriver')  # chromedriver bin must be in folder of invocation -implement check
        self.driver.get('https://www.supremenewyork.com/shop/cart')  # commonly carts
        self.driver.delete_all_cookies()
        for key, value in dict_from_cookiejar(response.cookies).items():
            self.driver.add_cookie({'name': key, 'value': value})
        self.driver.refresh()
        self.checkout(self.driver)

    def add_to_cart(self, listed_product_name, product_base_id, product_color_id, product_size_id):
        sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: Adding [[ {self.thread_text_color}{listed_product_name}{COLOR_END} ]] to cart...\n')
        add_payload = {
            's': str(product_size_id),
            'st': str(product_color_id),
            'qty': str(self.item_quantity)
        }
        headers = {
            'Host':              'www.supremenewyork.com',
            'Accept':            'application/json',
            'Proxy-Connection':  'keep-alive',
            'X-Requested-With':  'XMLHttpRequest',
            'Accept-Encoding':   'gzip, deflate',
            'Accept-Language':   'en-us',
            'Content-Type':      'application/x-www-form-urlencoded',
            'Origin':            'http://www.supremenewyork.com',
            'Connection':        'keep-alive',
            'User-Agent':        'Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Mobile/14C92',
            'Referer':           'http://www.supremenewyork.com/mobile'
        }
        atc_response = requests.request('POST', f'https://www.supremenewyork.com/shop/{product_base_id}/add.json', data=add_payload, headers=headers)

        if atc_response.status_code != 200:  # DID ITEM ADD TO CART - wait/sleep and make POST again
            sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: {str(atc_response.status_code)} Error [[ {self.thread_text_color}{listed_product_name}{COLOR_END} ]] {FAIL}FAILED!{COLOR_END}\n')
            sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {addResp.json()}\n')
            sys.exit()
        else:
            if atc_response.json() == []:  # request was OK but did not add item to cart - wait/sleep and make POST again
                sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: Response Empty! - Problem Adding to Cart! [[ {self.thread_text_color}{listed_product_name}{COLOR_END} ]] {FAIL}FAILED!{COLOR_END} - {self.thread_text_color}Trying once more with different payload{COLOR_END}\n')  # CHECK THIS - DID ITEM ADD TO CART? MAKE POST AGAIN
                add_payload = {
                    'size': str(product_size_id),
                    'style': str(product_color_id),
                    'qty': str(self.item_quantity)
                }
                atc_response = requests.request('POST', f'https://www.supremenewyork.com/shop/{product_base_id}/add.json', data=add_payload, headers=headers)
                if atc_response.status_code != 200:  # DID ITEM ADD TO CART - wait/sleep and make POST again
                    sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: {str(atc_response.status_code)} Error [[ {self.thread_text_color}{listed_product_name}{COLOR_END} ]] {FAIL}FAILED!{COLOR_END}\n')
                    sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {addResp.json()}\n')
                    sys.exit()
                else:
                    if atc_response.json() == []:  # request was OK but did not add item to cart - wait/sleep and make POST again
                        sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: Response Empty! - Problem Adding to Cart! [[ {self.thread_text_color}{listed_product_name}{COLOR_END} ]] {FAIL}FAILED AGAIN EXITING!{COLOR_END}\n')  # CHECK THIS - DID ITEM ADD TO CART? MAKE POST AGAIN
                        sys.exit()
            sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: [[ {self.thread_text_color}{listed_product_name} - {str(self.item_color)} - {str(self.item_size)}{COLOR_END} ]] added to cart!\n')
        self.show_cookies(atc_response)
        self.start_webdriver(atc_response)

    def find_product(self):
        while self.product_found == 0:
            current_mobile_json = self.fetch_mobile_stock()
            for category in list(current_mobile_json['products_and_categories'].values()):
                for item in category:
                    if self.item_name.lower() in item['name'].lower():
                        self.product_found = 1
                        listed_product_name = item['name']
                        listed_product_id = item['id']
                        sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: [[ {self.thread_text_color}{listed_product_name}{COLOR_END} ]] {str(listed_product_id)} found ( MATCHING ITEM DETECTED )\n')
            if self.product_found != 1:
                sys.stdout.write(f'[[ {self.thread_text_color}{str(threading.current_thread().getName())}{COLOR_END} ]] {utc_to_est()} :: Reloading and reparsing page...\n')
                time.sleep(user_config.poll)
            else:
                color_id, size_id = self.find_product_variant(listed_product_name, listed_product_id)
                self.add_to_cart(listed_product_name, listed_product_id, color_id, size_id)

class ChromeDriverGetter:
    def __init__(self):
        self.latest_version = requests.request('GET', 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE').content.decode()
        if platform.system() == 'Windows':
            self.url = f'https://chromedriver.storage.googleapis.com/{self.latest_version}/chromedriver_win32.zip'
        elif platform.system() == 'Darwin':
            self.url = f'https://chromedriver.storage.googleapis.com/{self.latest_version}/chromedriver_mac64.zip'
        else:  # Linux
            self.url = f'https://chromedriver.storage.googleapis.com/{self.latest_version}/chromedriver_linux64.zip'

    def download(self):
        self.zip_file_name = 'chromedriver.zip'
        print(f'Downloading chromedriver zip ({self.latest_version})')
        response = requests.request('GET', self.url, stream=True)
        with open(self.zip_file_name, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024): 
                if chunk:
                    file.write(chunk)
        print('Download Complete')

    def unzip(self):
        print(f'Unzipping {self.zip_file_name}')
        zip_ref = zipfile.ZipFile(self.zip_file_name,'r')
        zip_ref.extractall(os.getcwd())
        zip_ref.close()
        chromedriver_binary_path = f'{os.getcwd()}/{zip_ref.infolist()[0].filename}'  # extracted file's name
        os.chmod(chromedriver_binary_path, 0o755)
        return chromedriver_binary_path

    def clean_up(self):
        print('Removing zip file if it exists')
        with contextlib.suppress(FileNotFoundError):
            os.remove(f'{os.getcwd()}/{self.zip_file_name}')


def utc_to_est():
    current = datetime.datetime.now()
    return f'{str(current)} EST'

if __name__ == '__main__':
    if len(glob.glob('*.zip')):
        for zipfile in glob.glob('*.zip'):
            os.remove(zipfile)
    if len(glob.glob('chromedriver*')) == 0:
        cdg = ChromeDriverGetter()
        cdg.download()
        chromedriver_executable_file = cdg.unzip()
        cdg.clean_up()
    else:
        chromedriver_executable_file = f'{os.getcwd()}/{glob.glob("chromedriver*")[0]}'  # assume there is only one filename match
    user_config = Config()
    assert len(user_config.productNames) == len(user_config.productColors) == len(user_config.productSizes) == len(user_config.productQuantities), 'Assertion Error: Product section lengths unmatched'
    for supreme_product_index in  range(0, len(user_config.productNames)):
        color_text = random.choice(list(colorCodes.values()))
        colorCodes = {key: val for key, val in colorCodes.items() if val != color_text}
        itemName = user_config.productNames[supreme_product_index].title()
        itemSize = user_config.productSizes[supreme_product_index].title()
        itemColor = user_config.productColors[supreme_product_index].title()
        itemQuantity = user_config.productQuantities[supreme_product_index]
        product_thread = threading.Thread(target=SupremeProduct, args=(itemName, itemColor, itemSize, itemQuantity, color_text, chromedriver_executable_file,))
        print(f'[[ {color_text}Thread-{str(supreme_product_index + 1)}{COLOR_END} ]] {color_text}{str(itemName)} :: {str(itemSize)} :: {str(itemColor)} :: {str(itemQuantity)} :: Thread initialized!{COLOR_END}')
        product_thread.start()
