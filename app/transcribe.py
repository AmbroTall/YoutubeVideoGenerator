import os
import whisper
import yt_dlp

def download_audio(video_url, output_directory):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_directory, '%(title)s.%(ext)s'),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def transcribe_youtube_video(video_url):
    # Load Whisper model
    model = whisper.load_model("medium")

    # Download audio
    output_directory = "temp_audio"
    os.makedirs(output_directory, exist_ok=True)
    download_audio(video_url, output_directory)

    # Find the downloaded audio file
    audio_file = [f for f in os.listdir(output_directory) if f.endswith('.mp3')][0]
    audio_path = os.path.join(output_directory, audio_file)

    # Transcribe
    result = model.transcribe(audio_path)

    # Clean up
    os.remove(audio_path)
    os.rmdir(output_directory)

    return result["text"]