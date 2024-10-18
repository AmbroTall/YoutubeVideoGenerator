import os
import random
import sys
import yaml
import requests
from pytube import YouTube
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import base64
from openai import OpenAI
import logging
import statistics
import textwrap
import math

# Load configuration
with open('../config/config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

print("Loaded configuration:")
print(yaml.dump(config))

def get_youtube_thumbnail(video_url):
    try:
        yt = YouTube(video_url)
        thumbnail_url = yt.thumbnail_url
        response = requests.get(thumbnail_url)
        img = Image.open(io.BytesIO(response.content))
        # Resize image to lower resolution
        img.thumbnail((512, 512))  # Resize to max 512x512 while maintaining aspect ratio
        return img
    except Exception as e:
        print(f"Error fetching YouTube thumbnail: {e}")
        return None

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_text_from_image(img):
    client = OpenAI(api_key="sk-MWy2JCoFFQpZlMyK-kCqIAtRRrO1To_Dqzj8GdkTpuT3BlbkFJo9ZhJNzzmwkThyGfqrKnHaEuQygri-Mp4qhYT-h1sA")
    base64_image = encode_image(img)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract and return only the text visible in this image. If there's no text, return 'NO_TEXT_FOUND'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        print(f"API Response: {response}")  # Debug print
        extracted_text = response.choices[0].message.content.strip()
        # Join all lines into a single string
        extracted_text = ' '.join(extracted_text.split())
        return extracted_text if extracted_text != "NO_TEXT_FOUND" else ""
    except Exception as e:
        logging.error(f"Error extracting text from image using OpenAI: {e}")
        print(f"Full error: {e}")  # Debug print
        return ""

def generate_thumbnail(text, lang, k, config, color_highlights):
    print(f"Starting thumbnail generation with text: {text}")
    if not text.strip():
        print("Warning: Empty input text. Using default text.")
        text = "NO TEXT"
    
    # 1. Initial Setup
    width = config['video']['width']
    height = config['video']['height']
    font_path = config['paths']['font']
    object_image_folder = config['paths']['faces']
    target_padding_top_bottom = 25  # For top and bottom padding
    target_padding_left = 30  # For left padding
    padding_tolerance = 2
    overlap = 250  # Amount of overlap with the right image

    print(f"Image dimensions: {width}x{height}")
    print(f"Font path: {font_path}")
    print(f"Object image folder: {object_image_folder}")

    # Create background and paste face image
    background = Image.new('RGB', (width, height), color='black')
    try:
        object_image = get_random_face_image(object_image_folder)
        print(f"Face image loaded successfully")
    except Exception as e:
        print(f"Error loading face image: {e}")
        return None

    new_width = int(object_image.width * height / object_image.height)
    object_image = object_image.resize((new_width, height), Image.LANCZOS)

    # Create a gradient mask for the transition
    gradient_mask = Image.new('L', (new_width, height))
    mask_draw = ImageDraw.Draw(gradient_mask)
    for x in range(new_width):
        # Calculate alpha value (0 = transparent, 255 = opaque)
        alpha = min(255, int(255 * x / (new_width * 0.2)))
        mask_draw.line([(x, 0), (x, height)], fill=alpha)

    # Apply the gradient mask to the object image
    masked_object = Image.new('RGBA', (new_width, height), color='black')
    masked_object.paste(object_image, (0, 0), gradient_mask)

    # Paste the masked object onto the background
    background.paste(masked_object, (width - new_width, 0), masked_object)

    # 2. Text Preprocessing
    text = ' '.join(text.upper().split())
    text_area_width = width - new_width + overlap  # Total width available for text

    # 3. Find Optimal Font Size and Line Breaks
    font_size, lines, metrics = find_optimal_font_size_and_lines(text, font_path, text_area_width - target_padding_left - target_padding_left, height, target_padding_top_bottom, padding_tolerance)

    # 4. Use the metrics returned by find_optimal_font_size_and_lines
    top_padding, bottom_padding, avg_line_width, line_heights = metrics

    # 5. Vertical Alignment
    total_text_height = sum(line_heights)
    y_start = (height - total_text_height) // 2

    # 6. Color Alternation
    colors = ['rgb(255,200,100)', 'rgb(255,255,255)']

    # 7. Create a new transparent layer for the text and shadow
    text_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw_text = ImageDraw.Draw(text_layer)
    draw_shadow = ImageDraw.Draw(shadow_layer)

    # 8. Final Rendering with Shadow
    y = y_start
    font = ImageFont.truetype(font_path, font_size)
    shadow_font = ImageFont.truetype(font_path, font_size)
    shadow_offset = int(font_size * 0.08)
    shadow_color = (0, 0, 0, 150)  # Increased opacity for a stronger shadow
    
    # Calculate the left edge for text alignment
    left_edge = target_padding_left

    for i, line in enumerate(lines):
        # Use left edge for alignment
        x = left_edge
        
        # Draw shadow (multiple layers for a larger, stronger shadow)
        for offset in range(1, 30):
            offset_val = offset * 1.5
            draw_shadow.text((x - offset_val, y - offset_val), line, fill=shadow_color, font=shadow_font)
            draw_shadow.text((x + offset_val, y - offset_val), line, fill=shadow_color, font=shadow_font)
            draw_shadow.text((x - offset_val, y + offset_val), line, fill=shadow_color, font=shadow_font)
            draw_shadow.text((x + offset_val, y + offset_val), line, fill=shadow_color, font=shadow_font)
        
        # Draw actual text
        draw_text.text((x, y), line, fill=colors[i % 2], font=font)
        
        y += line_heights[i]

    # 9. Apply blur to shadow layer
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=int(font_size * 0.15)))  # Slightly reduced blur radius

    # 10. Combine layers
    background = Image.alpha_composite(background.convert('RGBA'), shadow_layer)
    background = Image.alpha_composite(background, text_layer)

    # Save and return
    thumbnail_path = os.path.join(config['paths']['thumbnails'], f'{lang}_{k}.png')
    background.convert('RGB').save(thumbnail_path)
    
    # Calculate max_line_width
    max_line_width = max(font.getbbox(line)[2] for line in lines) if lines else 0
    
    print_debug_info(font_size, len(lines), text_area_width, max_line_width, top_padding, bottom_padding, target_padding_left, avg_line_width)
    print_line_length_stats(lines)  # Add this line
    print(f"Thumbnail saved at: {thumbnail_path}")
    return thumbnail_path

