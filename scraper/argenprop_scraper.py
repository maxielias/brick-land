from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

class ArgenPropData:
    """
    A class for scraping property data from ArgenProp website.

    Attributes:
        url (str): The URL of the property.
        list_of_urls (list): A list of URLs of multiple properties.
        source (str): The source of the property data.
        soup (BeautifulSoup): The BeautifulSoup instance for parsing HTML.

    Methods:
        create_soup_instance(url): Create a BeautifulSoup instance.
        create_project_brief(url, soup): Create a brief summary of the property.
        project_images(url, soup): Get the images of the property.
        available_apartments(url, soup): Get the available apartments.
        get_apartment_data(url, main_url): Retrieves data for a specific apartment.
        create_brief_list_of_projects(urls, n): Create a brief list of projects.
        compile_project_data(): Compiles all data for each project and its apartments.
    """

    def __init__(self, url=None, list_of_urls=None):
        self.url = url
        self.urls = list_of_urls
        self.source = 'argenprop'
        self.soup = None

    def create_soup_instance(self, url):
        """
        Create a BeautifulSoup instance.

        Args:
            url (str): The URL to create the BeautifulSoup instance for.

        Returns:
            BeautifulSoup: The BeautifulSoup instance.

        """
        request = requests.get(url)
        self.soup = BeautifulSoup(request.content, 'html.parser')
        return self.soup

    def create_project_brief(self, url=None, soup=None):
        """
        Create a brief summary of the property.

        Args:
            url (str): The URL of the property.
            soup (BeautifulSoup): The BeautifulSoup instance.

        Returns:
            str: The brief summary of the property.

        """
        data_dict = {}
        soup = self.soup
        data1 = soup.find('p', {'class': 'sidebar-top-info'}).text.strip() if soup.find('p', {'class': 'sidebar-top-info'}) else ''
        data2 = soup.find('p', {'class': 'sidebar-top-heading'}).text.strip() if soup.find('p', {'class': 'sidebar-top-heading'}) else ''
        data3 = soup.find('h2', {'class': 'sidebar-top-info'}).text.strip() if soup.find('h2', {'class': 'sidebar-top-info'}) else ''
        data4 = ''.join([s.text for s in soup.find_all('div', {'class': 'sidebar-details-item'})])
        lines = [line.strip() for line in data4.split('\n') if line.strip()]
        text_elements = [f"{lines[i]} {lines[i+1]}" for i in range(0, len(lines), 2)]
        data4 = ', '.join(text_elements) + '.'        
        section_list_icons = ''.join([s.text.replace('\n', '').replace('\t', '').lstrip() for s in soup.find_all('ul', {'class': 'section-list__icons'})]).split(' ')
        data5 = []
        for string in section_list_icons:
            if string != '':
                data5.append(string)
        data5 = ' '.join(data5)
        brief_text = data1 + ' ' + data2 + ' ' + data3 + ' ' + data4 + ' ' + data5
        if not brief_text:
            brief_text = 'nan'
        project_data = {
            'district': data1,
            'address': data2,
            'brief_text': brief_text,
        }
        return project_data
    
    def project_images(self, url=None, soup=None):
        """
        Get the images of the property.

        Args:
            url (str): The URL of the property.
            soup (BeautifulSoup): The BeautifulSoup instance.

        Returns:
            list: A list of image URLs for the property.

        """
        list_of_images = []
        soup = self.soup.find('ul', {'class': 'main__slider-photos'}).find_all('img')
        for img in soup:
            if img['data-popup-src']:
                list_of_images.append(img['data-popup-src'])
            else:
                list_of_images.append('nan')
        return list_of_images
    
    def available_apartments(self, url=None, soup=None):
        """
        Get the available apartments.

        Args:
            url (str): The URL of the property.
            soup (BeautifulSoup): The BeautifulSoup instance.

        Returns:
            list: A list of available apartment URLs.

        """
        available_apartments = []
        soup = BeautifulSoup(requests.get(url).content, 'html.parser').find_all('a')
        for item in soup:
            regex_pattern = re.compile(r'^\/emprendimientos\/[^/]+--\d{5,15}$')
            if re.match(regex_pattern, item['href']):
                available_apartments.append(item['href'])
        return available_apartments

    def get_apartment_data(self, url, main_url):
        """
        Retrieves data for a specific apartment from a given URL.

        Args:
            url (str): The URL of the apartment listing.
            main_url (str): The main URL of the website.

        Returns:
            dict: A dictionary containing apartment data.
        """
        apartment_main_data = []
        apartment_description = []
        apartment_other_data = []
        idx = f'https://argenprop.com{url}'
        soup = BeautifulSoup(requests.get(f'https://argenprop.com{url}').content, 'html.parser')
        address_floor = soup.find('h2', {'class': 'resume-primary'}).get_text().split(',')
        address = address_floor[0].strip()
        floor = address_floor[1].strip() if len(address_floor) > 1 else 'nan'
        try:
            price = soup.find('p', {'class': 'resume-price'}).get_text()
        except Exception as e:
            print(f'{e} for price apartment: {idx}')
            price = 'nan'
        try:
            location = soup.find('h2', {'class': 'resume-info-location'}).get_text().split('Venta en ')[1]
        except Exception as e:
            print(f'{e}, Skipping apartment {idx}')
            return None
        apmd = soup.find_all('div', {'class': 'resume__list-item'})
        for item in apmd:
            apartment_main_data.append(item.text.split('\n')[2].strip().replace('m\u00b2', 'm2') if item.text.split('\n')[2].strip() else 'nan')
        try:
            apartment_description = soup.find('div', {'class': 'section-description--content'}).text.strip().replace('\n', ' ').replace('m\u00b2', 'm2')
        except AttributeError:
            pass
        try:
            apartment_description = apartment_description.split('AVISO LEGAL')[0].strip().replace('\n', ' ')
        except:
            pass
        try:
            apartment_description = apartment_description.split('Para verlo')[0].strip().replace('\n', ' ')
        except AttributeError:
            pass
        apod = soup.find('div', {'class': 'main__details'}).find_all('li')
        for item in apod:
            apartment_other_data.append(re.sub(r'\s+', ' ', item.text.replace('\n', ' ').replace('•', '').strip().replace('m\u00b2', 'm2')) if
                                        re.sub(r'\s+', ' ', item.text.replace('\n', ' ').replace('•', '').strip().replace('m\u00b2', 'm2')) else 'nan')
        apartment_images = []
        apimg = soup.find('div', {'class': 'popupbox-footer-content'}).find_all('img')
        for img in apimg:
            apartment_images.append(img['data-popup-src'] if img['data-popup-src'] else 'nan')

        def extract_surface_m2(main_data_list, additional_data_list):
            """
            Extracts the number of square meters (m2) of surface from the provided lists.
            If not found in the first list, it searches in the second list.

            Args:
                main_data_list (list): A list containing main property data.
                additional_data_list (list): A list containing additional property data.

            Returns:
                str: The number of square meters, or 'nan' if not found.
            """
            pattern = re.compile(r'\b(\d{1,5})\s?m2\b', re.IGNORECASE)
            
            for item in main_data_list:
                match = pattern.search(item)
                if match:
                    return int(match.group(1))
            
            for item in additional_data_list:
                match = pattern.search(item)
                if match:
                    return int(match.group(1))
            
            return 'nan'
        
        def extract_rooms_and_bedrooms(data_list):
            """
            Extracts the number of ambientes and dormitorios from a list of property data.
            If one of the values is missing, it calculates it from the other.

            Args:
                data_list (list): A list containing property data.

            Returns:
                dict: A dictionary containing the number of ambientes and dormitorios.
            """
            rooms = None
            bedrooms = None
            
            for item in data_list:
                match_rooms = re.search(r'(\d{1,5})\s?ambientes', item, re.IGNORECASE)
                if match_rooms:
                    rooms = int(match_rooms.group(1))
                match_bedrooms = re.search(r'(\d{1,5})\s?dormitorios', item, re.IGNORECASE)
                if match_bedrooms:
                    bedrooms = int(match_bedrooms.group(1))

            if "Monomabiente" in apartment_main_data:
                rooms = 1
                bedrooms = 1
            elif rooms is None and bedrooms is not None:
                rooms = bedrooms + 1
            elif bedrooms is None and rooms is not None:
                bedrooms = rooms - 1
            
            return {
                'rooms': rooms if rooms is not None else 'nan',
                'bedrooms': bedrooms if bedrooms is not None else 'nan'
            }
        
        rooms_and_bedrooms = extract_rooms_and_bedrooms(apartment_main_data)

        apartment_description = apartment_description if apartment_description else "" + " " + ", ".join(apartment_main_data) + ", ".join(apartment_other_data) 
        
        return {
            'prop_url': idx,
            'prop_address': address,
            'prop_floor': floor,
            'prop_price': price,
            'prop_m2': extract_surface_m2(apartment_main_data, apartment_other_data),
            'prop_rooms': rooms_and_bedrooms['rooms'],
            'prop_bedrooms': rooms_and_bedrooms['bedrooms'],
            'prop_location': location,
            'prop_description': apartment_description,
            'prop_images': apartment_images
        }
    

    def compile_project_data(self):
        """
        Compiles all data for each project and its apartments.

        Returns:
            list: A list of dictionaries containing all compiled data for each project and its apartments.
        """
        compiled_data = []
        for i, project_url in enumerate(self.urls):
            print(f'Scraping project {i+1} from {len(self.urls)+1}:', project_url)
            self.create_soup_instance(project_url)
            project_data = self.create_project_brief()
            project_images = self.project_images()
            apartment_urls = self.available_apartments(url=project_url)
            apartments_data = []
            for apt_url in apartment_urls:
                apartments_data.append(self.get_apartment_data(url=apt_url, main_url=project_url))
            compiled_data.append({
                'project_url': project_url,
                'project_district': project_data['district'],
                'project_address': project_data['address'],
                'project_description': project_data['brief_text'],
                'project_images': project_images,
                'properties': apartments_data
            })
        return compiled_data


if __name__ == '__main__':
    import json

    urls = pd.read_csv('data/raw/list_of_all_urls.csv')
    list_of_urls = urls.loc[urls['URL'].str.contains('argenprop'), 'URL'].tolist()
    apd = ArgenPropData(list_of_urls=list_of_urls)
    compiled_data = apd.compile_project_data()
    with open('data/raw/argenprop_data.json', 'w') as json_file:
        json.dump(compiled_data, json_file, indent=4)
