# YouTube Video Generator

This project is a web application that automates the process of creating YouTube videos from transcribed content. It includes functionality for transcribing YouTube videos, processing text, generating text-to-speech audio, and creating videos with subtitles and thumbnails.

## Project Structure

project_root/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── transcribe.py
│   ├── text_processing.py
│   ├── tts.py
│   └── video_generation.py
│
├── config/
│   └── config.yaml
│
├── static/
│   ├── background_images/
│   ├── faces/
│   ├── fonts/
│   └── output/
│
├── templates/
│   └── index.html
│
├── .env
├── requirements.txt
├── Dockerfile
├── wsgi.py
└── README.md




## Changes from Original Colab Notebooks

The original project, which consisted of three separate Colab notebooks, has been restructured into a single web application. Here are the key changes:

1. **Modularization**: The code has been split into separate Python modules (`transcribe.py`, `text_processing.py`, `tts.py`, `video_generation.py`, `thumbnail_generation.py`) for better organization and maintainability.

2. **Web Interface**: A Flask web application (`main.py`) has been created to provide a user interface for the video generation process.

3. **Configuration**: A `config.yaml` file has been introduced to centralize configuration settings.

4. **Environment Variables**: Sensitive information like API keys are now stored in a `.env` file.

5. **Dockerization**: A Dockerfile has been added to containerize the application for easy deployment.

6. **TTS Change**: The Google TTS has been replaced with XTTSv2 for local text-to-speech generation.

7. **Video Generation**: The video generation process now uses a single background image instead of multiple video clips.

8. **Thumbnail Generation**: The thumbnail generation process has been integrated into the main application flow.



## Setup and Installation

1. Create a new directory for your project
2. Copy all project files into this directory
3. Install dependencies: `pip install -r requirements.txt`
4. Set up your `.env` file with necessary API keys
5. Configure `config/config.yaml` with your specific settings
6. Run the application: `python app/main.py`

## Usage

1. Access the web interface through your browser
2. Enter a YouTube URL and other required information
3. The application will process the video and generate a new video with the specified modifications

## Key Components

- **Transcription**: Uses Whisper to transcribe YouTube videos
- **Text Processing**: Cleans and formats the transcribed text
- **TTS**: Generates audio using XTTSv2
- **Video Generation**: Creates a video with subtitles and background image
- **Thumbnail Generation**: Creates custom thumbnails for the videos

## Configuration

Adjust the `config.yaml` file to customize various aspects of the video generation process, including paths, video settings, and language preferences.

## Docker

To run the application in a Docker container:

1. Build the Docker image: `docker build -t youtube-video-generator .`
2. Run the container: `docker run -p 5500:5500 youtube-video-generator`

## Testing

Run tests using: `python -m unittest discover tests`
