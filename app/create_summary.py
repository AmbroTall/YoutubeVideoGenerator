import os
import openai

# Set your OpenAI API key
openai.api_key = "your_openai_api_key"  # Replace with your actual OpenAI API key

# Define the path to your files
lang_folder = 'path/to/YOUTUBE_MANAGER/XRP_videos/'  # Update this path
sub_folder = 'English'
filename = 'English_new.txt'

# Construct the full path to the text file
text_file_path = os.path.join(lang_folder, sub_folder, filename)

# Read the content of the text file
with open(text_file_path, "r") as text_file:
    text = text_file.read()

# Initialize variables for tracking GPT costs
tot_gpt_cost = {}
prompt_tokens = 0
completion_tokens = 0

# Define your SEO tags
tags = "xrp, xrp ripple, xrp news, xrp price, xrp crypto, xrp ripple news"

# Make the API call to OpenAI's ChatCompletion
gpt_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    temperature=0.9,
    max_tokens=500,
    messages=[
        {"role": "assistant", "content": "You are an SEO professional for Youtube descriptions in the crypto niche. Output only the final text, do not write anything else."},
        {"role": "user", "content": f'Write a short version of the given text and optimize it for SEO. Write out of the perspective of a XRP enthusiast and XRP maximalist, without stating that in the description. While writing respect the following requirements: \n1. Seamlessly incorporate the target keywords into the content. \n2. When appropriate, divide the content into shorter paragraphs to enhance SEO. \n Here are the keywords for youtube SEO (tags): "{tags}". Here is a transcription of the video: "{text}"'}
    ]
)

# Extract the summary from the response
summary = gpt_response['choices'][0]['message']['content']
prompt_tokens += gpt_response['usage']['prompt_tokens']
completion_tokens += gpt_response['usage']['completion_tokens']

# Calculate the cost of the summary
summary_cost = prompt_tokens * 0.000003 + completion_tokens * 0.000004
print(f'Your spending for the summary of English script is ${summary_cost}')

# Print the summary response
print(gpt_response)

# Save the summary to a new text file
output_file_path = os.path.join(lang_folder, 'TODAY_VIDEOS__', 'English_summary.txt')  # Update this path
with open(output_file_path, "w") as text_file:
    text_file.write(summary)

print(f'Summary saved to {output_file_path}')