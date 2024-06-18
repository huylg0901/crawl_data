import requests
import pandas as pd
from tqdm import tqdm
import numpy as np
import time
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_random_user_agent():
    with open('user_agents.txt', 'r') as file:
        user_agents = file.readlines()
    return random.choice(user_agents).strip()

class OpenStreetMap:
    def __init__(self):
        random_user_agent = get_random_user_agent()
        self.proxies = ["your_proxy"]
        self.current_proxy_index = 0
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent': random_user_agent,
            'referer': 'https://nominatim.openstreetmap.org/ui/search.html'
        })

    def get_latlog(self, address):
        proxy = {'https': f'http://{self.proxies[self.current_proxy_index]}'}
        url = f"https://nominatim.openstreetmap.org/search.php?q={address}&limit=1&format=json"
        try:
            logging.info(f"Requesting data for address: {address}")
            response = self.session.get(url, proxies=proxy, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logging.warning("Request timed out. Retrying...")
            return self.get_latlog(address)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            if response.status_code == 429:
                logging.info("Rate limit exceeded, changing proxy.")
                #self.changer_proxy()
                return self.get_latlog(address)
            if response.status_code == 503:
                time.sleep(10)
            raise

    def changer_proxy(self):
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        logging.info(f"Proxy changed to {self.proxies[self.current_proxy_index]}")
        time.sleep(1)  # Short pause after changing proxy

    def process_address(self, i, address, df):
        try:
            data = self.get_latlog(address)
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                df.loc[i, 'lat_address'] = lat
                df.loc[i, 'lon_address'] = lon
                logging.info(f"Processed {address}: Latitude = {lat}, Longitude = {lon}")
        except Exception as e:
            logging.error(f"Error processing address {address}: {e}")

    def main(self):
        df = pd.read_csv("input.csv")
        df['lat_address'] = np.nan
        df['lon_address'] = np.nan

        for i, address in tqdm(enumerate(df['address']), total=len(df), desc="Processing addresses"):
            self.process_address(i, address, df)

        df.to_excel("output.xlsx", index=False)

if __name__ == '__main__':
    osm = OpenStreetMap()
    osm.main()
