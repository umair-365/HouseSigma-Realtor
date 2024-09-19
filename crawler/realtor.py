import requests
import scrapy
from base64 import b64decode
from datetime import datetime
import json
from HouseSigma_Realtor.configurations.config import ZYTE_API_KEY


class Realtor:
    sh = {
        'st': 'street',
        'ave': 'avenue',
        'rd': 'road',
        'dr': 'drive',
        'cres': 'crescent',
        'blvd': 'boulevard',
        'grve': 'grove',
    }

    def fetch_broker(self, url):
        """
            Fetch Broker Details from Given URL
        """
        print('Fetching Broker Info From', url)
        while True:
            try:
                api_response = requests.post(
                    "https://api.zyte.com/v1/extract",
                    auth=(ZYTE_API_KEY, ""),
                    timeout=20,
                    json={
                        "url": url,
                        "httpResponseBody": True,
                        "customHttpRequestHeaders":
                            [
                                {'name': 'request-id', 'value': '|auHWs.ZbZLW'},
                                {'name': 'accept', 'value': '*/*'},
                                {'name': 'accept-language', 'value': 'en-US,en;q=0.9'},
                                {'name': 'content-type', 'value': 'application/json; charset=UTF-8'},
                                {'name': 'origin', 'value': 'https://www.realtor.ca'},
                                {'name': 'priority', 'value': 'u=1, i'},
                                {'name': 'referer', 'value': 'https://www.realtor.ca/realtor-search-results'},
                                {'name': 'user-agent', 'value': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}

                            ]
                    },
                )

                if api_response.status_code == 200:
                    break
                else:
                    print('Retrying to fetch response')
            except:
                print('Retrying to fetch response')

        http_response_body = b64decode(api_response.json()["httpResponseBody"]).decode()
        response = scrapy.Selector(text=http_response_body)

        # Fetch All Brokers
        realtors = [
            v for v in response.css('#propertyDetailsRealtorsCon > span') if 'realtorCard' in v.css('::attr(id)').extract_first()
        ]

        brokers_info = list()
        for realtor in realtors:
            item = dict()
            item['name'] = realtor.css('.realtorCardName ::text').extract_first()
            item['website'] = realtor.css('.realtorCardBottomLeft a ::attr(href)').extract_first()
            item['timestamp'] = str(datetime.now()).split('.')[0]
            item.update({f'mobile {_+1}':v for _, v in enumerate(realtor.css('.realtorCardPhone ::text').extract())})
            brokers_info.append(item)

        return brokers_info

    def remove_short_forms(self, location):
        location = ' '.join([v if not self.sh.get(v, '') else self.sh[v] for v in location.split(' ')])
        return location

    def get_property(self, location):
        """
            Fetch Property URL for Given Location
        """
        print('Fetching Realtor Url For', location)
        url = 'https://www.realtor.ca/Services/Actions.asmx/GetAutocompleteResults'
        location = location.replace('-', ' ')
        location = self.remove_short_forms(location)

        # property payload
        body = {
            "query": ' '.join(location.split(' ')[:2]),
            "includeLocations": False,
            "lat": "",
            "lon": "",
            "cultureId": 1,
            "appMode": 1
        }

        while True:  # loop to get suggestions
            while True:  # loop to fetch success response
                try:
                    api_response = requests.post(
                        "https://api.zyte.com/v1/extract",
                        auth=(ZYTE_API_KEY, ""),
                        timeout=20,
                        json={
                            "url": url,
                            "httpResponseBody": True,
                            "httpRequestText": json.dumps(body),
                            "httpRequestMethod": "POST",
                            "customHttpRequestHeaders":
                                [
                                    {'name': 'request-id', 'value': '|auHWs.ZbZLW'},
                                    {'name': 'accept', 'value': '*/*'},
                                    {'name': 'accept-language', 'value': 'en-US,en;q=0.9'},
                                    {'name': 'content-type', 'value': 'application/json; charset=UTF-8'},
                                    {'name': 'origin', 'value': 'https://www.realtor.ca'},
                                    {'name': 'priority', 'value': 'u=1, i'},
                                    {'name': 'referer', 'value': 'https://www.realtor.ca/realtor-search-results'},
                                    {'name': 'user-agent', 'value': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}

                                ]
                        },
                    )
                    if api_response.status_code == 200:
                        break
                    else:
                        print('Retrying To Fetch Response')
                except:
                    print('Retrying To Fetch Response')

            http_response_body = b64decode(api_response.json()["httpResponseBody"]).decode()

            try:
                data = json.loads(json.loads(http_response_body)['d'])['Results']
                if len(data) == 1:
                    property_url = [v['RelativeURLEn'] for v in data][0]
                    return property_url
                else:
                    _property = []
                    for suggestion in data:
                        _location = ''.join(location.split(' '))
                        _suggestion = ''.join(self.remove_short_forms(suggestion['Address_EN'].lower().replace('-', '')).split(' '))

                        if (_suggestion in _location) or (_location in _suggestion):
                            property_url = suggestion['RelativeURLEn']
                            return property_url
                    else:
                        print('Property Not Found')

                _property[0]
            except:
                print('increase search query length')
                body['query'] = location[:len(body['query']) + 2]
                if len(body['query']) == len(location):
                    print("Not Found", location)
                    return ''
