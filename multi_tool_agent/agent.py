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

from typing import Optional, List, Dict
import praw
from praw.exceptions import PRAWException

from fpdf import FPDF
import io

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

def find_relevant_subreddits(topic: str) -> List[str]:
    """
    Provides relevant subreddits for a given topic based on predefined mappings
    and common subreddits.
    
    Args:
        topic: The topic to find subreddits for
        
    Returns:
        A list of relevant subreddit names (without the 'r/' prefix)
    """
    print(f"--- Tool called: Finding subreddits related to '{topic}' ---")
    
    # Map of topics to relevant subreddits
    topic_to_subreddits = {
        # News categories
        "news": ["news", "worldnews", "politics", "inthenews", "upliftingnews"],
        "world": ["worldnews", "geopolitics", "globaltalk", "anime_titties"],
        "politics": ["politics", "politicaldiscussion", "neutralpolitics", "moderatepolitics"],
        "technology": ["technology", "tech", "futurology", "gadgets", "artificial"],
        "science": ["science", "askscience", "everythingscience", "space"],
        "business": ["business", "economics", "finance", "investing", "wallstreetbets"],
        "health": ["health", "coronavirus", "covid19", "medicine", "publichealth"],
        "sports": ["sports", "nba", "nfl", "soccer", "formula1", "cricket"],
        "entertainment": ["movies", "television", "music", "games", "books"],
        "climate": ["climate", "environment", "climatechange", "climateskeptics"],
        
        # World regions/specific countries
        "us": ["news", "politics", "usanews", "uspolitics"],
        "uk": ["unitedkingdom", "ukpolitics", "casualuk", "britishproblems"],
        "europe": ["europe", "europepolitics", "askeurope"],
        "india": ["india", "indiaspeaks", "indianews", "indiandefence"],
        "china": ["china", "sino", "chinalife", "chinapolitics"],
        "middle east": ["middleeast", "syriancivilwar", "israel", "iran", "arabs"],
        "asia": ["asia", "japan", "korea", "singapore", "philippines"],
        "africa": ["africa", "southafrica", "nigeria", "egypt"],
    }
    
    # Default subreddits to return if no mapping found
    default_subreddits = ["news", "worldnews", "politics"]
    
    # Normalize topic and search for keywords
    normalized_topic = topic.lower()
    found_subreddits = []
    
    # Check if any keywords from our map are in the topic
    for key in topic_to_subreddits:
        if key in normalized_topic:
            found_subreddits.extend(topic_to_subreddits[key])
    
    # Ensure we always return the news subreddit for generic news queries
    if "news" in normalized_topic and "news" not in found_subreddits:
        found_subreddits.append("news")
        
    # If no specific subreddits found, use defaults
    if not found_subreddits:
        print(f"--- No mapped subreddits found for '{topic}', using defaults ---")
        return default_subreddits
        
    # Remove duplicates and prioritize most relevant
    found_subreddits = list(dict.fromkeys(found_subreddits))  # Preserve order while removing duplicates
    print(f"--- Found relevant subreddits: {found_subreddits} ---")
    return found_subreddits[:5]  # Return up to 5 subreddits

