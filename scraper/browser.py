import cloudscraper


class Browser():
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def get(self, url):
        try:
            return self.scraper.get(url)
        except Exception as e:
            print(f"Error getting url: {e}")
            return None

    def post(self, url, data):
        return self.scraper.post(url, data)

    def get_text(self, url):
        return self.scraper.get(url).text