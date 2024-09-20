import requests
from datetime import datetime
import json
from location_info import locations
from HouseSigma_Realtor.crawler.realtor import Realtor
from HouseSigma_Realtor.configurations.config import USERNAME, PASSWORD
from HouseSigma_Realtor.utils.update_json_file import update_file, update_broker_list

class HouseSigma:
    def __init__(self):
        self.cookies = {
            'storeAsyc_desk': '%7B%22access_token%22%3A%222024091770uu3c0npp20t35hkd8pqjsi02%22%7D'
        }
        self.headers = {
            "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
            "sec-ch-ua-mobile": "?0",
            "Authorization": "Bearer 20240820u13lknhu4cleq8631oarilm8r8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "HS-Client-Type": "desktop_v7",
            "HS-Client-Version": "7.21.19",
            "Referer": "https://housesigma.com/",
            "sec-ch-ua-platform": "\"Windows\""
        }
        self.request = requests.Session()
        self.all_properties = list()
        self.realtor = Realtor()

    def login(self):
        """
            Sign-In To HouseSigma
        """

        signing_url = 'https://housesigma.com/bkv2/api/auth/user/signin'
        signing_payload = {
            'email': USERNAME,
            'lang': "en_US",
            'login_type': "normal",
            'pass': PASSWORD,
            'province': "ON",
            'token': '20240820u13lknhu4cleq8631oarilm8r8'
        }

        self.request.post(
            url=signing_url,
            data=json.dumps(signing_payload),
            headers=self.headers
        )

    def get_listing(self):
        """
            Iterate all locations and its all listing one by one
        """

        listing_url = 'https://housesigma.com/bkv2/api/search/mapsearchv3/list'

        for location_name in locations.keys():
            done_listing = 0

            # listing Payload
            payload = {
                "lang": "en_US",
                "province": "ON",
                "list_type": [1],
                "rent_list_type": [2],
                "listing_days": 1,
                "sold_days": 1,
                "de_list_days": 90,
                "basement": [],
                "open_house_date": 0,
                "description": "",
                "listing_type": ["all"],
                "max_maintenance_fee": 0,
                "house_type": ["all"],
                "building_age_min": 999,
                "building_age_max": 0,
                "price": [0, 6000000],
                "front_feet": [0, 100],
                "square_footage": [0, 4000],
                "bedroom_range": [0],
                "bathroom_min": 0,
                "garage_min": 0,
                "zoom": 13,
                "page": 1,
                "sort_type": 1,
                "ts": str(datetime.now().timestamp()).split('.')[0]
            }
            payload.update(locations[location_name])  # set longitudes and latitudes of each location

            while True:  # loop for pagination till last page
                resp = self.request.post(
                    url=listing_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    cookies=self.cookies
                )
                page_listing = resp.json()['data'].get('houseList', list())

                for listing in page_listing:
                    address_id = listing['id_address']
                    listing_id = listing['id_listing']

                    self.fetch_details(address_id, listing_id)
                    print(location_name, 'One property done')

                done_listing += resp.json()['data']['rowCount']
                if done_listing == resp.json()['data']['total']:
                    break

                payload['page'] = payload['page'] + 1
                print('Next Page')

    def fetch_details(self, address_id, listing_id):
        """
            Fetching details of a property
        """
        details_api = 'https://housesigma.com/bkv2/api/listing/info/detail_v2'
        detail_payload = {
            "lang": "en_US",
            "province": "ON",
            "id_address": address_id,
            "id_listing": listing_id,
            "event_source": "",
            "ts": str(datetime.now().timestamp()).split('.')[0]
        }
        while True:  # loop to handle accept agreement issue

            detail_resp = self.request.post(
                url=details_api,
                headers=self.headers,
                data=json.dumps(detail_payload),
                cookies=self.cookies
            )
            info = detail_resp.json()['data']
            item = dict()
            item['location'] = f"{info['house']['address']} {info['house']['municipality_name']} - {info['house']['community_name']}"
            if not info['house']['address_navigation']:
                # Login again to fetch data properly
                self.login()
                print('SignIn Again')
            else:
                break

        item['history'] = list()
        all_history = info['listing_history']
        for history in all_history:
            history_obj = self.parse_history(history)
            item['history'].append(history_obj)

        seo_address = info['house']['seo_address']

        # fetch property url from realtor
        realtor_url = self.realtor.get_property(seo_address)
        if realtor_url:
            realtor_url = 'https://www.realtor.ca' + realtor_url

            # fetch broker details from realtor
            brokers = self.realtor.fetch_broker(realtor_url)
            item['brokers'] = brokers

            # update broker's database
            update_broker_list(brokers)

            # update listing database
            update_file(item)

    def parse_history(self, history):
        """
            Parse History data of a property
        """
        history_data = dict()
        history_data['start_date'] = history['date_start']
        history_data['end_date'] = history['date_end']
        if history['price_sold']:
            history_data['price'] = history['price_sold']
        else:
            history_data['price'] = history['price']
        history_data['event'] = history['status']
        history_data['id'] = history['ml_num']

        return history_data

