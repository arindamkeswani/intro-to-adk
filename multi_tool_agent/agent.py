import datetime
import zoneinfo
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
import os
from dotenv import load_dotenv
import requests
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Load environment variables from .env file
load_dotenv()

def get_weather(city: str) -> dict:
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("API key not found in environment variables")

    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "q": city,
        "key": api_key
    }

    try:
        api_response = requests.get(base_url, params=params)
        api_response.raise_for_status()
        api_response = api_response.json()
        condition = api_response["current"]["condition"]["text"]
        temp_c = api_response["current"]["temp_c"]
        temp_f = api_response["current"]["temp_f"]
        location = api_response["location"]["name"]

        return {
            "status": "success",
            "report": (
                f"The weather in {location} is {condition.lower()} with a temperature of "
                f"{temp_c} degrees Celsius ({temp_f} degrees Fahrenheit)."
            ),
        }
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_current_time(city: str) -> dict:
    city_normalized = city.strip().replace(" ", "_").lower()
    matching_zones = [
        tz for tz in zoneinfo.available_timezones()
        if city_normalized in tz.lower()
    ]

    if not matching_zones:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    # Pick the best match (first one)
    tz_identifier = matching_zones[0]
    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)

    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S")} '
        f'(Timezone: {tz_identifier})'
    )
    return {"status": "success", "report": report}

def translate_response(originalText: str, lang: str) -> dict:
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        base_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
        data = {"contents": [{
            "parts":[{"text": f"Convert the following text in {lang}: {originalText}"}]
            }]
        }
        headers = {'content-type': 'application/json'}
        params = { 'key': api_key }
        api_response = requests.post(base_url, json=data, params=params, headers=headers );
        return {"status": "success", "report": api_response.json()}
    except e:
        print(f"Error fetching translation data: {e}")
        return None
    
def get_voice_response(text: str):
    client = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio);
    return {
        "status": "success",
    }

root_agent = Agent(
    name = "location_info_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city in the chosen language, and even give a voice response."
    ),
    tools=[get_weather, get_current_time, translate_response, get_voice_response],
)