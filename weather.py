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

BROADCAST_INTERVAL_SECONDS = 1
LOCAL_PURPLE_URL = 'http://nicolass-macbook-air.local:4000'
PREC = 3
PROD_PURPLE_URL = 'https://mypurplewebsite.com'
UPDATE_PERIOD_SECONDS = 10

def get_purple_url() -> str:
    if os.getenv('PURPLE_ENV') == 'PROD':
        return PROD_PURPLE_URL
    else:
        return LOCAL_PURPLE_URL

def get_broadcast_path() -> str:
    return get_purple_url() + '/api/weather_snapshots/broadcast'

sensor = WeatherHAT()

def post(url: str, payload: dict):
    json_str = json.dumps({'weather_snapshot': payload})
    request = Request(
        url,
        data=json_str.encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'X-purple-api-secret': os.getenv('PURPLE_API_SECRET', '435f.,pizTlf*321#cv'),
        },
        method='POST',
    )
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
        post(get_broadcast_path(), self._asdict())

def get_data() -> WeatherData:
    return WeatherData(
        humidity=round(sensor.humidity, PREC),
        is_wind_and_rain_updated=sensor.updated_wind_rain,
        pressure=round(sensor.pressure, PREC),
        rain_millimeters=round(sensor.rain_total, PREC),
        temperature=round((sensor.temperature*1.8) + 32, PREC),
        unix_timestamp=int(time.time()),
        update_period_seconds=UPDATE_PERIOD_SECONDS,
        wind_direction_degrees=(int(sensor.wind_direction) + 180) % 360,
        wind_speed_mph=round(sensor.wind_speed * 2.23693629, PREC) or 0,
    )

def run():
    fail_count = 0
    while True:
        weather_data = None
        try:
            sensor.update(interval=UPDATE_PERIOD_SECONDS)
            weather_data = get_data()
            weather_data.broadcast()
        except Exception as e:
            fail_count += 1
            logger.error('failed to send %s to %s (fail=%s)', weather_data, get_broadcast_path(), fail_count)
            logger.exception(e)
        else:
            fail_count = 0
        finally:
            if fail_count > 60:
                # prevent this program from getting stuck in an infinite error loop
                logger.error('received too many errors: exiting')
                exit(1)
            else:
                if fail_count == 0:
                    time.sleep(BROADCAST_INTERVAL_SECONDS)
                else:
                    # simple backoff logic so that it can wait out downtime caused by deploy/etc.
                    time.sleep(fail_count*10 if fail_count else 1)

if __name__ == '__main__':
    run()
