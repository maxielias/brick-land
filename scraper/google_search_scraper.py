import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
import chardet
from autoscraper import AutoScraper
import os

class RealStateDataScraper:
    def __init__(self, query_list, num_results=10):
        self.query_list = query_list
        self.num_results = num_results
        self.urls = []

    def google_search(self):
        """Performs Google searches for all queries and stores the URLs."""
        try:
            for query in self.query_list:
                print(f"Searching for: {query}")
                # Append 'site:.ar' to search only Argentine websites
                query = f"{query} site:.ar"
                for url in search(query, num_results=self.num_results, lang='es'):
                    self.urls.append(url)
        except Exception as e:
            print(f"An error occurred during the Google search: {e}")

    def detect_encoding(self, content):
        """Detects the encoding of the content."""
        result = chardet.detect(content)
        return result['encoding']

    def scrape_url_content(self, url):
        """Scrapes the content of a single URL."""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                encoding = self.detect_encoding(response.content)
                soup = BeautifulSoup(response.content.decode(encoding), 'html.parser')
                paragraphs = soup.find_all('p')
                text = "\n".join([para.get_text() for para in paragraphs])
                return text
            else:
                print(f"Failed to retrieve content from {url}, status code: {response.status_code}")
                return self.scrape_alternative(url)
        except Exception as e:
            print(f"Failed to scrape {url} with requests: {e}")
            return self.scrape_alternative(url)

    def scrape_alternative(self, url):
        """Alternative method to scrape the content of a single URL using AutoScraper."""
        try:
            # Initialize AutoScraper
            scraper = AutoScraper()
            
            # We need to provide the URL and a list of elements we want to scrape.
            # For this example, we will use the same URL and the desired content.
            response = requests.get(url)
            if response.status_code == 200:
                encoding = self.detect_encoding(response.content)
                soup = BeautifulSoup(response.content.decode(encoding), 'html.parser')
                paragraphs = soup.find_all('p')
                wanted_list = [para.get_text() for para in paragraphs[:3]]  # Take first 3 paragraphs as example
                
                # Build the scraper
                scraper.build(url, wanted_list)
                
                # Get the results
                result = scraper.get_result_similar(url)
                text = "\n".join(result)
                return text
            else:
                print(f"Failed to retrieve content from {url} for AutoScraper, status code: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Failed to scrape {url} with AutoScraper: {e}")
            return ""

    def scrape_all_urls(self):
        """Scrapes content from all stored URLs and returns it as a list of dictionaries."""
        results = []
        for idx, url in enumerate(self.urls):
            print(f"Scraping URL {idx + 1}/{len(self.urls)}: {url}")
            content = self.scrape_url_content(url)
            results.append({'url': url, 'content': content})
            time.sleep(1)  # Adding delay to avoid being blocked
        return results

    def get_unique_results(self):
        """Removes duplicate URLs and returns a dictionary with unique URLs and their contents."""
        unique_urls = set(self.urls)
        unique_results = []
        for url in unique_urls:
            content = self.scrape_url_content(url)
            unique_results.append({'url': url, 'content': content})
        return unique_results

    def save_results_to_file(self, results, file_name):
        """Saves the scraped results to a text file."""
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(f"URL: {result['url']}\n")
                f.write(f"Content:\n{result['content']}\n")
                f.write("="*80 + "\n")

    def save_urls_to_file(self, file_name):
        """Saves the scraped URLs to a text file."""
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, 'w', encoding='utf-8') as f:
            for url in self.urls:
                f.write(f"{url}\n")

# Example usage
if __name__ == "__main__":
    queries = [
        "Consejos para comprar departamentos en pozo",
        "Tips para invertir en proyectos inmobiliarios en pozo",
        "Guía para comprar propiedades en pozo",
        "Recomendaciones para adquirir inmuebles en pozo",
        "Mejores prácticas para comprar de pozo",
        "Errores comunes al comprar de pozo y cómo evitarlos",
        "Aspectos a considerar al comprar departamentos en pozo",
        "Ventajas y desventajas de comprar propiedades en pozo",
        "Experiencias de compra de inmuebles en pozo",
        "Checklist para comprar un departamento en pozo"
    ]

    num_results = 10  # Set the number of results to retrieve

    scraper = RealStateDataScraper(query_list=queries, num_results=num_results)
    scraper.google_search()
    
    # Save all URLs to a file
    scraper.save_urls_to_file(file_name='data/raw/scraped_real_state_advice_urls.txt')
    
    unique_results = scraper.get_unique_results()
    
    # Save the unique results to a file
    scraper.save_results_to_file(unique_results, file_name='data/raw/scraped_articles_data.txt')
