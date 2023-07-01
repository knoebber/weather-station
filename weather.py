#!/usr/bin/python

import json
import logging
import os
import time

from typing import NamedTuple
from urllib.request import Request
from urllib.request import urlopen

from weatherhat import WeatherHAT

logger = logging.getLogger(__name__)

UPDATE_PERIOD_SECONDS = 10
PREC = 3
LOCAL_PURPLE_URL = 'http://nicolass-macbook-air.local:4000'
PROD_PURPLE_URL = 'https://mypurplewebsite.com'

def get_purple_url():
    if os.getenv('PURPLE_ENV') == 'PROD':
        return PROD_PURPLE_URL
    else:
        return LOCAL_PURPLE_URL

sensor = WeatherHAT()

def post(url: str, payload: dict):
    json_str = json.dumps({'weather_snapshot': payload})
    request = Request(url, data=json_str.encode('utf-8'), method='POST')
    request.add_header('Content-Type', 'application/json')
    request.add_header('X-purple-api-secret', os.getenv('PURPLE_API_SECRET', 'fake-api-secret'))
    with urlopen(request) as response:
        logger.info(json.loads(response.read()))

class WeatherData(NamedTuple):
    humidity: float
    is_wind_and_rain_updated: bool
    pressure: float
    rain_millimeters: float
    temperature: float
    unix_timestamp: int
    update_period_seconds: int
    wind_direction_degrees: int
    wind_speed_mph: float

    def broadcast(self):
        post(get_purple_url() + '/api/weather_snapshots/broadcast', self._asdict())

def get_data():
    return WeatherData(
        humidity=round(sensor.humidity, PREC),
        is_wind_and_rain_updated=sensor.updated_wind_rain,
        pressure=round(sensor.pressure, PREC),
        rain_millimeters=round(sensor.rain_total, PREC),
        temperature=round((sensor.temperature*1.8) + 32, PREC),
        unix_timestamp=int(time.time()),
        update_period_seconds=UPDATE_PERIOD_SECONDS,
        wind_direction_degrees=int(sensor.wind_direction),
        wind_speed_mph=round(sensor.wind_speed * 2.23693629, PREC) or 0,
    )

def run():
    while True:
        weather_data = None
        try:
            sensor.update(interval=UPDATE_PERIOD_SECONDS)
            weather_data = get_data()
            weather_data.broadcast()
        except Exception as e:
            logger.error('failed to send %s', weather_data)
            logger.exception(e)
        finally:
            time.sleep(1)

if __name__ == '__main__':
    run()
