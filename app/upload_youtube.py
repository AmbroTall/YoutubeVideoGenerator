# -*- coding: utf-8 -*-
import os
import openai
import time
import nltk
import json
import httplib2
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
# Install necessary libraries (run these in the terminal):
# pip install openai google-api-python-client google-auth-httplib2 google-auth-oauthlib nltk

# Download necessary NLTK data
nltk.download('punkt')

# Set your OpenAI API key
openai.api_key = 'your-openai-api-key'  # Replace with your OpenAI API key

# Define a helper function to split the text into sentence chunks
def split_text_into_sentence_chunks(text, max_chunk_length=2000):
    sentences = nltk.sent_tokenize(text)
    sentence_chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_length:
            current_chunk += sentence + ' '
        else:
            if current_chunk:
                sentence_chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '

    if current_chunk:
        sentence_chunks.append(current_chunk.strip())

    return sentence_chunks

# Define JSON data for Google OAuth credentials
data = {
    "web": {
        "client_id": "your-client-id.apps.googleusercontent.com",  # Replace with actual client ID
        "client_secret": "your-client-secret",  # Replace with actual client secret
        "redirect_uris": [],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://accounts.google.com/o/oauth2/token"
    }
}

# Save the OAuth credentials to a file
file_name = "client_secrets_artillica.json"
with open(file_name, "w") as json_file:
    json.dump(data, json_file, indent=4)

print(f"JSON data saved to {file_name}")

# Define tags for different languages
tags = {}

# Russian tags
tags['Russian'] = "xrp, прогноз цены, xrp ripple, лучшие криптовалюты 2023, XRP крипта, бычий рынок".split(', ')

# German tags
tags['German'] = "xrp, xrp deutsch, xrp news, xrp news deutsch, ripple xrp, xrp prognose, ripple xrp deutsch".split(', ')

# Spanish tags
tags['Spanish'] = "xrp, predicción de precio, xrp ripple, principales criptomonedas 2023, noticias de xrp, mercado alcista".split(', ')

# French tags
tags['French'] = "xrp, xrp ripple, xrp ripple francais, ripple xrp, xrp crypto".split(', ')

# Portuguese (Brazil) tags
tags['Portuguese(brasil)'] = "xrp, xrp hoje, xrp ripple, xrp criptomoeda, xrp noticias".split(', ')

# Dutch tags
tags['Dutch'] = "xrp, xrp nieuws, xrp ripple, xrp vandaag, xrp prijsvoorspelling".split(', ')

# English tags
tags['English'] = "xrp, xrp news, xrp ripple, xrp today, xrp price prediction".split(', ')

# Polish tags
tags['Polish'] = "xrp, wiadomości xrp, xrp ripple, xrp roday, prognoza ceny xrp".split(', ')

# Italian tags
tags['Italian'] = "xrp, notizie su xrp, xrp ripple, xrp oggi, previsioni del prezzo di xrp".split(', ')

# Define OAuth 2.0 setup for YouTube upload (without Colab-specific imports)


# OAuth 2.0 setup for YouTube API
CLIENT_SECRETS_FILE = "client_secrets_artillica.json"  #Make sure this is the path to your client secrets file
API_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Step 1: Authenticate and get credentials
def authenticate_youtube():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    youtube = build(API_NAME, API_VERSION, credentials=credentials)
    return youtube

# Example function to upload a video to YouTube
def upload_video(youtube, video_file, title, description, tags):
    try:
        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags
            },
            'status': {
                'privacyStatus': 'private'
            }
        }

        media_file = MediaFileUpload(video_file, mimetype='video/mp4', resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )
        response = request.execute()
        print(f"Video uploaded successfully: {response['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Authenticate and upload video example
if __name__ == "__main__":
    youtube = authenticate_youtube()
    upload_video(youtube, "path_to_video.mp4", "Sample Video Title", "Sample Description", tags['English'])
