import time
import json
from urllib.request import Request
from urllib.request import urlopen

from typing import NamedTuple

from weatherhat import WeatherHAT

PREC = 3
LOCAL_PURPLE_URL = 'http://nicolass-macbook-air.local:4000'
PROD_PURPLE_URL = 'https://mypurplewebsite.com'

PURPLE_URL = LOCAL_PURPLE_URL

sensor = WeatherHAT()

def post(url: str, payload: dict):
    json_str = json.dumps({"weather_snapshot": payload})
    request = Request(url, data=json_str.encode('utf-8'), method='POST')
    request.add_header('Content-Type', 'application/json')
    with urlopen(request) as response:
        print(json.loads(response.read()))

class WeatherData(NamedTuple):
    humidity: float
    pressure: float
    temperature: float
    unix_timestamp: int

    def broadcast(self):
        post(PURPLE_URL + '/api/weather_snapshots/broadcast', self._asdict())

def get_data():
    sensor.update(interval=5.0)
    return WeatherData(
        humidity=round(sensor.humidity, PREC),
        pressure=round(sensor.pressure, PREC),
        temperature=round((sensor.temperature*1.8) + 32, PREC),
        unix_timestamp=int(time.time()),
    )

def run():
    while True:
        try:
            weather_data = get_data()
            weather_data.broadcast()
        except Exception as e:
            print('failed to send data', e)

        time.sleep(1)

if __name__ == "__main__":
    run()