def find_optimal_font_size_and_lines(text, font_path, max_width, max_height, target_padding_top_bottom, padding_tolerance):
    low, high = 10, 200
    best_size = 10
    best_lines = []
    best_score = float('-inf')
    best_metrics = None
    max_iterations = 30  # Increased number of iterations
    
    for iteration in range(max_iterations):
        mid = (low + high) / 2  # Use floating-point division for more precise font sizes
        font_size = int(mid)
        font = ImageFont.truetype(font_path, font_size)
        lines = break_text_into_lines(text, font, max_width)
        line_heights = [font.getbbox(line)[3] for line in lines]
        line_widths = [font.getbbox(line)[2] for line in lines]
        total_height = sum(line_heights)
        top_padding = (max_height - total_height) // 2
        bottom_padding = max_height - total_height - top_padding
        
        score = calculate_score(font_size, lines, line_widths, total_height, top_padding, bottom_padding, target_padding_top_bottom, max_height, max_width)
        
        print(f"Iteration {iteration + 1}: Font size: {font_size}, Lines: {len(lines)}, Total height: {total_height}, Top padding: {top_padding}, Bottom padding: {bottom_padding}, Score: {score:.2f}")
        
        if score > best_score:
            best_size = font_size
            best_lines = lines
            best_score = score
            best_metrics = (top_padding, bottom_padding, statistics.mean(line_widths), line_heights)
        
        if high - low < 1:
            break
        
        if total_height > max_height or score == float('-inf'):
            high = mid
        else:
            low = mid
    
    return best_size, best_lines, best_metrics

def find_optimal_font_size_and_lines_fallback(text, font_path, max_width, max_height, target_padding_top_bottom):
    font_size = 8  # Start with a small font size
    while font_size < 150:
        font = ImageFont.truetype(font_path, font_size)
        lines = break_text_into_lines(text, font, max_width)
        line_heights = [font.getbbox(line)[3] for line in lines]
        total_height = sum(line_heights)
        
        if total_height <= max_height - 2 * target_padding_top_bottom:
            top_padding = (max_height - total_height) // 2
            bottom_padding = max_height - total_height - top_padding
            return font_size, lines, (top_padding, bottom_padding, max_width, line_heights)
        
        font_size += 1
    
    # If we get here, we couldn't fit the text even at 150pt font size
    return 8, textwrap.wrap(text, width=50), (target_padding_top_bottom, target_padding_top_bottom, max_width, [8])

def balance_lines(lines, font, max_width):
    if len(lines) <= 1:
        return lines
    
    words = ' '.join(lines).split()
    balanced_lines = []
    current_line = []
    current_width = 0
    target_width = max_width * 0.9  # Aim for 90% of max width
    
    for word in words:
        word_width = font.getbbox(word)[2]
        if current_width + word_width <= target_width:
            current_line.append(word)
            current_width += word_width + font.getbbox(' ')[2]
        else:
            if current_line:
                balanced_lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                balanced_lines.append(word)
                current_line = []
                current_width = 0
    
    if current_line:
        balanced_lines.append(' '.join(current_line))
    
    return balanced_lines

