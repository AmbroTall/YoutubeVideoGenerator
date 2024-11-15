# Instructions for integration:
# 1. Create a 'translations' folder in your project directory.
# 2. Install required packages: pip install openai nltk and add to requirements.txt
# 3. Update main.py to import and use the translate_text function between transcription and TTS generation.
# 4. Ensure that the config.yaml file includes a 'translations' path under the 'paths' section.
# 5. Set the OPENAI_API_KEY environment variable with your OpenAI API key.

import os
import nltk
from openai import OpenAI
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Download NLTK data for sentence tokenization
nltk.download('punkt', quiet=True)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Define the model
MODEL = "gpt-4o-mini"

def translate_text(text, target_language, config):
    # Split the text into manageable chunks
    chunks = split_text_into_chunks(text)
    # print('my chunks ::', chunks)

    translated_chunks = []
    for chunk in chunks:
        # Translate the chunk using GPT-4o-mini
        translation = translate_chunk(chunk, target_language)
        translated_chunks.append(translation)

    # Combine the translated chunks
    translated_text = ' '.join(translated_chunks)

    print('translated', translated_text)

    # Save the translated text to a file
    save_translation(translated_text, target_language, config)

    return translated_text

def translate_chunk(chunk, target_language):
    target_language_name = "Italian" if target_language == "it" else target_language

    prompt = f"Translate the following text to {target_language_name}:\n\n{chunk}\n\nTranslation:"
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that translates text accurately."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    translation = response.choices[0].message.content.strip()

    # Check if the translation is identical to the input
    if translation == chunk.strip():
        print(f"Warning: Translation for {target_language} might have failed. Retrying...")
        
        # Retry with a stricter prompt
        prompt = f"Translate into formal {target_language_name}, avoiding comments or explanations. Text:\n\n{chunk}\n\nTranslation:"
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Translate accurately without adding comments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        translation = response.choices[0].message.content.strip()

    return translation


def split_text_into_chunks(text, max_chunk_length=2000):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_length:
            current_chunk += sentence + ' '
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def save_translation(translated_text, target_language, config):
    translations_folder = config['paths']['translations']
    os.makedirs(translations_folder, exist_ok=True)
    
    file_path = os.path.join(translations_folder, f"{target_language}_translation.txt")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(translated_text)

# Additional language-specific processing can be added here if needed

def split_text_into_sentence_chunks(text, max_chunk_length=2000):
    sentences = nltk.sent_tokenize(text)
    sentence_chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_length:
            current_chunk += sentence + ' '
        else:
            sentence_chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '
    if current_chunk:
        sentence_chunks.append(current_chunk.strip())
    return sentence_chunks

def remove_first_sentences(text, number_of_sentences_to_remove):
    sentences = nltk.sent_tokenize(text)
    return ' '.join(sentences[number_of_sentences_to_remove:])

def gpt_response_to_chunks(text, hashtag):
    text_cor = text.replace('\n', '\n ')
    words = text_cor.strip().split(' ')
    if hashtag.lower() not in words[0].lower():
        print("GPT wrote some comments at the beginning. I will take care of it.")
        comments = 1
    else:
        print("GPT didn't add any comments at the beginning. Great!")
        comments = 0

    all_chunks = []
   
    chunk = ''

    for w in words:
        if hashtag.lower() not in w.lower():
            chunk += w + ' '
        else:
            if chunk and comments == 0: 
                print(chunk)
                all_chunks.append(chunk)
                chunk = ''
            elif chunk and comments:
                chunk = ''
                comments = 0

    print(chunk)
    all_chunks.append(chunk)
    return all_chunks

def paraphrase_segment(text_chunk):
    gpt_response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        max_tokens=4000,
        messages=[
            {"role": "system", "content": "Your output message should contain only paraphrased text, do not write anything else, do not write your opinion or other comments. Start each rephrased sentence with the hashtag '#new'. Strictly follow all the instructions in this guidance."},
            {"role": "user", "content": f"""Rephrase each sentence (sentence by sentence) and correct grammar error in the provided text. Do not alter the original meaning and do not omit sentences. Use ordinary language with simple clear wording and good speech flow. Here is the text: "{text_chunk}" """}
        ]
    )
    return gpt_response.choices[0].message.content

def process_chunks(chunks):
    new_text = ""
    for chunk in chunks:
        print('original length', len(chunk))
        # new_chunk = paraphrase_segment(chunk) + '\n'
        # print('new chunk', chunk)
        new_chunk_list = gpt_response_to_chunks(chunk, '#text')
        for t in new_chunk_list:
            new_text += t + '\n'
    return new_text


def paraphrase(text):
    # story = extract_story(text)
    # idea = extract_idea(story)
    chunks = split_text_into_sentence_chunks(text, 2500)
    new_text = process_chunks(chunks)
    print('story',new_text)
    return new_text


def extract_story(rawstory):
    gpt_response = client.chat.completions.create(
        model=MODEL,
        temperature=0.05,
        max_tokens=4000,
        messages=[
            {"role": "system", "content": "Your task is to copy sentences which are a part of the main protagonist's story and to omit other sentences which break the flow of the story. Start the story with the hashtag '#text'.Adhere strictly to these guidelines."},
            {"role": "user", "content": f"{rawstory} \Please extract (copy, do not alter) the story about infidelity. Do not omit any sentences related to the protagonist and his wife (completely preserve original formulation). Omit sentences which are not the part of the story."}
        ]
    )
    outline = gpt_response.choices[0].message.content
    outline = outline.replace('# ', '#')
    return  outline


def extract_idea(storyoutline):
    gpt_response = client.chat.completions.create(
        model=MODEL,
        temperature=0.05,
        max_tokens=4000,
        messages=[
            {"role": "system", "content": "You are professional writer of novels and narratives about infidelity. Your task is to extract the idea of the story from the given text (settings, storyline, description of protagonists and so on). Output only the idea of the story, do not write anything else. Start writing idea with the hashtag '#idea'. Adhere strictly to these guidelines."},
            {"role": "user", "content": f"Describe in details the idea of the following story: \n{storyoutline}"}
        ]
    )
    final_idea = gpt_response.choices[0].message.content
    final_idea = final_idea.replace('# ', '#')
    return  final_idea
