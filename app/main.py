from flask import Flask, render_template, request, send_file, send_from_directory, jsonify
import transcribe, text_processing, tts, video_generation, translation, thumbnail_generation
import yaml
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# Initialize the Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Logs to a file
        logging.StreamHandler()          # Logs to console
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

progress = 0
current_process = ""

@app.route('/', methods=['GET', 'POST'])
def index():
    global progress, current_process
    videos_dir = os.path.join(app_dir, 'static', 'output')
    images_dir = os.path.join(app_dir, 'static', 'thumbnails')

    # Ensure the videos and images directories exist
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    videos = os.listdir(videos_dir)
    images = os.listdir(images_dir)

    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        languages = request.form.getlist('languages[]')
        k = request.form['video_number']
        logger.info("Received request for YouTube URL: %s with languages: %s", youtube_url, languages,k)

        # Step 1: Transcribe
        try:
            transcript = transcribe.transcribe_youtube_video(youtube_url)
            logger.info("Transcript generated successfully.")
        except Exception as e:
            logger.error("Error during transcription: %s", e)
            return jsonify({"error": "Failed to transcribe video"}), 500

        # Step 2: Process text
        try:
            processed_text = text_processing.process_text(transcript)
            logger.info("Text processed successfully.")
        except Exception as e:
            logger.error("Error during text processing: %s", e)
            return jsonify({"error": "Failed to process text"}), 500

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
                logger.debug("Enhanced audio files: %s", audio_files)
                logger.debug("Audio durations: %s", audio_durations)

                # Generate Thumbnail
                thumbnail = thumbnail_generation.main(youtube_url, lang, config, k)
                logger.info("Thumbnail generated successfully for language: %s", lang)

                # Generate video
                video_file = video_generation.generate_video(audio_files, audio_durations, chunks, config, lang, k)
                logger.info("Video generated successfully for language: %s - File: %s", lang, video_file)

            except Exception as e:
                logger.error("Error processing language %s: %s", lang, e, exc_info=True)

        # Create and start threads for each language
        with ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(partial(process_language, k=k), languages)

        return render_template('index.html', videos=videos, images=images)

    return render_template('index.html', videos=videos, images=images)


@app.route('/progress')
def get_progress():
    return jsonify({"progress": progress, "process": current_process})


@app.route('/audio')
def get_audio():
    output_dir = os.path.join(app_dir, "enhanced_audio")
    enhanced_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
    if enhanced_files:
        output_file = os.path.join(output_dir, enhanced_files[0])
        logger.info("Serving enhanced audio file: %s", output_file)
        return send_file(output_file, as_attachment=True)
    else:
        logger.error("No enhanced WAV file found.")
        return jsonify({"error": "No enhanced WAV file found"}), 404


@app.route('/output/<filename>')
def serve_video(filename):
    return send_from_directory(os.path.join(app_dir, 'static', 'output'), filename)


@app.route('/thumbnails/<filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(app_dir, 'static', 'thumbnails'), filename, mimetype='image/png')


if __name__ == '__main__':
    app.run(host='::', port=5500, debug=True)
