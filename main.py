"""
Jarvis: A Voice-Activated Personal Assistant

This script creates a voice-activated personal assistant named Jarvis. It can perform various tasks such as telling the time and date, opening applications, calculating expressions, and generating responses using the OpenAI API. The assistant listens for voice commands and responds accordingly.

Author: Siddhesh Kulkarni
"""

import subprocess
import speech_recognition as sr
import datetime
import webbrowser
import os
import openai
import threading
import requests
import time

# Set API key for OpenAI
openai.api_key = "YOUR_API_KEY"

# Create an event to handle stop speaking
stop_speaking = threading.Event()


def speak(text, voice="Daniel", rate=185):
    """
    Uses the system's text-to-speech engine to speak the given text.
    Parameters:
    - text: The text to be spoken.
    - voice: The voice to use (default is "Daniel").
    - rate: The rate of speech (default is 185).
    """
    global stop_speaking
    try:
        print(f"Speaking: {text}")
        process = subprocess.Popen(['say', '-v', voice, '-r', str(rate), text])
        while process.poll() is None:
            if stop_speaking.is_set():
                process.terminate()
                print("Speaking interrupted.")
                break
    except Exception as e:
        print(f"Error in speaking: {e}")


def take_command():
    """
    Listens for a voice command and returns it as a string.
    Returns "None" if there was an error or no command was recognized.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.2)
        time.sleep(1)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)
            print("Audio captured.")
        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
            return "None"
        except Exception as e:
            print(f"Error during listening: {e}")
            return "None"

    try:
        print("Understanding...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"You said: {query}\n")
        return query
    except sr.UnknownValueError:
        print("Could not understand the audio. Please try again.")
        return "None"
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return "None"
    except Exception as e:
        print(f"Error during recognition: {e}")
        return "None"


def preprocess_expression(expression):
    """
    Replaces words in a mathematical expression with corresponding symbols.
    Parameters:
    - expression: The mathematical expression as a string.
    Returns the processed expression.
    """
    replacements = {
        "plus": "+",
        "minus": "-",
        "times": "*",
        "multiplied by": "*",
        "divided by": "/",
        "into": "*",
        "by": "/",
        "raised to the power of": "**",
        "power": "**",
        "cube": "**3",
        "square": "**2",
        "mod": "%",
        "modulus": "%",
        "percent": "/100",
        "percentage": "/100",
        "root": "**0.5",
        "square root": "**0.5",
        "cube root": "**(1/3)",
        "x": "*",
    }
    for word, symbol in sorted(replacements.items(), key=lambda item: -len(item[0])):
        expression = expression.replace(word, symbol)
    return expression


def calculate(expression):
    """
    Evaluates a mathematical expression and returns the result.
    Parameters:
    - expression: The mathematical expression as a string.
    Returns the result or an error message if the evaluation fails.
    """
    try:
        expression = preprocess_expression(expression)
        result = eval(expression)
        return result
    except Exception as e:
        return "Error in calculation"


def get_time():
    """
    Returns the current time as a string.
    """
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")


def get_date():
    """
    Returns the current date as a string.
    """
    now = datetime.datetime.now()
    return now.strftime("%B %d, %Y")


def open_website(url):
    """
    Opens the specified URL in the default web browser.
    Parameters:
    - url: The URL to open.
    """
    webbrowser.open(url)


# Mapping of common application names to their system paths
application_mapping = {
    "safari": "Safari",
    "chrome": "Google Chrome",
    "vscode": "Visual Studio Code",
    "spotify": "Spotify",
    "slack": "Slack",
    "zoom": "zoom.us",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "microsoft teams": "Microsoft Teams",
    "discord": "Discord",
    "outlook": "Microsoft Outlook",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
}


def open_application(app_name):
    """
    Opens the specified application by name.
    Parameters:
    - app_name: The name of the application to open.
    Returns a message indicating the result.
    """
    app_name = app_name.lower()
    if app_name in application_mapping:
        app_path = application_mapping[app_name]
    else:
        app_path = app_name
    try:
        subprocess.run(["open", f"/Applications/{app_path}.app"])
        return f"Opening {app_path}"
    except Exception as e:
        return f"Could not open {app_path}: {e}"


def generate_response(command, voice, rate):
    """
    Generates a response based on the given command.
    Parameters:
    - command: The command string.
    - voice: The voice to use for the response.
    - rate: The rate of speech.
    Returns a response string.
    """
    if "time" in command:
        return f"The current time is {get_time()}"
    elif "date" in command:
        return f"Today's date is {get_date()}"
    elif "open " in command:
        app_name = command.replace("open ", "").strip()
        if app_name in application_mapping:
            return open_application(app_name)
        else:
            url = f"https://{app_name}.com"
            speak(f"Opening {app_name}", voice, rate)
            open_website(url)
            return "Done"
    elif "calculate" in command:
        speak("What would you like to calculate?", voice, rate)
        expression = take_command().lower()
        if expression != "none":
            result = calculate(expression)
            return f"The result is {result}"
    else:
        # Use OpenAI API to generate a response
        return get_openai_response(command)


def get_openai_response(command):
    """
    Uses the OpenAI API to generate a response to the given command.
    Parameters:
    - command: The command string.
    Returns a response string or an error message.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": command}
            ],
            max_tokens=150
        )
        response_text = response.choices[0].message['content'].strip()
        return response_text
    except:
        return f"Error generating response: "


def jarvis(voice="Daniel", rate=185):
    """
    Main function to run the Jarvis assistant.
    Listens for commands and responds accordingly.
    Parameters:
    - voice: The voice to use for responses (default is "Daniel").
    - rate: The rate of speech (default is 185).
    """
    speak("Hello, I am Jarvis. Siddhesh Sir's personal AI assistant", voice, rate)

    while True:
        print("Waiting for command...")
        command = take_command().lower()

        if command == "none":
            continue
        elif "wake up" in command or "hey jarvis" in command:
            speak("Good morning sir, I hope you had a good sleep. Let's grind for today!", voice, rate)
        elif "how are you" in command:
            speak("I am doing great, sir. Thank you for asking. What about you?", voice, rate)
        elif "good" in command or "great" in command:
            speak("That's great to hear, sir. How can I assist you today?", voice, rate)
        elif "bad" in command or "not good" in command:
            speak("I am sorry to hear that, sir. How can I assist you today?", voice, rate)
        elif "thank you" in command or "thanks" in command:
            speak("You're welcome, sir. I am here to help you.", voice, rate)
        elif "who is your boss" in command or "who created you" in command:
            speak("I was created by Siddhesh Sir. Legend of today's time", voice, rate)
        elif "let's talk later jarvis" in command or "exit" in command or "quit" in command:
            speak("Alright sir, Goodbye!", voice, rate)
            break
        elif "alright jarvis" in command or "okay" in command:
            stop_speaking.set()
            speak("Yes?", voice, rate)
            stop_speaking.clear()
        else:
            stop_speaking.clear()
            response = generate_response(command, voice, rate)
            # Run speak in a separate thread to allow interruption
            speak_thread = threading.Thread(target=speak, args=(response, voice, rate))
            speak_thread.start()


if __name__ == "__main__":
    jarvis("Daniel", 185)
