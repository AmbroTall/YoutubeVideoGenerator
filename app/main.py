from flask import Flask,Blueprint, render_template, request, send_file,url_for, send_from_directory,jsonify
import transcribe, text_processing, tts, video_generation, translation,thumbnail_generation 
import yaml
import os
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
# Initialize the Flask app
app = Flask(__name__)

os.environ["COQUI_TOS_AGREED"] = "1"

base_dir = os.path.dirname(os.path.dirname(__file__))  # Base directory of the app
config_dir = os.path.join(base_dir, 'config')
app_dir = os.path.join(base_dir, 'app')

# Open the config.yaml file using the absolute path
with open(os.path.join(config_dir, 'config.yaml'), 'r') as config_file:
    config = yaml.safe_load(config_file)
# Load configuration
# with open('../config/config.yaml', 'r') as config_file:
#     config = yaml.safe_load(config_file)
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
        print("Selected languages:", languages)
        k = request.form['video_number']
        
        # Step 1: Transcribe
        transcript = transcribe.transcribe_youtube_video(youtube_url)
        
        # Step 2: Process text
        processed_text = text_processing.process_text(transcript)

        # Function to process each language in a separate thread
        def process_language(lang):
            print(f"Processing language: {lang}")
            
            # Paraphrase the processed text
            text = translation.paraphrase(processed_text)
            
            # Translate text
            translated_text = translation.translate_text(text, lang, config)
            
            # Generate TTS
            audio_files, audio_durations, chunks = tts.generate_tts(translated_text, lang)
            
            # Generate Thumbnail
            thumbnail = thumbnail_generation.main(youtube_url, lang, config,k)
            
            # Generate video
            video_file = video_generation.generate_video(audio_files, audio_durations, translated_text, chunks, config, lang, k)
        
        # Create and start a thread for each language
        with ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(process_language, languages)

        return render_template('index.html', videos=videos, images=images)

    return render_template('index.html', videos=videos, images=images)


@app.route('/progress')
def get_progress():
    return jsonify({"progress": progress, "process": current_process})

@app.route('/audio')
def get_audio():
    output_dir = "enhanced_audio"
    enhanced_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
    if enhanced_files:
        output_file = os.path.join(output_dir, enhanced_files[0])
        return send_file(output_file, as_attachment=True)
    else:
        return jsonify({"error": "No enhanced WAV file found"}), 404

@app.route('/output/<filename>')
def serve_video(filename):
    return send_from_directory('static/output', filename)

@app.route('/thumbnails/<filename>')
def serve_image(filename):
    return send_from_directory(os.path.join('static/thumbnails'), filename, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='::', port=5500, debug=True)