import requests
from bs4 import BeautifulSoup
import pandas as pd

base_url = "https://vi.wikipedia.org"

category_url = f"{base_url}/wiki/Th%E1%BB%83_lo%E1%BA%A1i:Danh_s%C3%A1ch_x%C3%A3_t%E1%BA%A1i_Vi%E1%BB%87t_Nam"

response = requests.get(category_url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    div_content = soup.find('div', class_='mw-category')

    province_links = []
    if div_content:
        links = div_content.find_all('a')

        for link in links:
            province_name = link.get_text(strip=True)
            province_link = base_url + link['href']
            province_links.append((province_name, province_link))

    data = []

    for province_name, province_link in province_links:
        province_response = requests.get(province_link)

        if province_response.status_code == 200:
            province_soup = BeautifulSoup(province_response.content, 'html.parser')

            tables = province_soup.find_all('table', class_='wikitable')

            if tables:
                for table in tables:
                    rows = table.find_all('tr')

                    for row in rows:
                        cells = row.find_all('td')

                        if len(cells) > 0:
                            link_tag = cells[0].find('a', href=True)
                            link_tag1 = cells[1].find('a', href=True)
                            if link_tag:
                                commune_name = link_tag.get_text(strip=True)
                                ward_name = link_tag1.get_text(strip=True)
                                commune_link = base_url + link_tag['href']

                                commune_response = requests.get(commune_link)

                                if commune_response.status_code == 200:
                                    commune_soup = BeautifulSoup(commune_response.content, 'html.parser')

                                    infobox = commune_soup.find('table', class_='infobox')

                                    if infobox:
                                        lat_row = infobox.find('span', class_='latitude')
                                        lon_row = infobox.find('span', class_='longitude')

                                        if lat_row and lon_row:
                                            latitude = lat_row.get_text(strip=True)
                                            longitude = lon_row.get_text(strip=True)

                                            # Append the data to the list
                                            data.append({
                                                'Province': province_name,
                                                'Ward': ward_name,
                                                'Commune': commune_name,
                                                'Latitude': latitude,
                                                'Longitude': longitude
                                            })

    df = pd.DataFrame(data)

    df.to_excel('final_lat_long.xlsx', index=False)
else:
    print(f"Failed to retrieve the category page. Status code: {response.status_code}")
