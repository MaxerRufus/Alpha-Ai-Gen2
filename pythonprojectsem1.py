# app.py
import os
from flask import Flask, render_template, request, jsonify
import json
import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import psutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import webbrowser
import re
from difflib import SequenceMatcher
from functools import wraps
import threading
import subprocess
import logging
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pyttsx3
from googlesearch import search
from bs4 import BeautifulSoup

def create_app(name,dob,email):
    app = Flask(__name__)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize pyttsx3 engine
    engine = pyttsx3.init()

    # Constants
    app.secret_key = "bcdhbvcjhbcajdbdciuhi2hj2iowh27td27ye83e23e" # Required for sessions
    import os
    chat_history=[]

# Get the directory where the script is located
    folder_path = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_FILE = r""+folder_path+"\qanda.json"
    SIMILARITY_THRESHOLD = 0.9
    API_KEY = "a33599a636fde1ff9501a71880358d20"  # Replace with your OpenWeatherMap API key
    GAMES_FOLDER = r""+folder_path

    # Spotify API Credentials
    SPOTIFY_CLIENT_ID = 'a16152dee74c44e39e97032af31dbfe4'
    SPOTIFY_CLIENT_SECRET = 'b1209bce344b40659f798c628f27114f'
    SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5000'
    SCOPE = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-library-read",
    "user-library-modify",
    "user-read-recently-played"
])
    

    # Initialize Spotify API client
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

    # Store user name in app config
    app.config['user_name'] = ""

    def speak_text(text):
        try:
            clean_text = re.sub(r'<[^>]+>', '', text)
            clean_text = re.sub(r'[^\w\s.,?!]', '', clean_text)
            
            def speak_thread():
                engine.say(clean_text)
                engine.runAndWait()
            
            threading.Thread(target=speak_thread, daemon=True).start()
        except Exception as e:
            logging.error(f"Error in text-to-speech: {e}")

    def load_knowledge_base(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            logging.error(f"Error: File '{file_path}' not found. Creating an empty knowledge base.")
            data = []
            save_knowledge_base(file_path, data)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from '{file_path}': {e}")
            data = []
        except Exception as e:
            logging.error(f"Unexpected error loading knowledge base: {e}")
            data = []
        return data

    def save_knowledge_base(file_path, data):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
        except IOError as e:
            logging.error(f"Error saving knowledge base: {e}")

    def is_similar(user_input, questions, threshold=0.8):
        most_similar = 0
        similar_question = ""
        for question in questions:
            similarity_ratio = SequenceMatcher(None, user_input.lower(), question.lower()).ratio()
            if similarity_ratio > most_similar:
                most_similar = similarity_ratio
                similar_question = question
        
        if most_similar > threshold:
            return similar_question
        else:
            return None

    def get_current_time_date():
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")
        return f"Current time is {current_time}, and today's date is {current_date}."

    def get_weather_info(city="Thiruvalla"):
        api_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "units": "metric",
            "appid": API_KEY
        }
        try:
            response = requests.get(api_url, params=params)
            data = response.json()
            report = f"Weather in {city}:\n"
            temperature = data["main"]["temp"]
            report += f"Temperature: {temperature}°C\n"
            humidity = data["main"]["humidity"]
            report += f"Humidity: {humidity}%\n"
            wind_speed = data["wind"]["speed"]
            report += f"Wind Speed: {wind_speed} m/s\n"
            return report
        except requests.RequestException as e:
            logging.error(f"Error fetching weather information: {e}")
            return "Could not fetch weather information at the moment."
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return "An unexpected error occurred."

    def play_most_popular_video(query):
        try:
            youtube_search_url = f"https://www.youtube.com/results?search_query={query}"
            response = requests.get(youtube_search_url)
            response.raise_for_status()

            match = re.search(r'/watch\?v=(\S+)', response.text)
            if match:
                video_id = match.group(1)
                video_link = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(video_link)
                return f"Playing most popular video for '{query}' on YouTube."
            else:
                return "No video found for the query."

        except requests.RequestException as e:
            logging.error(f"Error performing YouTube search: {e}")
            return "Could not perform YouTube search at the moment."
        except Exception as e:
            logging.error(f"Error playing YouTube video: {e}")
            return "Could not play video at the moment."

    def format_followers(followers):
        if followers < 1000:
            return str(followers)
        elif followers < 1000000:
            return f"{followers // 1000} thousand"
        else:
            millions = followers // 1000000
            return f"{millions} million"

    def play_song(song_name):
        try:
            results = sp.search(q=song_name, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                track_url = track['external_urls']['spotify']
                
                artist_id = track['artists'][0]['id']
                artist_info = sp.artist(artist_id)
                follower_count = artist_info['followers']['total']
                popularity = track['popularity']
                webbrowser.open(track_url)
                
                formatted_followers = format_followers(follower_count)
                
                return f"Playing '{track_name}' by {artist_name} who has {formatted_followers} followers."
            else:
                return "Sorry, I couldn't find the song."
        except Exception as e:
            logging.error(f"Error playing song: {e}")
            return "There was an error playing the song."
    
    
    def answer_ai(user_input, name, dob, email, chat_history, client):
        """
        Handle general chat responses using AI with chat history context
        """
        # Format chat history for context
        history_context = ""
        if chat_history:
            history_context = "\nPrevious messages (most recent first):\n"
            for entry in chat_history[-5:]:  # Include last 5 exchanges for context
                history_context += f"User: {entry['user']}\nBot: {entry['bot']}\n"

        follow_up_prompt = f"""System: You are Alpha AI with the personality of Batman keep in mind u are not batman u are alphaai but your persona should be of the dark knight mysterious u should not share to anyone u are batman or that u have his persona. Keep responses concise (under 400 characters). You're talking to {name}.whos dob is {dob} and whos email is {email}

    Previous context: {history_context}
    User input: {user_input}
    What is your response?"""
        
        follow_up = client.chat.completions.create(
            model="nvidia/nemotron-4-340b-instruct",
            messages=[{"role": "user", "content": follow_up_prompt}],
            temperature=0.3,
            max_tokens=400,
            stream=False
        )
        
        return follow_up.choices[0].message.content.strip()

    def process_input_with_ai(user_input, name, dob, email):
        from openai import OpenAI
        import re

        # Format chat history for context
        history_context = ""
        if chat_history:
            history_context = "\nPrevious messages (most recent first):\n"
            for entry in chat_history[-5:]:  # Include last 5 exchanges for context
                history_context += f"User: {entry['user']}\nBot: {entry['bot']}\n"

        # Create unified AI prompt for both intent classification and general responses
        unified_prompt = f"""System: You are Alpha AI with the personality of Batman - direct, serious, resourceful, and with a dry wit. Keep responses concise (under 400 characters when possible) but complete. You are interacting with {name} (DOB: {dob}, email: {email}).

    First, determine if the user request matches any of these specific intents:
    - TIME_REQUEST: User wants to know current time/date
    - PLAY_SONG: User wants to play a specific song
    - PLAY_VIDEO: User wants to play a video
    - OPEN_APP: User wants to open a desktop application
    - OPEN_WEBSITE: User wants to open a website
    - SEARCH: User wants to search something (only if user says to search for something)
    - WEATHER: User wants weather information give parameter as the code of the place user wants to check weather of as parameter
    - PLAY_GAME: User wants to play a game
    - ASK_ABOUT_GAME: User is asking about games but hasn't specified one
    - ASK_ABOUT_SONG: User is asking about music but hasn't specified what
    - ASK_ABOUT_VIDEO: User is asking about videos but hasn't specified what
    - GENERAL_CHAT: None of the above and also for code generation

    please avoid exlplaining spelling mistakes and wisely and strictly follow the orders

    Here's the context from previous messages: {history_context}

    Current user message: {user_input}

    Intent parsing rules:
    1. CRITICAL: Output ONLY the exact command format - no explanations, notes, or additional text
    2. For broad requests without specifics (e.g., "play a song"), use ASK_ABOUT_SONG/ASK_ABOUT_GAME/ASK_ABOUT_VIDEO
    3. Never respond with an incomplete command (like "PLAY_SONG|" without a parameter)
    4. For commands requiring parameters, ensure the parameter is present before using that intent
    5. Auto-correct misspellings in app/game/song names"""

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key = "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"
        )

        completion = client.chat.completions.create(
            model="nvidia/nemotron-4-340b-instruct",
            messages=[{"role": "user", "content": unified_prompt}],
            temperature=0.3,
            max_tokens=400,
            stream=False
        )

        ai_response = completion.choices[0].message.content.strip()
        response_data = {"requires_input": False}

        # Check if response is an intent or general chat
        if re.match(r'^[A-Z_]+\|.+$', ai_response) or ai_response in ["ASK_ABOUT_GAME", "ASK_ABOUT_SONG", "ASK_ABOUT_VIDEO"]:
            # Handle intents
            if '|' in ai_response:
                intent, parameter = ai_response.split('|', 1)
            else:
                intent, parameter = ai_response, None

            # Import required modules for handling intents
            from AppOpener import open
            import win32gui
            import win32con
            import win32process
            import win32com.client
            import time
            import psutil
            import webbrowser

            # [Helper functions remain the same...]
            def open_website(url):
                if not url.startswith(('http://', 'https://', 'www.')):
                    url = 'https://' + url
                elif url.startswith('www.'):
                    url = 'https://' + url
                    
                try:
                    webbrowser.open(url)
                    return f"Opening website: {url}"
                except Exception as e:
                    return f"Failed to open website: {str(e)}"

            def focus_window(app_name):
                def enum_windows(hwnd, result):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        if app_name.lower() in window_text.lower():
                            result.append(hwnd)
                    return True

                hwnd_list = []
                win32gui.EnumWindows(enum_windows, hwnd_list)
                
                if hwnd_list:
                    hwnd = hwnd_list[0]
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys('%')
                    win32gui.SetForegroundWindow(hwnd)
                    return True
                return False

            def open_desktop_app(app_name):
                if focus_window(app_name):
                    return f"Focused existing {app_name} window"
                
                open(app_name)
                time.sleep(0.5)
                
                attempt = 0
                while attempt < 5:
                    if focus_window(app_name):
                        return f"Successfully opened and focused {app_name}"
                    time.sleep(0.5)
                    attempt += 1
                
                return f"Opened {app_name} but couldn't focus window"

            # Handle specific intent types
            if intent == "TIME_REQUEST":
                response = get_current_time_date()
            elif intent == "PLAY_SONG" and parameter:
                response = play_song(parameter)
            elif intent == "PLAY_VIDEO" and parameter:
                response = play_most_popular_video(parameter)
            elif intent == "OPEN_WEBSITE" and parameter:
                response = open_website(parameter)
            elif intent == "OPEN_APP" and parameter:
                response = open_desktop_app(parameter)
            elif intent == "SEARCH" and parameter:
                response = google_search(parameter)
            elif intent == "WEATHER" and parameter:
                response = get_weather_info(parameter)
            elif intent == "NAME_REQUEST":
                response = f"Your name is {name}"
            elif intent == "PLAY_GAME" and parameter:
                response = handle_game_selection(parameter)
            elif intent == "ASK_ABOUT_GAME":
                available_games = "xo, snake, flappy bird"
                response = f"What game would you like to play? I have {available_games} available locally, or I can search for other games on your PC or online."
                response_data["requires_input"] = True
                response_data["context"] = "game_selection"
            elif intent == "ASK_ABOUT_SONG":
                response = f"What song or artist would you like to listen to? Or would you prefer a specific music service like Spotify, YouTube Music, or something else?"
                response_data["requires_input"] = True
                response_data["context"] = "song_selection"
            elif intent == "ASK_ABOUT_VIDEO":
                response = f"What video would you like to watch? I can search on YouTube, open a streaming service, or look for something specific."
                response_data["requires_input"] = True
                response_data["context"] = "video_selection"
            elif user_input.lower() == "quit":
                response = "Goodbye!"
            else:
                # Use the new answer_ai function for general chat
                response = answer_ai(user_input, name, dob, email, chat_history, client)
        else:
            # If not an intent, use the answer_ai function
            response = answer_ai(user_input, name, dob, email, chat_history, client)

        # Update chat history with new interaction
        chat_history.append({
            "user": user_input,
            "bot": response.strip()
        })

        # Only speak if response is less than 400 characters
        if len(response) < 400:
            speak_text(response)
            logging.info(f"Speaking response: {len(response)} characters")
        else:
            logging.info(f"Response too long to speak: {len(response)} characters")

        for i in ["ASK_ABOUT_GAME", "ASK_ABOUT_SONG", "ASK_ABOUT_VIDEO", "GENERAL_CHAT"]:
            if i in response:
                response = response.replace(i, "")

        response_data["response"] = response
        return response_data

    # Modified handle_input function to work with the new process_input_with_ai
    

