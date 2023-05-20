import time
import json

from typing import NamedTuple

import weatherhat

PREC = 3
LOCAL_PURPLE = 'http://nicolass-macbook-air.local:4000'
PROD_PURPLE = 'https://mypurplewebsite.com'

sensor = weatherhat.WeatherHAT()


class WeatherData(NamedTuple):
    humidity: float
    pressure: float
    temperature: float

    def to_json(self):
        return json.dumps(self._asdict())
        

def get_data():
    sensor.update(interval=5.0)
    return WeatherData(
        humidity=round(sensor.humidity, PREC),
        pressure=round(sensor.pressure, PREC),
        temperature=round((sensor.temperature*1.8) + 32, PREC),
    )


# def run():
#     while True:
#         time.sleep(1)
#         print(data)


if __name__ == "__main__":
    run()
