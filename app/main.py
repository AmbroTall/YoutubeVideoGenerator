from flask import Flask, render_template, request, send_file, url_for, jsonify, send_from_directory,session
import transcribe, text_processing, tts, video_generation, translation, thumbnail_generation
import yaml
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
import ffmpeg
import os
from urllib.parse import urlparse, parse_qs
import re
import subprocess
import threading
import queue
from yt_dlp import YoutubeDL
from openai import OpenAI
from youtube_scanner import YouTubeScanner
import traceback
from pymongo import MongoClient
import json
import time
import logging
import sys
from dotenv import load_dotenv
from functools import partial

app = Flask(__name__)
# Add a secret key for session management
app.secret_key = 'your-secret-key-here'  # Replace with a secure secret key
# Load environment variables from .env file
load_dotenv()
# Ensure the uploads directory exists
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Add these global variables at the top of your file
progress_queue = queue.Queue()
current_progress = {'frame': 0, 'total_frames': 0, 'percentage': 0}

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Initialize scanner with MongoDB Atlas URI
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://junglebuilds:junglebuilds@artillica.0wu4a.mongodb.net/youtube_shorts_db?retryWrites=true&w=majority&appName=artillica')
scanner = YouTubeScanner(MONGODB_URI)
db_client = MongoClient(MONGODB_URI)
db = db_client['youtube_shorts']
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

os.environ["COQUI_TOS_AGREED"] = "1"

base_dir = os.path.dirname(os.path.dirname(__file__))  # Base directory of the app
config_dir = os.path.join(base_dir, 'config')
app_dir = os.path.join(base_dir, 'app')

# Load configuration
try:
    with open(os.path.join(config_dir, 'config.yaml'), 'r') as config_file:
        config = yaml.safe_load(config_file)
    logger.info("Configuration loaded successfully.")
except Exception as e:
    logger.error("Error loading configuration: %s", e)
    raise


def get_video_id(url):
    """Extract video ID from YouTube URL"""
    parsed_url = urlparse(url)
    
    # Check if the URL is a standard YouTube video link
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path.startswith('/watch'):
            # Extract the video ID from the query parameters
            query_params = parse_qs(parsed_url.query)
            return query_params.get('v', [None])[0]  # Return the first value of 'v' or None
    
    return None  

def get_video_duration(url):
    """Get video duration using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get('duration', 0)
        except:
            return 0


def process_new_video(video):
    """Process a newly found video"""
    try:
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        print(f"\nProcessing new video: {video_url}")
        
        # Here you would add your video processing logic
        # For example:
        # - Download the video
        # - Process it
        # - Upload to Telegram
        # - etc.
        
    except Exception as e:
        print(f"Error processing new video: {e}")
        print(f"Stack trace: {traceback.format_exc()}")

@app.route('/progress')
def get_progress():
    """Endpoint to get current progress"""
    return jsonify(current_progress)

def get_video_description(url):
    """Get video description using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get('description', '')
        except Exception as e:
            print(f"Error getting video description: {e}")
            return ''



@app.route('/', methods=['GET', 'POST'])
def index():
    videos_dir = os.path.join(app_dir, 'static', 'output')
    images_dir = os.path.join(app_dir, 'static', 'thumbnails')

    # Ensure the videos and images directories exist
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    videos = os.listdir(videos_dir)
    images = os.listdir(images_dir)

    if request.method == 'POST':
        video_url = request.form.get('video_url')
        if not video_url:
            return render_template('index.html', 
                                error="Keine URL angegeben",
                                )
        
        video_id = get_video_id(video_url)
        if not video_id:
            return render_template('index.html', 
                                error="Ungültige YouTube Shorts URL",
                                )
        
        # Store video URL in session
        session['current_video_id'] = video_id
        session[f'video_url_{video_id}'] = video_url
        

        # Reset progress
        current_progress['frame'] = 0
        current_progress['total_frames'] = 0
        current_progress['percentage'] = 0
    
        
        try:

            # Get descriptions
            original_description = get_video_description(video_url)
            
            
            return render_template('index.html',
                                video_id=video_id,
                                show_progress=True,
                                original_description=original_description,
                                )
            
        except Exception as e:
            return render_template('index.html',
                                error=f"Fehler bei der Verarbeitung: {str(e)}",
                            )
    
    return render_template('index.html',videos=videos, images=images)