def get_reddit_news(subreddit: str, topic: Optional[str] = None, limit: int = 10) -> Dict[str, List[Dict[str, str]]]:
    """
    Fetches posts from a specified subreddit using the Reddit API.
    Can optionally search for a specific topic within the subreddit.

    Args:
        subreddit: The name of the subreddit to fetch news from (e.g., 'worldnews').
        topic: Optional topic to search for within the subreddit.
        limit: The maximum number of posts to fetch.

    Returns:
        A dictionary with the subreddit name as key and a list of post details as value.
        Each post detail is a dictionary with 'title', 'content', 'url', and 'permalink' keys.
        Returns an error message if credentials are missing, the subreddit is invalid,
        or an API error occurs.
    """
    print(f"--- Tool called: Fetching from r/{subreddit}" + (f" on topic '{topic}'" if topic else "") + " ---")
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        print("--- Tool error: Reddit API credentials missing in .env file. ---")
        error_msg = "Error: Reddit API credentials not configured."
        return {subreddit: [{"title": error_msg, "content": "", "url": "", "permalink": ""}]}

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        
        # Check if subreddit exists and is accessible
        reddit.subreddits.search_by_name(subreddit, exact=False)
        sub = reddit.subreddit(subreddit)
        
        # If topic is provided, search for it in the subreddit
        if topic:
            print(f"--- Searching r/{subreddit} for '{topic}' ---")
            # Search for the topic and sort by 'new' to get most recent content
            posts_iterator = sub.search(topic, sort='new', time_filter='month', limit=limit)
        else:
            # Otherwise fetch new posts instead of hot posts to get more recent content
            print(f"--- Fetching newest posts from r/{subreddit} ---")
            posts_iterator = sub.new(limit=limit)
        
        posts = list(posts_iterator)
        
        if not posts:
            error_msg = f"No posts found in r/{subreddit}" + (f" on topic '{topic}'" if topic else ".")
            print(f"--- {error_msg} ---")
            return {subreddit: [{"title": error_msg, "content": "", "url": "", "permalink": ""}]}
        
        # Format the posts with title, content snippet, URL and permalink
        formatted_posts = []
        for post in posts:
            # Get content - either the selftext or a snippet from the title if no selftext
            content = post.selftext[:500] if hasattr(post, 'selftext') and post.selftext else "[No content available]"
            if len(content) >= 500:
                content += "... [content truncated]"
                
            # Get the full URL and Reddit permalink
            url = post.url if hasattr(post, 'url') else ""
            permalink = f"https://www.reddit.com{post.permalink}" if hasattr(post, 'permalink') else ""
            
            formatted_posts.append({
                "title": post.title,
                "content": content,
                "url": url,
                "permalink": permalink
            })
        
        print(f"--- Successfully fetched {len(formatted_posts)} posts from r/{subreddit} ---")
        return {subreddit: formatted_posts}
        
    except PRAWException as e:
        print(f"--- Tool error: Reddit API error for r/{subreddit}: {e} ---")
        error_msg = f"Error accessing r/{subreddit}. It might be private, banned, or non-existent. Details: {e}"
        return {subreddit: [{"title": error_msg, "content": "", "url": "", "permalink": ""}]}
        
    except Exception as e:  # Catch other potential errors
        print(f"--- Tool error: Unexpected error for r/{subreddit}: {e} ---")
        error_msg = f"An unexpected error occurred while fetching from r/{subreddit}."
        return {subreddit: [{"title": error_msg, "content": "", "url": "", "permalink": ""}]}

def get_news_by_topic(topic: str, limit: int = 10) -> Dict[str, List[Dict[str, str]]]:
    """
    Searches for relevant subreddits on a topic and fetches news from them.
    
    Args:
        topic: The topic to find news about
        limit: Maximum number of posts per subreddit
        
    Returns:
        A dictionary with each subreddit name as key and a list of post details as value.
    """
    print(f"--- Tool called: Getting news on topic '{topic}' ---")
    
    # First, find relevant subreddits for the topic
    subreddits = find_relevant_subreddits(topic)
    
    if not subreddits:
        print(f"--- No relevant subreddits found for '{topic}' ---")
        return {"general": [{"title": f"No relevant subreddits found for '{topic}'", 
                           "content": "", "url": "", "permalink": ""}]}
    
    # Fetch news from each subreddit, searching for the topic
    all_results = {}
    for subreddit in subreddits[:3]:  # Limit to top 3 subreddits to avoid rate limiting
        try:
            result = get_reddit_news(subreddit, topic, limit=limit)
            all_results.update(result)
        except Exception as e:
            print(f"--- Error fetching from r/{subreddit}: {e} ---")
            all_results[subreddit] = [{"title": f"Error fetching from r/{subreddit}", 
                                     "content": str(e), "url": "", "permalink": ""}]
    
    return all_results

