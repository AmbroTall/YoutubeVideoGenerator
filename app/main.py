from flask import Flask,Blueprint, render_template, request, send_file,url_for, send_from_directory
import transcribe, text_processing, tts, video_generation, translation,thumbnail_generation 
import yaml
import os

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



@app.route('/', methods=['GET', 'POST'])
def index():
    videos_dir = os.path.join(app_dir, 'static', 'output') 
    images_dir = os.path.join(app_dir, 'static', 'thumbnails')
    videos = os.listdir(videos_dir)
    images = os.listdir(images_dir)
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        lang = request.form['language']
        k = request.form['video_number']
        
        # Step 1: Transcribe
        transcript = transcribe.transcribe_youtube_video(youtube_url)
        
        # Step 2: Process text
        processed_text = text_processing.process_text(transcript)

        text = translation.paraphrase(processed_text)

        # Step 3: Translate Text
        translated_text = translation.translate_text(text,lang,config)
        
        # Step 3: Generate TTS
        audio_files,audio_durations,chunks = tts.generate_tts(translated_text,lang)

        # Step 4: generate Thumbnail
        thumbnail = thumbnail_generation.main(youtube_url, lang)
        
        # Step 5: Generate video
        video_file = video_generation.generate_video(audio_files,audio_durations,translated_text,chunks , config, lang, k)
        
        return render_template('index.html', videos=videos,images=images)

    return render_template('index.html', videos=videos,images=images)

@app.route('/output/<filename>')
def serve_video(filename):
    return send_from_directory('static/output', filename)

@app.route('/thumbnails/<filename>')
def serve_image(filename):
    return send_from_directory(os.path.join('static/thumbnails'), filename, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=True)