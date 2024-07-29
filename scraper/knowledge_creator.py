import os
from bs4 import BeautifulSoup
from browser import Browser
import json
import re
from fpdf import FPDF

class KnowledgeCreator:
    def __init__(self, browser, directory=None):
        self.browser = browser
        self.directory = directory

    def read_text_files(self, list_of_files=None):
        all_urls = []
        if list_of_files:
            for file in list_of_files:
                with open(file, 'r', encoding='utf-8') as f:
                    urls = f.readlines()
                    urls = [url.strip() for url in urls]
                    all_urls.extend(urls)
        else:
            for filename in os.listdir(self.directory):
                if filename.endswith('.txt'):
                    with open(os.path.join(self.directory, filename), 'r', encoding='utf-8') as file:
                        urls = file.readlines()
                        urls = [url.strip() for url in urls]
                        all_urls.extend(urls)
        return all_urls

    def create_unique_url_set(self, list_of_files=None):
        all_urls = self.read_text_files(list_of_files=list_of_files)
        unique_urls = set(all_urls)
        print(f"Number of unique urls: {len(unique_urls)}")
        return unique_urls
    
    def get_text_from_url(self, url):
        print(f"Scraping {url}")
        try:
            url_request = self.browser.get(url).content
            soup = BeautifulSoup(url_request, 'lxml')
            paragraphs = soup.find_all('p')
            article = '\n'.join([p.get_text() for p in paragraphs])
            article = re.sub(r'\s+', ' ', article)
            article = self.remove_emojis(article)
            return article
        except Exception as e:
            print(f"Error scraping url: {e}")
            pass
    
    def remove_emojis(self, text):
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    def create_article_dicts(self, list_of_files=None):
        unique_urls = self.create_unique_url_set(list_of_files=list_of_files)
        articles = []
        for url in unique_urls:
            article_text = self.get_text_from_url(url)
            articles.append({'url': url, 'article_text': article_text})
        print(f"Number of articles scraped: {len(articles)}")
        return articles
    
    def save_articles_to_json(self, articles, output_file):
        dict_articles = {article['url']: article['article_text'] for article in articles}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict_articles, f, indent=4)
        print('Json file saved')

    def save_articles_to_file(self, articles, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write(f"'{article['url']}':\n")
                f.write(f"'{article['article_text']}'\n")
                f.write("#################\n")
        print('Text file saved')

    def save_articles_to_pdf(self, articles, output_dir, font='DejaVu',
                             font_path='assets/fonts/DejaVu_Sans/DejaVuSansCondensed.ttf'):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for idx, article in enumerate(articles):
            url = article['url']
            article_text = article['article_text']
            if article_text is not None:
                file_name = self.get_valid_file_name(url, idx)[0:20]
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_font(font, '', font_path, uni=True)
                pdf.set_font(font, '', 14)
                pdf.multi_cell(0, 10, article_text)
                pdf_file_path = os.path.join(output_dir, f"{file_name}.pdf")
                pdf.output(pdf_file_path)
                print(f"Saved PDF: {pdf_file_path}")
    
    def get_valid_file_name(self, url, idx):
        try:
            file_name = url.split('/')[-1]
            if not file_name:
                file_name = url.split('/')[-2]
            if not file_name:
                file_name = f"article_{idx}"
        except IndexError:
            file_name = f"article_{idx}"
        file_name = re.sub(r'\W+', '_', file_name)  # Replace non-alphanumeric characters with underscores
        return file_name

# Usage example
if __name__ == '__main__':
    directory_paths = ['data/raw/real_state_advice_urls.txt', 'data/raw/scraped_real_state_advice_urls.txt']
    browser_instance = Browser()
    knowledge_creator = KnowledgeCreator(browser=browser_instance)
    unique_urls = knowledge_creator.create_unique_url_set(list_of_files=directory_paths)
    articles = knowledge_creator.create_article_dicts(list_of_files=directory_paths)
    
    output_file = 'data/raw/articles.txt'
    knowledge_creator.save_articles_to_file(articles, output_file)

    json_output_file = 'data/raw/json_articles.json'
    knowledge_creator.save_articles_to_json(articles, json_output_file)

    pdf_output_dir = 'data/processed/pdf_files'
    knowledge_creator.save_articles_to_pdf(articles, pdf_output_dir)

    print("Articles saved to file successfully!")