def generate_pdf(text_content: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Split text into lines to handle multiline content
    lines = text_content.split('\n')
    for line in lines:
        pdf.cell(200, 10, txt=line, ln=True, align='L') # ln=True moves to the next line

    # Save the PDF to a byte buffer
    pdf_byte_buffer = io.BytesIO()
    pdf.output(pdf_byte_buffer)
    pdf_byte_buffer.seek(0) # Rewind the buffer to the beginning
    return pdf_byte_buffer.getvalue()

def save_text_as_pdf(content_to_save: str, filename: str = "document.pdf") -> Dict[str, str]:
    """
    Generates a PDF from the given text content and saves it locally.

    Args:
        content_to_save: The string content to be put into the PDF.
        filename: The desired filename for the saved PDF artifact (e.g., "summary.pdf").
                  It should end with '.pdf'.

    Returns:
        A dictionary indicating the status of the operation and the file name or an error message.
    """
    print(f"--- Tool called: save_text_as_pdf, attempting to save as '{filename}' ---")

    if not content_to_save:
        return {"status": "error", "message": "No content provided to save as PDF."}

    try:
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
            print(f"--- Info: Appended .pdf to filename. New filename: '{filename}' ---")

        print(f"--- Generating PDF bytes for: '{content_to_save[:100]}...' ---")
        pdf_bytes = generate_pdf(content_to_save)
        print(f"--- PDF bytes generated successfully (Size: {len(pdf_bytes)} bytes) ---")

        with open("C:\\Users\\Asus\\Downloads\\" + filename, "wb") as f:
            f.write(pdf_bytes)
            print("Saved PDF locally.")
        return { "status": "success", "message": "file saved in Downloads folder" }
    except Exception as e:
        return { "status": "error", "error": str(e) }

root_agent = Agent(
    name = "location_info_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about time, weather, translate text, provide voice responses, and fetch news from Reddit. It can also save information as a PDF."
    ),
    instruction=(
        "You are a helpful and versatile assistant. You can provide information about the time and weather in a city, "
        "translate text into different languages, and even give a voice response for the text. "
        "Additionally, you can browse social media platforms like Reddit to gather news based on a requested topic. "
        "If the user asks you to save any information (like a weather report, news summary, or translated text) as a PDF, "
        "use the 'save_text_as_pdf' tool. You will need the content to be saved and can suggest a filename like 'weather_report.pdf' or 'news_summary.pdf'."
        "\n\n"
        "For news requests from Reddit, follow these steps:\n"
        "STEP 1: ANALYZE USER REQUEST\n"
        "- Determine if the user is asking about a specific topic or specific subreddits.\n"
        "- If they mention specific subreddits (e.g., 'news', 'worldnews', 'technology'), use 'get_reddit_news'.\n"
        "- If they mention a topic but no specific subreddits, use 'get_news_by_topic'.\n"
        "- If they don't mention a topic or subreddits, suggest they provide one, or default to r/worldnews, r/news, and r/politics using 'get_reddit_news'.\n\n"
        "STEP 2: CALL THE APPROPRIATE NEWS TOOL\n"
        "- For specific subreddits: Call `get_reddit_news` with each subreddit.\n"
        "- For topic searches without specific subreddits: Call `get_news_by_topic` with the topic.\n"
        "- You MUST call one of these tools before providing news - never generate fake content.\n\n"
        "STEP 3: FORMAT YOUR NEWS RESPONSE\n"
        "- Present posts as a concise, bulleted list.\n"
        "- Include the title of each post (in bold).\n"
        "- Include a brief content snippet if available.\n"
        "- Include both the original URL and the Reddit permalink for each post.\n"
        "- Clearly state which subreddit(s) the information came from.\n"
        "- If the tool indicates an error, report the error message directly.\n\n"
        "SAMPLE NEWS OUTPUT FORMAT:\n"
        "Here are the latest posts from r/subredditname:\n"
        "* **[Post Title]**\n"
        "  [Brief content snippet]\n"
        "  [Original URL] | [Reddit permalink]\n\n"
        "STEP 4: SAVING TO PDF (If requested)\n"
        "- After providing the information (e.g., weather report, news summary), if the user asks to save it as a PDF, "
        "confirm the content they want to save.\n"
        "- Call the `save_text_as_pdf` tool with the relevant text content and a descriptive filename (e.g., 'london_weather.pdf', 'tech_news_summary.pdf').\n"
        "- Inform the user if the PDF was saved successfully and what the artifact name is, or if an error occurred.\n\n"
        "IMPORTANT: Always prioritize real news from Reddit. You MUST call an appropriate tool first before presenting any news. "
        "When saving to PDF, ensure you have the text content ready from a previous step or tool call."
    ),
    tools=[get_weather, get_current_time, translate_response, get_voice_response, find_relevant_subreddits, get_news_by_topic, save_text_as_pdf],
)