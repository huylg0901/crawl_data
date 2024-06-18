import requests
import pandas as pd
import threading
from tqdm import tqdm
import numpy as np
import time
import logging
import random

# Set up logging to both file and console with utf-8 encoding
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler with utf-8 encoding
file_handler = logging.FileHandler('detailed_request_logs.txt', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Console handler with utf-8 encoding
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_random_user_agent():
    with open('user_agents.txt', 'r', encoding='utf-8') as file:
        user_agents = file.readlines()
    return random.choice(user_agents).strip()

class OpenStreetMap:
    def __init__(self):
        random_user_agent = get_random_user_agent()
        self.proxies = ["your_proxy"]
        self.current_proxy_index = 0
        self.lock = threading.Lock()
        self.num_threads = 3
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent': random_user_agent,
            'referer': 'https://nominatim.openstreetmap.org/ui/search.html'
        })

    def measure_request(self, url, proxy=None):
        timings = {}

        # Layer 7 - Application: Prepare the HTTP request
        start = time.time()
        request = requests.Request('GET', url)
        prepared_request = request.prepare()
        timings['application_preparation'] = time.time() - start

        # Layer 3 - Network: DNS Resolution and Proxy Setup (if any)
        start = time.time()
        if proxy:
            self.session.proxies.update({
                'http': proxy,
                'https': proxy
            })
        timings['network_dns_proxy_setup'] = time.time() - start

        # Layer 4 - Transport (and some of layer 5 Session, layer 6 Presentation in TLS setup if HTTPS)
        start = time.time()
        response = self.session.send(prepared_request)
        timings['transport_session_presentation'] = time.time() - start

        # Time to first byte (TTFB) - relevant for network requests
        start = time.time()
        first_byte = response.content[0:1]
        timings['time_to_first_byte'] = time.time() - start

        # Complete response time
        start = time.time()
        content = response.content
        timings['content_download'] = time.time() - start

        # Logging detailed timing information
        logging.info(f"Request URL: {url}")
        if proxy:
            logging.info(f"Proxy used: {proxy}")
        logging.info(f"Timing details: {timings}")

        # Returning response and timings for further processing
        return response, timings

    def get_latlog(self, address):
        proxy = f'http://{self.proxies[self.current_proxy_index]}'
        url = f"https://nominatim.openstreetmap.org/search.php?q={address}&polygon_geojson=1&format=jsonv2"
        try:
            logging.info(f"Requesting data for address: {address} using proxy {self.proxies[self.current_proxy_index]}")
            response, timings = self.measure_request(url, proxy)
            logging.info(f"Response received for {address} in {sum(timings.values()):.2f} seconds")
            return response.json(), timings
        except requests.exceptions.Timeout:
            logging.warning("Request timed out. Retrying...")
            return self.get_latlog(address)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            if response.status_code == 429:
                logging.info("Rate limit exceeded, changing proxy.")
               # self.changer_proxy()
                return self.get_latlog(address)
            raise

    # def changer_proxy(self):
    #     with self.lock:
    #         self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
    #         logging.info(f"Proxy changed to {self.proxies[self.current_proxy_index]}")
    #         time.sleep(1)  # Short pause after changing proxy

    def process_address(self, i, address, df):
        start_time = time.time()
        try:
            data, timings = self.get_latlog(address)
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                with self.lock:
                    df.loc[i, 'lat_address'] = lat
                    df.loc[i, 'lon_address'] = lon
                processing_time = time.time() - start_time
                logging.info(f"Processed {address}: Latitude = {lat}, Longitude = {lon} in {processing_time:.2f} seconds with detailed timings {timings}")
        except Exception as e:
            logging.error(f"Error processing address {address}: {e}")

    def main(self):
        df = pd.read_csv("input.csv")
        df['lat_address'] = np.nan
        df['lon_address'] = np.nan

        threads = []
        for i, address in tqdm(enumerate(df['address']), total=len(df), desc="Processing addresses"):
            while threading.active_count() > self.num_threads:
                time.sleep(1)
            thread = threading.Thread(target=self.process_address, args=(i, address, df))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        df.to_excel("output.xlsx", index=False)

if __name__ == '__main__':
    osm = OpenStreetMap()
    osm.main()
