import sys

import pandas as pd

from scraper import utils
from scraper.browser import Browser
from scraper.scraper2 import URLScraper


def main(url):
    # base_url = utils.parse_zonaprop_url(url)
    print(f'Running scraper for {base_url}')
    print(f'This may take a while...')
    # browser = Browser()
    scraper = URLScraper(base_url)
    url_scraper = URLScraper(url)
    url_scraper.scrape_and_save()
    # urls = scraper.get_posting_urls()
    # df = pd.DataFrame(estates)
    print('Scraping finished !!!')
    print('Saving data to csv file')
    # filename = utils.get_filename_from_datetime(base_url, 'csv')
    # utils.save_df_to_csv(df, filename)
    # print(f'Data saved to {filename}')
    # print('Scrap finished !!!')

if __name__ == '__main__':
    # url = sys.argv[1]
    base_url = 'https://www.zonaprop.com.ar/emprendimientos-capital-federal.html' # if url is None else url
    main(base_url)