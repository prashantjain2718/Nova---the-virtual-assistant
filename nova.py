import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
import google.generativeai as genai
from googleapiclient.discovery import build
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Initialize Speech Recognition & TTS Engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Function: Convert Text to Speech
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function: AI Processing
def aiProcess(command):
    """Process user commands using Google's Gemini AI."""
    try:
        genai.configure(api_key=GENAI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"""
        You are NOVA, a virtual assistant. 
        - If asked to **open a website**, return **only the URL**.
        - If no URL is found, perform a **Google search** instead.
        - By default, **keep responses concise**, unless explicitly asked for details.
        Task: {command}
        """)

        return response.text.strip()
    except Exception as e:
        return f"AI Processing Error: {e}"

# Function: Search YouTube and Play Video
def search_youtube_and_play(keyword):
    """Search YouTube and play the first video result."""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(part="snippet", q=keyword, type="video", maxResults=1)
        response = request.execute()

        if response["items"]:
            video_id = response["items"][0]["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            speak(f"Playing {response['items'][0]['snippet']['title']} on YouTube.")
            webbrowser.open(video_url)
        else:
            speak("No videos found.")
    except Exception as e:
        speak(f"An error occurred while searching YouTube: {e}")

# Function: Google Search (If No URL Found)
def google_search(query):
    """Perform a Google search if a direct website is not found."""
    try:
        search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_CSE_ID}"
        response = requests.get(search_url).json()
        
        if "items" in response and response["items"]:
            url = response["items"][0]["link"]
            speak(f"Opening {query} on Google.")
            webbrowser.open(url)
        else:
            speak("No direct website found. Searching on Google.")
            webbrowser.open(f"https://www.google.com/search?q={query}")

    except Exception as e:
        speak(f"Google Search Error: {e}")
        webbrowser.open(f"https://www.google.com/search?q={query}")

# Function: Process User Commands
async def processCommand(c):
    c = c.lower()

    if "play" in c and "on youtube" in c:
        keyword = c.replace("play", "").replace("on youtube", "").strip()
        speak(f"Searching YouTube for {keyword}...")
        search_youtube_and_play(keyword)

    elif "news" in c:
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?category=technology&apiKey={NEWS_API_KEY}")
            if r.status_code == 200:
                data = r.json()
                articles = data.get("articles", [])
                if articles:
                    speak("Here are the top headlines:")
                    for i, article in enumerate(articles[:5], 1):
                        speak(f"{i}. {article.get('title')}")
                else:
                    speak("No articles found.")
            else:
                speak(f"Failed to fetch news. Status code: {r.status_code}.")
        except Exception as e:
            speak(f"Error fetching news: {e}")

    elif "open" in c:
        response = aiProcess(c)
        if "http" in response or "www" in response:
            speak(f"Opening {response}")
            webbrowser.open(response)
        else:
            google_search(c.replace("open", "").strip())

    elif "search" in c:
        search_query = c.replace("search", "").strip()
        speak(f"Searching Google for {search_query}...")
        google_search(search_query)

    elif "shutdown" in c:
        speak("Shutting down the system. Goodbye!")
        os.system("shutdown /s /t 1")

    elif "restart" in c:
        speak("Restarting the system. See you soon!")
        os.system("shutdown /r /t 1")

    else:
        result = aiProcess(c)
        speak(result)

# Main Function: Continuous Listening
async def main():
    speak("Initializinng Nova...")

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
                command = recognizer.recognize_google(audio)

                if command.lower().startswith("nova"):
                    print("Nova Active...")
                    await processCommand(command[4:].strip())

        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"Error: {e}")

# Run NOVA
asyncio.run(main())