@app.route('/output/<filename>')
def serve_video(filename):
    return send_from_directory(os.path.join(app_dir, 'static', 'output'), filename)


@app.route('/thumbnails/<filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(app_dir, 'static', 'thumbnails'), filename, mimetype='image/png')

@app.route('/check_video/<video_id>')
def check_video(video_id):
    stretched_path = os.path.join(UPLOAD_FOLDER, f'{video_id}_stretched.mp4')
    if os.path.exists(stretched_path):
        video_url = url_for('static', filename=f'uploads/{video_id}_stretched.mp4')
        return jsonify({
            'ready': True,
            'video_url': video_url
        })
    return jsonify({'ready': False})


# Add new route for initializing channel scanning
@app.route('/init_channel_scan', methods=['POST'])
def init_channel_scan():
    try:
        video_url = request.form.get('video_url')
        if not video_url:
            return jsonify({'error': 'No URL provided'})
            
        channel_id = scanner.initialize_channel(video_url)
        if not channel_id:
            return jsonify({'error': 'Failed to initialize channel scanning'})
            
        try:
            scanner.start_scanning(channel_id, process_new_video)
            return jsonify({'success': True, 'channel_id': channel_id})
        except Exception as e:
            print(f"Error starting scanner: {str(e)}", flush=True)
            return jsonify({'error': f'Failed to start scanning: {str(e)}'})
            
    except Exception as e:
        print(f"Error in init_channel_scan: {str(e)}", flush=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/channel_status')
def channel_status():
    """Get current channel status"""
    try:
        # Get most recent channel
        channel = scanner.channel_info.find_one(
            sort=[('last_scan', -1)]
        )
        
        if channel:
            channel_info = scanner.get_channel_info(channel['_id'])
            if channel_info:
                return jsonify({
                    'success': True,
                    'channel_id': channel['_id'],
                    'channel_name': channel_info['channel_name'],
                    'channel_thumbnail': channel.get('thumbnail_url', ''),  # Ensure thumbnail URL is stored
                    'last_scan': channel_info['last_scan'].strftime('%Y-%m-%d %H:%M:%S') if channel_info['last_scan'] else 'Never'
                })
        
        return jsonify({'success': False, 'error': 'No channel found'})
        
    except Exception as e:
        print("\n❌ Error in channel_status:", flush=True)
        print(f"Error details: {str(e)}", flush=True)
        print("Stack trace:", traceback.format_exc(), flush=True)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/scan_now', methods=['POST'])
def scan_now():
    """Trigger an immediate scan"""
    try:
        channel_id = request.form.get('channel_id')
        if not channel_id:
            # Try to get the most recent channel from database
            channel = scanner.channel_info.find_one({})
            if channel:
                channel_id = channel['_id']
            else:
                return jsonify({
                    'success': False,
                    'error': 'No channel ID provided and no channels in database'
                })
        
        logger.info("Starting immediate scan for channel: %s", channel_id)
        # Start scanning with callback
        success = scanner.start_scanning(channel_id, process_new_video)
        
        if not success:
            logger.error("Scan failed to start")
            return jsonify({
                'success': False,
                'error': 'Failed to start scan'
            })
        
        return jsonify({
            'success': True,
            'message': 'Scan completed successfully'
        })
        
    except Exception as e:
        logger.error("Error in scan_now: %s", str(e), exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/change_channel', methods=['POST'])
def change_channel():
    """Change the channel being scanned"""
    try:
        video_url = request.form.get('video_url')
        if not video_url:
            return jsonify({'success': False, 'error': 'No URL provided'})
            
        # Stop current scanning
        scanner.scheduler.remove_all_jobs()
        
        # Initialize new channel
        channel_id = scanner.initialize_channel(video_url)
        if not channel_id:
            return jsonify({'success': False, 'error': 'Failed to initialize new channel'})
            
        # Start scanning new channel
        scanner.start_scanning(channel_id, process_new_video)
        
        return jsonify({
            'success': True,
            'channel_id': channel_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
    
def process_videos_in_background():
    """Background thread to continuously process videos."""
    
    while True:
        # Fetch videos that are not processed from the 'processed_videos' collection
        videos_to_process = list(db['processed_videos'].find({"video_processed": False}).sort("upload_date", 1))
        logger.info("Videos to process: %s", videos_to_process)
        if videos_to_process:
            
            logger.info("Found unprocessed videos, starting processing...")
            for video in videos_to_process:
               
                video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
                k = video['video_id']
                logger.info(f"\nProcessing new video: {video_url}")

                try:
                    # Step 1: Transcribe
                    transcript = transcribe.transcribe_youtube_video(video_url)
                    logger.info("Transcript generated successfully.")

                    # Step 2: Process text
                    processed_text = text_processing.process_text(transcript)
                    logger.info("Text processed successfully.")

                    # Function to process each language
                    def process_language(lang,k):
                        try:
                            logger.info("Processing language: %s", lang)

                            # Paraphrase the processed text
                            text = translation.paraphrase(processed_text)

                            # Translate text
                            translated_text = translation.translate_text(text, lang, config)
                            logger.info("Text translated successfully for language: %s", lang)

                            # Generate TTS
                            audio_files, audio_durations, chunks = tts.generate_tts(translated_text, lang)
                            logger.info("TTS generated successfully for language: %s", lang)

                            # Generate Thumbnail
                            thumbnail = thumbnail_generation.main(video_url, lang, config,k)
                            logger.info("Thumbnail generated successfully for language: %s", lang)

                            # Generate video
                            video_file = video_generation.generate_video(audio_files, audio_durations, chunks, config, lang,k)
                            logger.info("Video generated successfully for language: %s - File: %s", lang, video_file)

                            if video_file:
                                # Update video_processed to True in the 'processed_videos' collection
                                db['processed_videos'].update_one({"_id": video["_id"]}, {"$set": {"video_processed": True}})
                                logger.info("Updated video_processed to True for video_id: %s", video['video_id'])


                        except Exception as e:
                            logger.error("Error processing language %s: %s", lang, e, exc_info=True)

                    # Create and start threads for each language
                    languages = ['de']  # Example languages
                    with ThreadPoolExecutor(max_workers=6) as executor:
                        executor.map(partial(process_language, k=k), languages)

                except Exception as e:
                    logger.error("Error processing video %s: %s", video['video_id'], e, exc_info=True)

        else:
            logger.info("No unprocessed videos found.")

        # Sleep for a specified interval before checking again
        time.sleep(10)  # Check every 10 seconds

@app.route('/reset_channel', methods=['POST'])
def reset_channel():
    print("Reset channel endpoint called")
    try:
        video_url = request.form.get('video_url')
        if not video_url:
            print("No URL provided")
            return jsonify({'success': False, 'error': 'No URL provided'})
            
        print("\n====== Starting Database Reset ======", flush=True)
        
        # Stop current scanning
        scanner.scheduler.remove_all_jobs()
        print("✓ Stopped current scanning jobs", flush=True)
        
        try:
            # Direct database access
            client = MongoClient(MONGODB_URI)
            db = client['youtube_shorts']
            
            # Get initial count before deletion
            initial_count = db.processed_videos.count_documents({})
            print(f"\nInitial document count: {initial_count}", flush=True)
            
            # Clear both collections
            channel_info_result = db.channel_info.delete_many({})
            processed_videos_result = db.processed_videos.delete_many({})
            
            print(f"Deleted {channel_info_result.deleted_count} documents from channel_info", flush=True)
            print(f"Deleted {processed_videos_result.deleted_count} documents from processed_videos", flush=True)
            
            # Verify deletion
            remaining_videos = list(db.processed_videos.find({}))
            remaining_count = len(remaining_videos)
            
            # Initialize new channel
            channel_id = scanner.initialize_channel(video_url)
            new_count = 1 if channel_id else 0
            
            return jsonify({
                'success': True,
                'message': 'Channel reset successfully',
                'channel_id': channel_id,
                'details': {
                    'initial_count': initial_count,
                    'deleted_count': processed_videos_result.deleted_count,
                    'remaining_count': remaining_count,
                    'new_count': new_count
                }
            })
            
        except Exception as e:
            error_msg = f"Database operation error: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        error_msg = f"Reset channel error: {str(e)}"
        print(f"❌ {error_msg}", flush=True)
        return jsonify({'success': False, 'error': error_msg})

if __name__ == '__main__':
    threading.Thread(target=process_videos_in_background, daemon=True).start()
    app.run(host='0.0.0.0', port=5500, debug=False)
