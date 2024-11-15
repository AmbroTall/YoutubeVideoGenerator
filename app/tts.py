import os
from TTS.api import TTS
import ffmpeg
import json
import threading
import subprocess
import shutil
import torch
import re
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
    global progress, current_process
    
    current_process = "Clearing previous outputs"
    progress = 5
    clear_output_folder()
    clear_enhanced_folder()

    current_process = "Initializing TTS"
    progress = 10
    
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # if not torch.cuda.is_available():
    #     raise RuntimeError("CUDA is not available. Please check your installation or ensure that a GPU is present.")
    # device = torch.device("cuda") 
    print('DEVICE ::',device)
    tts.to(device)
    
    current_process = "Generating audio in chunks"
    progress = 40
    language_output_dir = os.path.join(output_audio_dir, language)
    os.makedirs(language_output_dir, exist_ok=True)
    
    chunks = split_text_for_tts(text)
    print(f'CHUNK ::{language}',chunks)
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        tts_output = os.path.join(language_output_dir, f"{language}_tts_output_{i}.wav")

        tts.tts_to_file(
            text=chunk,
            file_path=tts_output,
            speaker_wav=reference_files,
            language=language,
            speed=1.0,
            split_sentences=False
        )
        audio_files.append(tts_output)

        if os.path.exists(tts_output):
            audio_files.append(tts_output)
        else:
            print(f"Error: TTS output not created for chunk {i} in language {language}")

    if not audio_files:
        print(f"No audio files were generated for language {language}. Please check the TTS setup.")
        return [], [], []
    
    current_process = "Enhancing audio"
    progress = 70

    # enhance_audio_file(language_output_dir,language)
    
    current_process = "Audio generation and enhancement complete"
    progress = 100

    enhanced_audio_files = [f for f in os.listdir(enhanced_audio_dir) if f.endswith('.wav')]
    print("enhanced_audio_files",enhanced_audio_files)
    audio_durations = [get_duration(file) for file in audio_files]
    print('durations', audio_durations)
    return audio_files, audio_durations,chunks


def enhance_audio_file(input_dir,language):
    enhance_executable = "resemble-enhance"


    language_enhanced_dir = os.path.join(enhanced_audio_dir, language)
    os.makedirs(language_enhanced_dir, exist_ok=True)
    print(f"Enhancing audio for {language}. Input directory: {input_dir}, Output directory: {language_enhanced_dir}")

    print(f"Input directory: {input_dir}")

    # Find all .wav files in the input directory
    input_files = [f for f in os.listdir(input_dir) if f.endswith('.wav')]
    print(f"WAV files found: {input_files}")

    if not input_files:
        print(f"No .wav files found in the input directory: {input_dir}")
        return

    for input_file in input_files:
        input_path = os.path.join(input_dir, input_file)
        output_file = f"enhanced_{input_file}"
        output_path = os.path.join(language_enhanced_dir, output_file)
        
       
        print(f"Input file: {input_path}")
        print(f"Output file: {output_path}")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        try:
            # Run the enhancement process for each file
            command = [enhance_executable, input_dir, output_path, "--device", device]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")
            print(f"Command error: {result.stderr}")
            
            if os.path.exists(output_path):
                print(f"Enhanced audio saved to: {output_path}")
            else:
                print(f"Error: Enhanced file not created")
        except subprocess.CalledProcessError as e:
            print(f"Error running resemble-enhance: {e}")
            print(f"Command output: {e.output}")

    print(f"Contents of enhanced directory after processing {language}: {os.listdir(language_enhanced_dir)}")




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


    
def split_text_for_tts(text, max_chars=200):
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











