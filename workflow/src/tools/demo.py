import warnings

# remove warnings
warnings.filterwarnings("ignore")

from datetime import datetime
import requests

from loguru import logger

from langchain.pydantic_v1 import BaseModel, Field


class WeatherSearchInput(BaseModel):
    city: str = Field(
        ...,
        description="The city to search for, in format of city, country, in US format",
    )


WMO_CODE = {
    "0": {
        "day": {
            "description": "Sunny",
            "image": "http://openweathermap.org/img/wn/01d@2x.png",
        },
        "night": {
            "description": "Clear",
            "image": "http://openweathermap.org/img/wn/01n@2x.png",
        },
    },
    "1": {
        "day": {
            "description": "Mainly Sunny",
            "image": "http://openweathermap.org/img/wn/01d@2x.png",
        },
        "night": {
            "description": "Mainly Clear",
            "image": "http://openweathermap.org/img/wn/01n@2x.png",
        },
    },
    "2": {
        "day": {
            "description": "Partly Cloudy",
            "image": "http://openweathermap.org/img/wn/02d@2x.png",
        },
        "night": {
            "description": "Partly Cloudy",
            "image": "http://openweathermap.org/img/wn/02n@2x.png",
        },
    },
    "3": {
        "day": {
            "description": "Cloudy",
            "image": "http://openweathermap.org/img/wn/03d@2x.png",
        },
        "night": {
            "description": "Cloudy",
            "image": "http://openweathermap.org/img/wn/03n@2x.png",
        },
    },
    "45": {
        "day": {
            "description": "Foggy",
            "image": "http://openweathermap.org/img/wn/50d@2x.png",
        },
        "night": {
            "description": "Foggy",
            "image": "http://openweathermap.org/img/wn/50n@2x.png",
        },
    },
    "48": {
        "day": {
            "description": "Rime Fog",
            "image": "http://openweathermap.org/img/wn/50d@2x.png",
        },
        "night": {
            "description": "Rime Fog",
            "image": "http://openweathermap.org/img/wn/50n@2x.png",
        },
    },
    "51": {
        "day": {
            "description": "Light Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Light Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "53": {
        "day": {
            "description": "Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "55": {
        "day": {
            "description": "Heavy Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Heavy Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "56": {
        "day": {
            "description": "Light Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Light Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "57": {
        "day": {
            "description": "Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Freezing Drizzle",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "61": {
        "day": {
            "description": "Light Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Light Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "63": {
        "day": {
            "description": "Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "65": {
        "day": {
            "description": "Heavy Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Heavy Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "66": {
        "day": {
            "description": "Light Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Light Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "67": {
        "day": {
            "description": "Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10d@2x.png",
        },
        "night": {
            "description": "Freezing Rain",
            "image": "http://openweathermap.org/img/wn/10n@2x.png",
        },
    },
    "71": {
        "day": {
            "description": "Light Snow",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Light Snow",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "73": {
        "day": {
            "description": "Snow",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Snow",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "75": {
        "day": {
            "description": "Heavy Snow",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Heavy Snow",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "77": {
        "day": {
            "description": "Snow Grains",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Snow Grains",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "80": {
        "day": {
            "description": "Light Showers",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Light Showers",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "81": {
        "day": {
            "description": "Showers",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Showers",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "82": {
        "day": {
            "description": "Heavy Showers",
            "image": "http://openweathermap.org/img/wn/09d@2x.png",
        },
        "night": {
            "description": "Heavy Showers",
            "image": "http://openweathermap.org/img/wn/09n@2x.png",
        },
    },
    "85": {
        "day": {
            "description": "Light Snow Showers",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Light Snow Showers",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "86": {
        "day": {
            "description": "Snow Showers",
            "image": "http://openweathermap.org/img/wn/13d@2x.png",
        },
        "night": {
            "description": "Snow Showers",
            "image": "http://openweathermap.org/img/wn/13n@2x.png",
        },
    },
    "95": {
        "day": {
            "description": "Thunderstorm",
            "image": "http://openweathermap.org/img/wn/11d@2x.png",
        },
        "night": {
            "description": "Thunderstorm",
            "image": "http://openweathermap.org/img/wn/11n@2x.png",
        },
    },
    "96": {
        "day": {
            "description": "Light Thunderstorms With Hail",
            "image": "http://openweathermap.org/img/wn/11d@2x.png",
        },
        "night": {
            "description": "Light Thunderstorms With Hail",
            "image": "http://openweathermap.org/img/wn/11n@2x.png",
        },
    },
    "99": {
        "day": {
            "description": "Thunderstorm With Hail",
            "image": "http://openweathermap.org/img/wn/11d@2x.png",
        },
        "night": {
            "description": "Thunderstorm With Hail",
            "image": "http://openweathermap.org/img/wn/11n@2x.png",
        },
    },
}


def get_current_weather(city: str) -> str:
    """
    Get the current weather of the city
    1. get the latitude and longitude of the city
    2. use the latitude and longitude to get the current weather

    ARGS:
        city: the city to get the current weather, in format of city, country, in US format
    RETURNS:
        the current weather of the city
    """

    def _get_city_coordinates(city: str) -> tuple[float, float]:
        """
        Get the latitude and longitude of the city
        ARGS:
            city: the city to get the latitude and longitude
        RETURNS:
            the latitude and longitude of the city
        """
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        try:
            latitude = data["results"][0]["latitude"]
            longitude = data["results"][0]["longitude"]
        except KeyError as e:
            logger.error(f"Error in get city coordinates: {e}, data: {data}")
            raise e
        return latitude, longitude

    def _get_current_weather(latitude: float, longitude: float) -> str:
        """
        Get the current weather of the city
        ARGS:
            latitude: the latitude of the city
            longitude: the longitude of the city
        RETURNS:
            the current weather of the city
        """

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "temperature_unit": "celsius",
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        current_weather = data["current_weather"]
        return {
            "temperature": current_weather["temperature"],
            "wind_speed": current_weather["windspeed"],
            "wind_direction": current_weather["winddirection"],
            "weathercode": current_weather["weathercode"],
            # if is_day is true, return day, otherwise return night
            "is_day": "day" if current_weather["is_day"] else "night",
        }

    try:
        latitude, longitude = _get_city_coordinates(city)
        weather_data = _get_current_weather(latitude, longitude)
    except Exception as e:
        logger.error(f"Error in get current weather: {e}")
        return f"Error in get current weather: {e}"
    weather_description = WMO_CODE[str(weather_data["weathercode"])]["day"][
        "description"
    ]
    image_url = WMO_CODE[str(weather_data["weathercode"])]["day"]["image"]
    template = """
    The weather in {city} is {weather_description} with a temperature of {temperature} degrees Celsius
    """
    result = template.format(
        city=city,
        weather_description=weather_description,
        temperature=weather_data["temperature"],
        wind_speed=weather_data["wind_speed"],
        wind_direction=weather_data["wind_direction"],
        image_url=image_url,
    )
    return result

def get_current_time() -> str:
    """
    Get the current time
    RETURNS:
        the current time
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

tools_map = {
    "get_current_weather": get_current_weather,
    "get_current_time": get_current_time,
}
