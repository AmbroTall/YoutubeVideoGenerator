import re
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize


def split_text_into_sentence_chunks(text, max_chunk_length=2000):
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

def remove_commas(text):
    sentences = sent_tokenize(text)
    cleaned_sentences = [sentence.replace(',', '') if len(sentence) < 140 else sentence for sentence in sentences]
    return ' '.join(cleaned_sentences)

def expand_abbreviations(text):
    abbreviations = {
        r'\bMr\.\b': 'Mister',
        r'\bMrs\.\b': 'Missus',
        r'\bMs\.\b': 'Miss',
        r'\bDr\.\b': 'Doctor',
        # Add more abbreviations as needed
    }

    for pattern, replacement in abbreviations.items():
        text = re.sub(pattern, replacement, text)
    return text

def process_text(text):
    # print('transcript',text)
    text = remove_commas(text)
    text = expand_abbreviations(text)
    
    return text