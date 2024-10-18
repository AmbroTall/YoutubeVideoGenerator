import os
from TTS.api import TTS
import ffmpeg
import threading
import subprocess
import shutil
import torch
import re
# Global variables
progress = 0
current_process = ""
reference_files = ["reference1.mp3", "reference2.mp3", "reference3.mp3"]

def clear_output_folder():
    output_folder = "output_audio"
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
    output_folder = "enhanced_audio"
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
    global progress, current_process
    
    current_process = "Clearing previous outputs"
    progress = 5
    clear_output_folder()
    clear_enhanced_folder()

    current_process = "Initializing TTS"
    progress = 10
    
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tts.to(device)
    
    current_process = "Generating audio in chunks"
    progress = 40
    output_audio = "output_audio"
    chunks = split_text_for_tts(text)
    print('CHUNK ::',chunks)
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        tts_output = os.path.join(output_audio, f"tts_output_{i}.wav")
        tts.tts_to_file(
            text=chunk,
            file_path=tts_output,
            speaker_wav=[os.path.join("reference_audio", ref) for ref in reference_files],
            language=language,
            speed=1.0,
            split_sentences=False
        )
        audio_files.append(tts_output)
    
    current_process = "Enhancing audio"
    progress = 70
    # enhance_audio_file(output_audio)

    current_process = "Audio generation and enhancement complete"
    progress = 100

    audio_durations = [get_duration(file) for file in audio_files]
    print('durations', audio_durations)
    return audio_files, audio_durations,chunks



def enhance_audio_file(input_dir):
    enhance_executable = "resemble-enhance"

    print(f"Input directory: {input_dir}")

    # Find all .wav files in the input directory
    input_files = [f for f in os.listdir(input_dir) if f.endswith('.wav')]
    print(f"WAV files found: {input_files}")

    if not input_files:
        print(f"No .wav files found in the input directory: {input_dir}")
        return

    for input_file in input_files:
        input_path = os.path.join(input_dir, input_file)
        output_file = "enhanced_" + input_file
        output_path = os.path.join(input_dir, output_file)
        output_dir= "enhanced_audio"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
       
        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")

        try:
            # Run the enhancement process for each file
            command = [enhance_executable, input_dir, output_dir, "--device", "cpu"]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")
            print(f"Command error: {result.stderr}")
            
            if os.path.exists(output_dir):
                print(f"Enhanced audio saved to: {output_dir}")
            else:
                print(f"Error: Enhanced file not created")
        except subprocess.CalledProcessError as e:
            print(f"Error running resemble-enhance: {e}")
            print(f"Command output: {e.output}")

    print(f"Contents of output directory after enhancement: {os.listdir(input_dir)}")


def get_duration(file_path):
    try:
        # Probe the MP3 file to get information
        probe = None
        probe = ffmpeg.probe(file_path, v="error", select_streams="a:0", show_entries="format=duration")

        # Extract the duration from the probe result
        audio_duration = float(probe["format"]["duration"])
        print('audio duration :', audio_duration)
        return audio_duration
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def split_text_for_tts(text, max_chars=220):
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



# def generate_tts(text, output_folder="output_audio"):
#     tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
#     os.makedirs(output_folder, exist_ok=True)
    
#     chunks = split_text_for_tts(text)
#     audio_files = []
    
#     for i, chunk in enumerate(chunks):
#         output_file = os.path.join(output_folder, f"chunk_{i}.wav")
#         tts.tts_to_file(text=chunk, file_path=output_file, speaker='speaker')
#         audio_files.append(output_file)
    
#     return audio_files

# def split_text_for_tts(text, max_chars=220):
#     words = text.split()
#     chunks = []
#     current_chunk = ""
    
#     for word in words:
#         if len(current_chunk) + len(word) + 1 <= max_chars:
#             current_chunk += " " + word if current_chunk else word
#         else:
#             chunks.append(current_chunk)
#             current_chunk = word
    
#     if current_chunk:
#         chunks.append(current_chunk)
    
#     return chunks