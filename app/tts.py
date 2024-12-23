import os
from TTS.api import TTS
import ffmpeg
import json
import threading
import subprocess
import shutil
import torch
import re
from concurrent.futures import ThreadPoolExecutor

# Global variables
progress = 0
current_process = ""
# reference_files = ["reference1.mp3", "reference2.mp3", "reference3.mp3"]
# Set the absolute path for the reference_audio directory
base_dir = os.path.dirname(os.path.dirname(__file__))
reference_audio_path = os.path.join(base_dir, "app", "reference_audio")
print('reference audio',reference_audio_path)
reference_files = [os.path.join(reference_audio_path, f"reference{i}.mp3") for i in range(1, 4)]
output_audio_dir = os.path.join(base_dir,"app", "output_audio")
enhanced_audio_dir = os.path.join(base_dir,"app", "enhanced_audio")


def clear_output_folder():
    output_folder = output_audio_dir
    if os.path.exists(output_folder):
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(output_folder)
    print("Output folder cleared.")

def clear_enhanced_folder():
    output_folder = enhanced_audio_dir
    if os.path.exists(output_folder):
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(output_folder)
    print("Enhanced folder cleared.")


def generate_tts(text, language):
    clear_output_folder()
    clear_enhanced_folder()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print('DEVICE ::', device)

    language_output_dir = os.path.join(output_audio_dir, language)
    os.makedirs(language_output_dir, exist_ok=True)

    chunks = split_text_for_tts(text)
    print(f'CHUNK ::{language}', chunks)
    audio_files = []

    for i, chunk in enumerate(chunks):
        tts_output = os.path.join(language_output_dir, f"{language}_tts_output_{i}")
        ref_audio_dir = os.path.join(base_dir,"app","reference_audio")
        ref_text_dir = os.path.join(base_dir,"app","reference_audio")

        # Get all reference audio and text files
        ref_audio_files = [
            os.path.join(ref_audio_dir, f) for f in os.listdir(ref_audio_dir) if f.endswith(".mp3")
        ]
        ref_text_files = [
            os.path.join(ref_text_dir, f) for f in os.listdir(ref_text_dir) if f.endswith(".txt")
        ]

        # Ensure there are references to process
        if not ref_audio_files:
            print(f"No reference audio files found in: {ref_audio_dir}")
            exit(1)

        if not ref_text_files:
            print(f"No reference text files found in: {ref_text_dir}")
            exit(1)

        # Check for mismatched counts of audio and text files
        if len(ref_audio_files) != len(ref_text_files):
            print("Mismatch between number of reference audio and text files.")
            exit(1)

        # Prepare command arguments for multiple references
        ref_audio_args = " ".join(ref_audio_files)
        ref_text_args = " ".join(ref_text_files)


        command = ["python3", "-m", "tools.api_client", "--text", chunk, "--reference_audio", *ref_audio_files, "--reference_text", *ref_text_files,"--streaming", "False", "--output", tts_output, "--format", "wav"]
        print(f"Running command: {' '.join(command)}")

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")
            print(f"Command error: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running command: {e}")
            print(f"Command output: {e.output}")
            print(f"Command error: {e.stderr}")
            continue

        # if os.path.exists(tts_output):
        #     audio_files.append(tts_output)
        # else:
        #     print(f"Error: TTS output not created for chunk {i} in language {language}")

    if not audio_files:
        print(f"No audio files were generated for language {language}. Please check the TTS setup.")
        return [], [], []

    audio_durations = [get_duration(file) for file in audio_files]
    print('durations', audio_durations)
    return audio_files, audio_durations, chunks


def get_duration(file_path):
    """Get the duration of an audio or video file using ffprobe."""
    try:
        # Command to get the duration
        cmd = f'ffprobe -i "{file_path}" -show_entries format=duration -v quiet -of csv="p=0"'
        
        # Execute the command
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        
        # Decode the output to a string and convert to float
        audio_duration = float(output.decode().strip())
        print('audio duration :', audio_duration)
        
        return audio_duration
    except Exception as e:
        print(f"Error: {e}")
        return None


    
def split_text_for_tts(text, max_chars=1000):
    # Split text into segments based on commas and full stops
    # The regex will split at commas and periods, keeping the punctuation with the sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Strip leading/trailing whitespace from the sentence
        sentence = sentence.strip()

        # If adding the current sentence stays within the max_chars limit
        if len(current_chunk) + len(sentence) + (1 if current_chunk else 0) <= max_chars:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            # If the current chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk)
            # Start a new chunk with the current sentence
            current_chunk = sentence

    # Append any remaining text as a chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks











