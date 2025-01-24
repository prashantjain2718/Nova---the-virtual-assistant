import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
import google.generativeai as genai
from googleapiclient.discovery import build
import asyncio
import os  

# API Keys
newsapi = "your api key here"
genai_api = "your api key here"
youtube_api_key = "your api key here"
# Initialize recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def aiProcess(command):
    genai.configure(api_key=genai_api)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"You are a virtual assistant named Nova. If I ask to open a website, just give its URL. Your task is: {command}")
    return response.text.strip()

def search_youtube_and_play(keyword):
    try:
        # Build the YouTube API client
        youtube = build("youtube", "v3", developerKey=youtube_api_key)

        # Perform a search query
        request = youtube.search().list(
            part="snippet",
            q=keyword,
            type="video",
            maxResults=1,  # Get the most relevant video
        )
        response = request.execute()

        # Check if any videos were found
        if response["items"]:
            # Get the video ID of the first search result
            video_id = response["items"][0]["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            speak(f"Playing {response['items'][0]['snippet']['title']} on YouTube.")
            webbrowser.open(video_url)
        else:
            speak("No videos found for the given keyword.")
    except Exception as e:
        speak(f"An error occurred while searching YouTube: {e}")

async def processCommand(c):
    c = c.lower()
    if "play" in c and "on youtube" in c:
        keyword = c.replace("play", "").replace("on youtube", "").strip()
        speak(f"Searching YouTube for {keyword}...")
        search_youtube_and_play(keyword)
    elif "news" in c:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?category=technology&apiKey={newsapi}")
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])
            if articles:
                speak("Here are the top headlines:")
                for i, article in enumerate(articles[:5], 1):  # Limit to top 5 headlines
                    speak(f"{i}. {article.get('title')}")
            else:
                speak("No articles found.")
        else:
            speak(f"Failed to fetch news. Status code: {r.status_code}.")
    elif "open" in c:
        response = aiProcess(c)
        if "http" in response or "www" in response:
            speak(f"Opening the website: {response}")
            webbrowser.open(response)
        else:
            speak(f"Sorry, I couldn't understand the website URL from your request.")
    elif "shutdown" in c:
        speak("Shutting down the system. Goodbye!")
        os.system("shutdown /s /t 1")  # Shutdown command for Windows
    elif "restart" in c:
        speak("Restarting the system. See you soon!")
        os.system("shutdown /r /t 1")  # Restart command for Windows
    else:
        result = aiProcess(c)
        speak(result)

async def main():
    speak("Initializing Nova...")
    while True:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
                command = recognizer.recognize_google(audio)
                if command.lower().startswith("nova"):
                    print("Nova Active...")
                    await processCommand(command[4:].strip())  # Skip the "Nova" keyword
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"Error: {e}")

# Run the main async loop
asyncio.run(main())