import os
import re
import numpy as np
import time
import random
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_audioclips, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont, ImageColor
import re
import ffmpeg
import shutil
from thumbnail_generation import generate_thumbnail
import subprocess
from moviepy.config import change_settings
# Set the correct path to the ImageMagick binary
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})


def generate_video(audio_files,audio_durations,chunk, chunks, config, lang, k):
    # Generate thumbnail
    thumbnail_path = generate_thumbnail(chunk[:100], lang, k, config,{})  # Use first 100 chars for thumbnail
    
    # Load audio clips
    audio_clips = [AudioFileClip(audio_file) for audio_file in audio_files]
    # Log audio files to check
    # print("Audio files:", audio_files)
    # full_audio = concatenate_audioclips(audio_clips)
    audio_clips = []
    for audio_file in audio_files:
        try:      
            audio_clips.append(AudioFileClip(audio_file))
        except Exception as e:
            print(f"Error loading {audio_file}: {e}")

    # Check if we successfully loaded any audio clips
    if not audio_clips:
        print("Error: No valid audio clips were loaded!")
    else:
        # Concatenate the audio clips
        full_audio = concatenate_audioclips(audio_clips)
        print("Audio concatenation successful!")
    
    # Get a random background image
    background_folder = config['paths']['background_images']
    background_image = random.choice(os.listdir(background_folder))
    background_path = os.path.join(background_folder, background_image)
    
    # Create video clip from the background image
    video = ImageClip(background_path).set_duration(full_audio.duration)
    
    # Add subtitles
    subtitles = create_subtitles(chunks, video.w, video.h, audio_durations)
    
    # Combine video and subtitles
    final_video = CompositeVideoClip([video] + subtitles)
    
    # Set audio
    final_video = final_video.set_audio(full_audio)
    
    # Write output file
    output_file = os.path.join(config['paths']['output'], f"{lang}_{k}.mp4")
    video = final_video.write_videofile(output_file, fps=24)
    
    return output_file

def create_subtitles(chunks, video_w, video_h, sentence_durations):
    subtitles = []
    start_time = 0

    # Split the text into sentences or lines
     # Split based on full stops, or you can use '\n' if using newlines

    # Ensure sentence_durations is a list of appropriate length
    if isinstance(sentence_durations, (float, np.float64)):
        sentence_durations = [sentence_durations] * len(chunks)

    # Create TextClip for each line and assign the corresponding duration and start time
    for i, (chunk, duration) in enumerate(zip(chunks, sentence_durations)):
        print(f"Adding subtitle: {chunk} (duration: {duration}s, start: {start_time}s)")
        
        # Create a TextClip for each subtitle line
        txt_clip = TextClip(chunk, fontsize=26, color='white', bg_color='none', method='caption')

        # Set the start time and duration for each line
        txt_clip = txt_clip.set_duration(duration).set_position(('center', 'center')).set_start(start_time)

        # Append the subtitle clip to the list
        subtitles.append(txt_clip)

        # Update the start time for the next subtitle
        start_time += duration

    return subtitles


def split_sentence_into_lines(text, max_line_length=50):
    lines = []
    current_line = []

    for word in text.split():
        if len(' '.join(current_line + [word])) <= max_line_length:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)