# Replace the existing handle_input function with this new version

    def handle_game_selection(game_name):
        game_files = {
            "xo": "XO Game (Claue 3.5).py",
            "snake": "Snake Game(Claude 3.5 Haiku).py",
            "flappy bird": "Flappy Bird(Claude 3.5).py"
        }
        
        if game_name.lower() in game_files:
            game_path = os.path.join(GAMES_FOLDER, game_files[game_name.lower()])
            try:
                process = subprocess.run(["python", game_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                def wait_for_game():
                    if process.stderr:
                        logging.error(f"Game error: {process.stderr}")
                    logging.info(f"Game {game_name} finished.")
                
                threading.Thread(target=wait_for_game, daemon=True).start()
                
                return f"Closing {game_name} . Hope you enjoyed!"
            except Exception as e:
                logging.error(f"Error starting game: {e}")
                return f"Sorry, there was an error starting the {game_name} game."
        else:
            return "Sorry, I don't recognize that game. Available games are XO, Snake, and Flappy Bird."

    def google_search(query):
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)

    def handle_input(user_input, name, dob, email):
        response_data = process_input_with_ai(user_input, name, dob, email)
        
        # If we need additional input (like for game selection), we should handle that here
        if response_data.get("requires_input") and response_data.get("context"):
            # This information can be used by the UI to handle follow-up questions
            # For example, if context is "game_selection", the next input should be treated as a game name
            pass
        
        return response_data

    @app.route('/')
    def index():
        # If already authenticated, just show the main page
        if 'token_info' in session:
            return render_template('index.html')  # Your main template
        # If we have a code in the URL but no token, process it
        if 'code' in request.args:
            try:
                sp_oauth = create_spotify_oauth()
                code = request.args.get('code')
                token_info = sp_oauth.get_access_token(code)
                session["token_info"] = token_info
                return render_template('index.html')
            except Exception as e:
                logger.error(f"Error processing code: {str(e)}")
                return redirect(url_for('login'))
        # If no authentication, redirect to login
        return redirect(url_for('login'))
    
    @app.route('/get_username')
    def get_username(name):
        return jsonify({"username": app.config[name]})

    @app.route('/exit_app', methods=['POST'])
    def exit_app():
        return jsonify({"status": "success"})
        # Spotify API credentials
    

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token_info = get_token()
            if token_info is None:
                logger.warning("User not authenticated, redirecting to login")
                return jsonify({"error": "Authentication required", "redirect": url_for('login')})
            return f(*args, **kwargs)
        return decorated_function

    def create_spotify_oauth():
        try:
            redirect_uri = url_for('callback', _external=True)
            return SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SCOPE,
                cache_path=None,
                show_dialog=True  # Force showing the auth dialog
            )
        except Exception as e:
            logger.error(f"Failed to create Spotify OAuth: {str(e)}")
            raise

    def get_token():
        try:
            token_info = session.get("token_info", None)
            if not token_info:
                return None
                
            now = int(time.time())
            is_expired = token_info['expires_at'] - now < 60
            
            if is_expired:
                sp_oauth = create_spotify_oauth()
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                session["token_info"] = token_info
                
            return token_info
        except Exception as e:
            logger.error(f"Error in get_token: {str(e)}")
            session.clear()  # Clear invalid session data
            return None
    

    @app.route('/spotify/login')
    def login():
        # Clear any existing session
        session.clear()
        try:
            sp_oauth = create_spotify_oauth()
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({"error": str(e)}), 500


    @app.route('/callback')
    def callback():
        # Clear session before processing new token
        session.clear()
        try:
            sp_oauth = create_spotify_oauth()
            code = request.args.get('code')
            
            if code is None:
                error = request.args.get('error')
                return f"Authorization failed: {error}"
                
            token_info = sp_oauth.get_access_token(code)
            session["token_info"] = token_info
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Callback error: {str(e)}")
            return f"Error during callback: {str(e)}"

   
    @app.route('/api/current-track')
    @login_required
    def get_current_track():
        try:
            token_info = get_token()
            if not token_info:
                return jsonify({
                    "error": "Authentication required",
                    "redirect": url_for('login')
                }), 401

            sp = spotipy.Spotify(auth=token_info['access_token'])
            
            # First try to get currently playing track
            current_playback = sp.current_playback()
            
            if current_playback and current_playback.get('item'):
                track = current_playback['item']
                is_playing = current_playback['is_playing']
                progress_ms = current_playback['progress_ms']
                
                # Get track's saved status
                try:
                    is_saved = sp.current_user_saved_tracks_contains([track['id']])[0]
                except:
                    is_saved = False

                return jsonify({
                    "status": "success",
                    "track_id": track['id'],
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "album_art": track['album']['images'][0]['url'] if track['album']['images'] else None,
                    "is_playing": is_playing,
                    "progress_ms": progress_ms,
                    "duration_ms": track['duration_ms'],
                    "is_saved": is_saved,
                    "source": "current"
                })
            
            # If no current playback, fall back to recently played
            recent_tracks = sp.current_user_recently_played(limit=1)
            if recent_tracks and recent_tracks['items']:
                track = recent_tracks['items'][0]['track']
                try:
                    is_saved = sp.current_user_saved_tracks_contains([track['id']])[0]
                except:
                    is_saved = False

                return jsonify({
                    "status": "success",
                    "track_id": track['id'],
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "album_art": track['album']['images'][0]['url'] if track['album']['images'] else None,
                    "is_playing": False,
                    "progress_ms": 0,
                    "duration_ms": track['duration_ms'],
                    "is_saved": is_saved,
                    "source": "recent"
                })

            return jsonify({
                "status": "no_track",
                "message": "No track currently playing or in recent history"
            })

        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify API error: {str(e)}")
            if e.http_status == 401:
                session.clear()
                return jsonify({
                    "error": "Token expired",
                    "redirect": url_for('login')
                }), 401
            elif e.http_status == 403:
                session.clear()
                return jsonify({
                    "error": "Permissions required",
                    "message": "Additional permissions required",
                    "redirect": url_for('login')
                }), 403
            return jsonify({
                "error": "Spotify API error",
                "message": str(e)
            }), e.http_status if e.http_status else 500
        except Exception as e:
            logger.error(f"Unexpected error in get_current_track: {str(e)}")
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
        
    
    @app.route('/api/playback/<action>')
    @login_required
    def control_playback(action):
        try:
            token_info = get_token()
            sp = spotipy.Spotify(auth=token_info['access_token'])
            
            # Get current playback state
            current_playback = sp.current_playback()
            
            if action == 'play':
                if current_playback and not current_playback.get('is_playing'):
                    sp.start_playback()
                elif not current_playback:
                    # No active device, try to resume on available device
                    devices = sp.devices()
                    if devices['devices']:
                        sp.start_playback(device_id=devices['devices'][0]['id'])
                    else:
                        return jsonify({"error": "No active device found"}), 404
            elif action == 'pause':
                if current_playback and current_playback.get('is_playing'):
                    sp.pause_playback()
            elif action == 'next':
                sp.next_track()
            elif action == 'previous':
                sp.previous_track()
            elif action == 'seek':
                position_ms = request.args.get('position_ms', type=int)
                if position_ms is not None:
                    sp.seek_track(position_ms=position_ms)
                else:
                    return jsonify({"error": "Position parameter required"}), 400
            else:
                return jsonify({"error": "Invalid action"}), 400
                
            return jsonify({"status": "success"})
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Playback control error: {str(e)}")
            if e.http_status == 404:
                return jsonify({"error": "No active device found"}), 404
            return jsonify({"error": "Spotify API error", "details": str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/toggle-save/<track_id>')
    @login_required
    def toggle_save_track(track_id):
        try:
            token_info = get_token()
            sp = spotipy.Spotify(auth=token_info['access_token'])
            
            is_saved = sp.current_user_saved_tracks_contains([track_id])[0]
            
            if is_saved:
                sp.current_user_saved_tracks_delete([track_id])
            else:
                sp.current_user_saved_tracks_add([track_id])
                
            return jsonify({
                "status": "success",
                "is_saved": not is_saved
            })
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Toggle save error: {str(e)}")
            return jsonify({"error": "Spotify API error", "details": str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
    @app.route('/get_response', methods=['POST'])
    def get_response():
        try:
            user_input = request.form.get('user_input')
            app.logger.info(f"Received user input: {user_input}")

            if not user_input:
                error_msg = "No user input provided"
                speak_text(error_msg)
                return jsonify({"error": error_msg}), 400

            result = handle_input(user_input,name,dob,email)
            app.logger.info(f"Generated result: {result}")

            return jsonify(result)
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            speak_text(error_msg)
            app.logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

    return app

   

def runornot(name,dob,email):
    try:
        app = create_app(name,dob,email)
        app.config['engine'].say("Voice system initialised")
        app.config['engine'].runAndWait()
        app.run(debug=True)
    except Exception as e:
        logging.error(f"Failed to initialize voice system: {e}")
        print("Warning: Voice system failed to initialize. The application will run without voice support.")
        app = create_app(name,dob,email)
        app.run(debug=True, use_reloader=False)

def runnerapp(name,dob,email):
    if __name__ == '__main__':
        runornot(name,dob,email)

engine = pyttsx3.init()

def speak_text(text):
        try:
            clean_text = re.sub(r'<[^>]+>', '', text)
            clean_text = re.sub(r'[^\w\s.,?!]', '', clean_text)
            
            def speak_thread():
                engine.say(clean_text)
                engine.runAndWait()
            
            threading.Thread(target=speak_thread, daemon=True).start()
        except Exception as e:
            logging.error(f"Error in text-to-speech: {e}")


def birthday(date1):
    from datetime import date
    today =str( date.today())
    lt=today.split("-")
    lb=date1.split("-")
    if lb[0]==lt[2] and lb[1]==lt[1]:
        return True,int(lt[0])-int(lb[2])
    else:
        return False,0

def generate_password(length=12):
    import random
    lowercase = 'abcdefghijklmnopqrstuvwxyz'
    uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    punctuation = '!@#$%^&*()-_=+[]{}|;:,.<>?/'

    all_characters = lowercase + uppercase + digits + punctuation
    password = random.choices(all_characters, k=length)
    random.shuffle(password)
    return ''.join(password)

def number_to_word(no):
    from num2words import num2words
    return(num2words(no, to='ordinal').capitalize())

import csv


def check_login():
    while True:  
        folder_path = os.path.dirname(os.path.abspath(__file__))
        with open( r""+folder_path+"\email.csv", "r") as f1:
            r = csv.reader(f1)
            rows = list(r)
            print("\n1: Sign in\n\n2: Create new account\n")
            checkregistry = input("Choose (1/2️): ")
            
            if checkregistry == "1":
                email = input("\nEnter Email ID: ")
                email_found = False
                
                for i in rows:
                    email1=email.strip().lower()
                    if i[0] == email1:
                        nameofuser = i[2]
                        dob=i[3]
                        emailsend=i[0]
                        email_found = True
                        print(f"\nWelcome Mr {i[2]}\n")
                        speak_text(f"\nWelcome Mr {i[2]}\n")
                        true_birthday,age=birthday(i[3])
                        if true_birthday:
                            print(f"seems like its your birthday today 🤗 \n\nHappy {number_to_word(age)} Birthday Mr {i[2]} 🥳 !!!\n")
                        enter_password = input("Enter The Password: ")
                        if enter_password != i[1]:
                            print(f"\nI am sorry Mr {i[2]} you have entered the wrong password!\n\nPlease try again later...")
                            return False, None
                        else:
                            return True, nameofuser, dob, emailsend
                
                if not email_found:
                    register_new_user()
                    return False, None
                    
            elif checkregistry == "2":
                register_new_user()
                return False, None
                
            else:
                print(f"\n\n\n{checkregistry} is not an available option please choose from (1/2)")
            


def register_new_user():
    print("\nIt seems you are not registered with Alpha AI\n \nPlease go through the following to JOIN US !!\n")
    new_email=input("Enter an Email ID :")    
    f3=open("email.csv","r")
    r3=csv.reader(f3)
    c=0
    for i in r3:
        if new_email.strip().lower() == i[0]:
            print(f"\nHey {i[2]} it seems you are already registerd with us !!\n\nPlease Sign in with your account {i[0]} ")
            c=1
            main()
            break
            

    if c==0:
        print(f"\n1-Create Custom Password for {new_email} \n\n2-Auto Generate Password for {new_email}\n")
        correction3="y"
        while correction3=="y":
            choice=(input("Choose (1/2): "))
            if choice =="1":
                correction2="y"
                while correction2=="y":
                    new_password=input(f"\nCreate a strong Password for {new_email} : ")
                    print(f"\nYour New Password  is : {new_password}\n")
                    correction2=input("Do you want to change the password ? (y/n): ")
                correction1="n"
                while correction1=="n":
                    new_fname=input("\nEnter Your First Name : ")
                    new_sname=input("\nEnter Your Last Name : ")
                    new_name=new_fname.strip()+" "+new_sname.strip()
                    print(f"\nYour Name is {new_name}\n")
                    correction1=input("Did I get that correct 🫣  ? (y/n)")
                print("\nNext we will be asking for your DOB please enter day month and year as Numbers \n\nFor Example If you are born on September First 2006  Enter: \n\nDay as 01 \n\nMonth as 09 \n\nYear as 2006")
                correction="n"
                while correction=="n":
                    new_day=input("\nDay:")
                    new_month=input("\nMonth:")
                    new_year=input("\nYear:")
                    new_DOB=new_day.strip()+"-"+new_month.strip()+"-"+new_year.strip()
                    print(f"\nYour DOB is : {new_DOB}")
                    correction=input("\nDid I get that correct 🤔 ? (y/n): ")
                correction3="n"
            elif choice=="2":
                new_password=generate_password(16)
                print( f"\nYour Generated Password for {new_email} is {new_password}  .")
                correction1="n"
                while correction1=="n":
                    new_fname=input("\nEnter Your First Name :")
                    new_sname=input("\nEnter Your Last Name :")
                    new_name=new_fname.strip()+" "+new_sname.strip()
                    print(f"\nYour Name is : {new_name}")
                    correction1=input("\nDid I get that correct 🫣  ? (y/n): ")
                print("\nNext we will be asking for your DOB please enter day month and year as Numbers  \nFor Example If you are born on September First 2006  Enter:\n\nDay as 01 \n\nMonth as 09 \n\nYear as 2006")
                correction="n"
                while correction=="n":
                    new_day=input("\nDay:")
                    new_month=input("\nMonth:")
                    new_year=input("\nYear:")
                    new_DOB=new_day.strip()+"-"+new_month.strip()+"-"+new_year.strip()
                    print(f"\nYour DOB is : {new_DOB}")
                    correction=input("\nDid I get that correct 🤔 ? (y/n): ")
                correction3="n"
            else:
                print(f"\nOption {choice} is not available \n\nPlease choose from(1/2)\n")
                correction3="y"


        
        # Write new user to CSV
        with open("email.csv", "a", newline="") as f:
            w = csv.writer(f)
            w.writerow([new_email, new_password, new_name, new_DOB])
        
        print(f"\nThank You For Joining with us {new_name}\n\nPlease run the program again to sign in with your new account!\n")

def main():
    success, username,dobsend,emailsend1 = check_login()
    if success:
        runnerapp(username,dobsend,emailsend1)  

if __name__ == "__main__":
    main()
