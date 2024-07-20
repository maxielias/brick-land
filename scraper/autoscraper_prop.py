import re
import pandas as pd
import math
from autoscraper import AutoScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time


class AutoScraperProp:
    """
    A class for scraping data from various real estate websites.
    """

    def __init__(self):
        """
        Initializes an instance of the AutoScraperProp class.
        """
        self.scraper = AutoScraper()
        self.page = 1
        self.driver = None
        self.source_page = {
            'argenprop': ['https://argenprop.com/emprendimientos/capital-federal?pagina-1',
                            re.compile(r'\b(\d{1,5})\b Emprendimientos en Capital Federal'),
                            r'\b(\d{1,5})\b', 20, re.compile(r'^/emprendimientos/emprendimiento-en[-a-z]*--(\d{5,15})$'), 'https://argenprop.com'],
            'zonaprop': ['https://www.zonaprop.com.ar/emprendimientos-capital-federal-pagina-1.html',
                            re.compile(r'\b(\d{1,5}.\d{1,5})\b Desarrollos inmobiliarios en venta - Propiedades e inmuebles en Capital Federal'),
                            r'\d{1,5}.\d{1,5}', 20, re.compile(r'^\/propiedades\/emprendimiento\/[\s\d\w-]{1,100}-\d{5,15}.html$'), 'https://www.zonaprop.com.ar'],
            'meli': ['https://inmuebles.mercadolibre.com.ar/departamentos/emprendimientos/capital-federal/_Desde_0_NoIndex_True',
                        re.compile(r'\b(\d{1,5})\b resultados', re.IGNORECASE), r'\b(\d{1,5})\b', 48,
                        re.compile(r'^https:\/\/departamento\.mercadolibre\.com\.ar\/MLA-(\d{5,15})-.*$'), ''],
            'mudafy': ['https://mudafy.com.ar/venta/emprendimientos/caba/1-p',
                        re.compile(r'\b(\d{1,5})\b resultados', re.IGNORECASE), r'\b(\d{1,5})\b', 22,
                        re.compile(r'^\/emprendimiento\/[\s\d\w-]{1,100}-\d{5,15}$'), 'https://mudafy.com.ar'],            
        }
    
    def get_selenium_driver(self):
        """
        Creates a Selenium WebDriver instance.
        """
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver
    
    def selenium_webpage_instance(self, url, driver=None):
        """
        Creates a Selenium instance and opens the specified URL.

        Args:
            url (str): The URL of the webpage to open.
            driver (WebDriver, optional): The Selenium WebDriver instance to use. If not provided, a new WebDriver instance will be created.

        Returns:
            None

        """
        self.get_selenium_driver()
        self.driver.get(url)
        self.driver.implicitly_wait(10)
        print('Selenium instance created.')
    
    def get_number_of_pages_with_selenium(self, url, tags):
        """
        Get the number of pages using Selenium.

        Args:
            url (str): The URL of the webpage to scrape.
            tags (str or list): The HTML tags or tag pattern to search for the page number.
            pattern (str): The regex pattern to extract the page number.

        Returns:
            int: The number of pages found.

        """
        if isinstance(tags, list):
            tags = tags[0]
        self.selenium_webpage_instance(url=url, driver=self.driver)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser').text.strip()
        string_with_page_number = re.findall(tags, soup)
        return int(string_with_page_number[0])
    
    def get_number_of_pages_with_requests(self, url, tags):
        """
        Get the number of pages using Requests.

        Args:
            url (str): The URL of the webpage to scrape.
            tags (str or list): The HTML tags or tag pattern to search for the page number.
            pattern (str): The regex pattern to extract the page number.

        Returns:
            int: The number of pages found.

        """
        if isinstance(tags, list):
            tags = tags[0]
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser').text.strip()
        string_with_page_number = re.findall(tags, soup)
        return int(string_with_page_number[0])
    
    def get_number_of_pages(self, source, tags=None, number_of_posts_per_page=None, digit_pattern=None, save_scaper=True):
        """
        Gets the number of pages from the website.

        This function scrapes the website to retrieve the number of pages available.

        Returns:
            int: The number of pages available.
        """
        source_url, page_tag, pattern, n, url_tag, main_url = self.source_page[source]
        if tags is None:
            tags = [page_tag]
        if number_of_posts_per_page is None:
            number_of_posts_per_page = n   
        if digit_pattern is None:
            digit_pattern = pattern 
        url = source_url
        try:
            number_of_posts = self.scraper.build(url, tags)
            string_digit = re.findall(pattern, number_of_posts[0])[0]
            string_to_integer = int(''.join([i for i in string_digit if i.isdigit()]))
            number_of_pages = math.ceil(string_to_integer / number_of_posts_per_page)
        except Exception as e:
            print(f'Error: {e}')
            print("Using Requests to get the number of pages.")
            try:
                number_of_pages = self.get_number_of_pages_with_requests(url=url, tags=tags)
            except Exception as e:
                print(f'Error: {e}')
                print("Using Selenium to get the number of pages.")
                number_of_pages = self.get_number_of_pages_with_selenium(url=url, tags=tags)
        return number_of_pages
    
    def get_urls_from_website(self, source, number_of_pages, tags=None):
        """
        Scrapes the website to retrieve a list of estates.

        This function scrapes the website to retrieve a list of estates.

        Returns:
            list: A list of estates scraped from the website.
        """
        print(f'Getting urls from website...{source}')
        list_of_urls = []
        # number_of_pages = 2
        for p in range(1, number_of_pages + 1):
            print(f'Scraping page {p}.')
            tags = [self.source_page[source][4]]
            main_url = self.source_page[source][5]
            if p == 1:
                url = self.source_page[source][0]
                urls = self.scraper.build(url, tags)
            else:
                if source == 'argenprop':
                    url = re.sub(re.compile(r'(pagina-)(\d{1,10})'), rf'pagina-{p}', url)
                    urls = self.scraper.get_result_similar(url)
                elif source == 'zonaprop':
                    url = re.sub(re.compile(r'(pagina-)(\d{1,10})'), rf'pagina-{p}', url)
                    urls = self.scraper.get_result_similar(url)
                elif source == 'meli':
                    url = re.sub(re.compile(r'(_Desde_)(\d{1,10})(_NoIndex_True)'), rf'_Desde_{(p-1)*48}_NoIndex_True', url)
                    urls = self.scraper.get_result_similar(url)
                elif source == 'mudafy':
                    url = re.sub(re.compile(r'(\d{1,10})-p'), rf'{p}-p', url)
                    urls = self.scraper.get_result_similar(url)
            urls = [main_url + url for url in urls]
            list_of_urls.append(urls)
            time.sleep(1)
        return list_of_urls
    
    def save_list_of_urls(self, filename, list_of_all_urls):
        """
        Saves the list of URLs to a CSV file.

        Args:
            filename (str): The name of the file to save the list of URLs.
            list_of_urls (list): The list of URLs to save.

        Returns:
            None
        """
        if isinstance(list_of_all_urls[0], list):
            print('Flattening list of URLs...')
            df_list_of_urls = []
            for urls in list_of_all_urls:
                for url in urls:
                    df_list_of_urls.append(url)
            print(f'Total URLs after flattening: {len(df_list_of_urls)}')
        df = pd.DataFrame(df_list_of_urls, columns=['URL'])
        df.to_csv(filename, index=False)
        print(f'{len(df_list_of_urls)} URLs saved to {filename}.')
    
    def main(self, filename, list_of_sources=None):
        """
        Main function to scrape the website.

        Args:
            source (str): The source of the website to scrape.
            filename (str): The name of the file to save the list of URLs.

        Returns:
            None
        """
        list_of_all_urls = []
        if list_of_sources is None:
            list_of_sources = self.source_page.keys()
        for src in list_of_sources:
            number_of_pages = self.get_number_of_pages(source=src)
            list_of_urls = self.get_urls_from_website(source=src, number_of_pages=number_of_pages)
            list_of_all_urls.extend(list_of_urls)
        if self.driver:
            self.driver.quit()
        self.save_list_of_urls(filename, list_of_all_urls)
        print('All websites scraped!')


if __name__ == '__main__':
    autoscraper = AutoScraperProp()
    autoscraper.main(filename='data/raw/list_of_all_urls.csv')
    if autoscraper.driver:
        autoscraper.driver.quit()
