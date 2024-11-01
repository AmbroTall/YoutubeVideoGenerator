import os
import whisper
import yt_dlp
from pydub import AudioSegment


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

def split_audio(audio_path, chunk_length_ms=900000, chunk_directory=""):  # 900 seconds in milliseconds
    audio = AudioSegment.from_mp3(audio_path)
    chunks = []
    
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_path = os.path.join(chunk_directory, f"{os.path.basename(audio_path)[:-4]}_chunk_{i // chunk_length_ms}.mp3")
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)
    
    return chunks

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

    # Create a directory for chunks
    chunk_directory = os.path.join(output_directory, "temp_chunks")
    os.makedirs(chunk_directory, exist_ok=True)

    # Split audio into chunks
    audio_chunks = split_audio(audio_path, chunk_length_ms=900000, chunk_directory=chunk_directory)

    # Transcribe each chunk and combine results
    combined_transcript = ""
    for chunk_path in audio_chunks:
        result = model.transcribe(chunk_path)
        combined_transcript += result["text"] + " "

    # Clean up: remove only the chunks created
    for chunk_path in audio_chunks:
        os.remove(chunk_path)

    # Remove the original audio file and the temporary directory
    os.remove(audio_path)
    os.rmdir(chunk_directory)  # Remove the chunk directory after cleaning up
    os.rmdir(output_directory)

    return combined_transcript.strip()

# def download_audio(video_url, output_directory):
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'outtmpl': os.path.join(output_directory, '%(title)s.%(ext)s'),
#     }
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         ydl.download([video_url])

# def transcribe_youtube_video(video_url):
#     # Load Whisper model
#     model = whisper.load_model("medium")

#     # Download audio
#     output_directory = "temp_audio"
#     os.makedirs(output_directory, exist_ok=True)
#     download_audio(video_url, output_directory)

#     # Find the downloaded audio file
#     audio_file = [f for f in os.listdir(output_directory) if f.endswith('.mp3')][0]
#     audio_path = os.path.join(output_directory, audio_file)

#     # Transcribe
#     result = model.transcribe(audio_path)

#     # Clean up
#     os.remove(audio_path)
#     os.rmdir(output_directory)

#     return result["text"]