def break_text_into_lines(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    target_width = max_width * 0.9  # Aim for 90% of max width
    
    for word in words:
        word_width = font.getbbox(word)[2]
        if current_width + word_width <= target_width:
            current_line.append(word)
            current_width += word_width + font.getbbox(' ')[2]
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                # If a single word is too long, split it
                split_word = textwrap.wrap(word, width=max(1, int(target_width / font.getbbox('W')[2])))
                lines.extend(split_word[:-1])
                current_line = [split_word[-1]]
                current_width = font.getbbox(current_line[0])[2]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Balance the last two lines if they're short
    if len(lines) > 1:
        last_line = lines[-1]
        second_last_line = lines[-2]
        if len(last_line) < len(second_last_line) * 0.7:
            words = (second_last_line + ' ' + last_line).split()
            mid = len(words) // 2
            lines[-2] = ' '.join(words[:mid])
            lines[-1] = ' '.join(words[mid:])
    
    return lines

def break_text_into_lines_aggressive(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.getbbox(test_line)[2] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # If a single word is too long, split it
                split_word = []
                for char in word:
                    if font.getbbox(''.join(split_word + [char]))[2] <= max_width:
                        split_word.append(char)
                    else:
                        lines.append(''.join(split_word))
                        split_word = [char]
                if split_word:
                    lines.append(''.join(split_word))
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def print_debug_info(font_size, num_lines, text_width, max_line_width, top_padding, bottom_padding, left_padding, avg_right_padding):
    print(f"Final font size: {font_size}")
    print(f"Number of lines: {num_lines}")
    print(f"Text width: {text_width}")
    print(f"Max line width: {max_line_width}")
    print(f"Top Padding: {top_padding}")
    print(f"Bottom Padding: {bottom_padding}")
    print(f"Left Padding: {left_padding}")
    print(f"Average Right Padding: {avg_right_padding:.2f}")

def get_random_face_image(folder):
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    valid_images = [f for f in os.listdir(folder) if f.lower().endswith(valid_extensions)]
    if not valid_images:
        raise ValueError(f"No valid image files found in {folder}")
    img_path = os.path.join(folder, random.choice(valid_images))
    return Image.open(img_path)

def check_line_length_consistency(lines):
    if not lines:
        return 0.0
    
    line_lengths = [len(line) for line in lines]
    avg_length = sum(line_lengths) / len(line_lengths)
    
    max_diff_percent = max(abs(length - avg_length) / avg_length for length in line_lengths)
    
    return 1.0 - min(max_diff_percent, 0.5)  # Allow up to 50% difference

def print_line_length_stats(lines):
    if not lines:
        print("No lines to analyze.")
        return

    line_lengths = [len(line) for line in lines]
    avg_length = sum(line_lengths) / len(line_lengths)
    shortest_line = min(line_lengths)
    longest_line = max(line_lengths)

    shortest_diff_percent = ((avg_length - shortest_line) / avg_length) * 100
    longest_diff_percent = ((longest_line - avg_length) / avg_length) * 100

    print("\nLine Length Statistics:")
    print(f"Average character length: {avg_length:.2f}")
    print(f"Shortest line: {shortest_line} characters")
    print(f"Shortest line difference from average: {shortest_diff_percent:.2f}%")
    print(f"Longest line: {longest_line} characters")
    print(f"Longest line difference from average: {longest_diff_percent:.2f}%")

def calculate_score(font_size, lines, line_widths, total_height, top_padding, bottom_padding, target_padding_top_bottom, max_height, max_width):
    if total_height > max_height:
        return float('-inf')
    
    padding_score = max(0, 100 - abs(target_padding_top_bottom - top_padding) - abs(target_padding_top_bottom - bottom_padding))
    width_variance = statistics.variance(line_widths) if len(line_widths) > 1 else 0
    line_length_score = check_line_length_consistency(lines)
    space_utilization = total_height / max_height
    
    return (
        font_size * 2 +
        padding_score * 1.5 +  # Increased weight for padding
        (1 / (width_variance + 1)) * 75 +  # Increased weight for width consistency
        line_length_score * 150 +  # Increased weight for line length consistency
        space_utilization * 200
    )

def adjust_lines_for_consistency(lines, font, max_width):
    if len(lines) <= 1:
        return lines
    
    words = ' '.join(lines).split()
    adjusted_lines = []
    current_line = []
    current_width = 0
    target_width = max_width * 0.8
    
    for word in words:
        word_width = font.getbbox(word)[2]
        if current_width + word_width <= target_width:
            current_line.append(word)
            current_width += word_width + font.getbbox(' ')[2]
        else:
            if current_line:
                adjusted_lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                adjusted_lines.append(word)
                current_line = []
                current_width = 0
    
    if current_line:
        adjusted_lines.append(' '.join(current_line))
    
    return adjusted_lines

def main(video_url):
    # video_url = input("Enter the YouTube video URL: ")
    
    thumbnail = get_youtube_thumbnail(video_url)
    if thumbnail is None:
        print("Failed to fetch thumbnail. Exiting.")
        return

    print("Thumbnail fetched successfully. Extracting text...")
    extracted_text = extract_text_from_image(thumbnail)
    
    if not extracted_text:
        print("No text extracted from the thumbnail. Using default text.")
        extracted_text = "AMAZING AI\nDISCOVERY"
    else:
        print(f"Extracted text: {extracted_text}")

    lang = "en"
    k = "001"
    
    try:
        thumbnail_path = generate_thumbnail(extracted_text, lang, k, config, {})
        if thumbnail_path:
            print(f"New thumbnail generated: {thumbnail_path}")
        else:
            print("Failed to generate thumbnail.")
    except Exception as e:
        print(f"An error occurred during thumbnail generation: {e}")

# if __name__ == "__main__":
#     main()




