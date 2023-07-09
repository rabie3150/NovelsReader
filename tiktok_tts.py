import os
import requests
import base64
import time
from concurrent.futures import ThreadPoolExecutor
import subprocess
import shutil
from tqdm import tqdm
import re

ENDPOINT = 'https://tiktok-tts.weilnet.workers.dev'
ENDPOINT_2 = 'https://api.almix.net/v1/tts' # backup endpoint

MAX_TEXT_LENGTH = 280
RETRY_COUNT = 5
RETRY_DELAY = 2
MAX_CONCURRENT_THREADS = 16

def clean_folder(folder_path,LIMIT_COUNT=None):
    cleaner_script = r'c:/Users/rabie/Desktop/scraper/cleaner.py'
    if LIMIT_COUNT : subprocess.run(['python', cleaner_script, folder_path,str(LIMIT_COUNT)])
    else: subprocess.run(['python', cleaner_script, folder_path])
    
def get_api_status():
    url = f'{ENDPOINT}/api/status'
    response = requests.get(url)
    data = response.json()
    return data

def generate_audio(text, voice):
    url = f'{ENDPOINT}/api/generation'
    data = {'text': text, 'voice': voice}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    audio_data = response_data['data']
    return audio_data

def split_text(text):
    text_parts = []
    while len(text) > MAX_TEXT_LENGTH:
        idx = MAX_TEXT_LENGTH
        separator = idx
        while idx > 0 and idx > MAX_TEXT_LENGTH - 100:
            if text[idx] in ('.', ','):
                separator = idx + 1
                break
            idx -= 1
        if text[:separator] != '':
            text_parts.append(text[:separator])
        text = text[separator:].strip()

    if text.strip() == '' or not any(char.isalnum() for char in text.strip()):
        # If the remaining text is empty or contains only special characters, reduce MAX_TEXT_LENGTH
        reduced_length = MAX_TEXT_LENGTH - 40
        if reduced_length < 40:
            # Minimum length to avoid an infinite loop
            reduced_length = 40
        if len(text_parts) == 0:
            # Entire text was empty or contained only special characters
            text_parts.append(text[:reduced_length])
        else:
            # Last part of the text was empty or contained only special characters
            text_parts[-1] += text[:reduced_length]
        text = text[reduced_length:].strip()

    text_parts.append(text)
    return text_parts

def generate_audio_file(text, voice, filename, input_file_path, retry_text_length=None):
    audio_data_parts = []

    if retry_text_length is not None:
        global MAX_TEXT_LENGTH
        MAX_TEXT_LENGTH = retry_text_length

    text_parts = split_text(text)

    for i, part in enumerate(text_parts, start=1):
        audio_data = None
        retry = 0
        while audio_data is None and retry < RETRY_COUNT:
            audio_data = generate_audio(part, voice)
            if audio_data is None:
                retry += 1
                time.sleep(RETRY_DELAY)
        if audio_data is not None:
            audio_data_parts.append(audio_data)
        else:
            error_message = f"Failed to generate audio for file: {filename}\nPart {i}:\n{part}\n"
            with open("error_log.txt", "a") as log_file:
                log_file.write(error_message)
            # Retry the whole text file with a different MAX_TEXT_LENGTH
            if retry < RETRY_COUNT and retry_text_length is None:
                print(f"Retrying the whole text file with MAX_TEXT_LENGTH = {MAX_TEXT_LENGTH - 50}")
                return generate_audio_file(text, voice, filename, input_file_path, retry_text_length=MAX_TEXT_LENGTH - 40)

    #if len(audio_data_parts) == len(text_parts):
    audio_data = ''.join(audio_data_parts)
    audio_bytes = base64.b64decode(audio_data)
    with open(filename, 'wb') as file:
        file.write(audio_bytes)
    # print(f'Successfully generated audio file: {filename}')
    input_file_dir = os.path.dirname(input_file_path)
    done_folder = os.path.join(input_file_dir, "Done")
    if not os.path.exists(done_folder):
        os.makedirs(done_folder)
    shutil.move(input_file_path, os.path.join(done_folder, os.path.basename(input_file_path)))
    #print(f'Moved input file to: {os.path.join(done_folder, os.path.basename(input_file_path))}')
    #else:
    #    print(f'\nError generating audio for file: {filename}')

def process_file(input_file_path, output_file_path, voice, progress_bar):
    if os.path.exists(output_file_path):
        print(f'Skipping file {input_file_path}. Output file already exists.')
        progress_bar.update(1)
    else:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        generate_audio_file(text, voice, output_file_path, input_file_path)
        progress_bar.update(1)

def voice_selector ():
    voices = {
        "en_us_ghostface": "Ghost Face",
        "en_us_chewbacca": "Chewbacca",
        "en_us_c3po": "C3PO",
        "en_us_stitch": "Stitch",
        "en_us_stormtrooper": "Stormtrooper",
        "en_us_rocket": "Rocket",
        "en_female_madam_leota": "Madame Leota",
        "en_male_ghosthost": "Ghost Host",
        "en_male_pirate": "Pirate",
        "en_au_001": "English AU - Female",
        "en_au_002": "English AU - Male",
        "en_uk_001": "English UK - Male 1",
        "en_uk_003": "English UK - Male 2",
        "en_us_001": "English US - Female 1",
        "en_us_002": "English US - Female 2",
        "en_us_006": "English US - Male 1",
        "en_us_007": "English US - Male 2",
        "en_us_009": "English US - Male 3",
        "en_us_010": "English US - Male 4",
        "en_male_narration": "Narrator",
        "en_male_funny": "Wacky",
        "en_female_emotional": "Peaceful",
        "en_male_cody": "Serious",
        "fr_001": "French - Male 1",
        "fr_002": "French - Male 2",
        "de_001": "German - Female",
        "de_002": "German - Male",
        "es_002": "Spanish - Male",
        "es_mx_002": "Spanish MX - Male",
        "br_001": "Portuguese BR - Female 1",
        "br_003": "Portuguese BR - Female 2",
        "br_005": "Portuguese BR - Male",
        "jp_001": "Japanese - Female 1",
        "jp_003": "Japanese - Female 2",
        "jp_005": "Japanese - Female 3",
        "jp_006": "Japanese - Male",
        "kr_002": "Korean - Male 1",
        "kr_004": "Korean - Male 2",
        "kr_003": "Korean - Female",
        "en_female_f08_salut_damour": "Alto",
        "en_male_m03_lobby": "Tenor",
        "en_male_m03_sunshine_soon": "Sunshine Soon",
        "en_female_f08_warmy_breeze": "Warmy Breeze",
        "en_female_ht_f08_glorious": "Glorious",
        "en_male_sing_funny_it_goes_up": "It Goes Up",
        "en_male_m2_xhxs_m03_silly": "Chipmunk",
        "en_female_ht_f08_wonderful_world": "Dramatic"
    }

    print("Please choose a voice:")
    for index, value in enumerate(voices.values(), 1):
        print(f"{index}. {value}")

    choice = -1
    while int(choice) not in range(1, 48):
        choice = input("Enter the number of your choice: ")
        if choice == '':
            choice = 19

    # Get the corresponding key based on the selected value
    voice_name = list(voices.values())[int(choice) - 1]
    voice_id = list(voices.keys())[list(voices.values()).index(voice_name)]

    # print("You selected:", )
    # print("Key of the selected value:", )
    return voice_id ,voice_name

def convert_text_to_speech(text, voice, output_file_path):
    return generate_audio_file(text, voice, output_file_path, None)

def convert_text_file_to_speech(input_file_path, voice, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    generate_audio_file(text, voice, output_file_path, input_file_path)

def sort_files_by_name(file_list):
    sorted_files = sorted(file_list, key=lambda x: [int(d) if d.isdigit() else d.lower() for d in re.split(r'(\d+)', x)])
    return sorted_files

def convert_folder_to_speech(voice=None, input_folder="C:/Users/rabie/Desktop/Input", output_folder="C:/Users/rabie/Desktop/Output", MAX_CONCURRENT_THREADS=16,LIMIT_COUNT=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if LIMIT_COUNT :clean_folder(input_folder,LIMIT_COUNT)
    else : clean_folder(input_folder)
    

    if voice:
        voice_id = voice
    else:
        voice_id, voice_name = voice_selector()

    file_names = os.listdir(input_folder)
    file_names = sort_files_by_name(file_names)
    if LIMIT_COUNT :
        try:
            file_names = file_names[:LIMIT_COUNT+1]
        except:
            pass
    file_names = [file_name for file_name in file_names if file_name.endswith('.txt')]

    try:
        file_names_sorted = sorted(file_names, key=lambda x: int(x.split('.')[0][4:]))
    except:
        file_names_sorted = sorted(file_names)

    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_THREADS)

    total_files = len(file_names_sorted)
    progress_bar = tqdm(total=total_files, desc="Progress", unit="file")

    for file_name in file_names_sorted:
        input_file_path = os.path.join(input_folder, file_name)
        output_file_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + ".mp3")

        if os.path.exists(output_file_path):
            #print(f"Chapter {file_name} already converted. Skipping conversion.")
            progress_bar.update(1)
        else:
            executor.submit(process_file, input_file_path, output_file_path, voice_id, progress_bar)

    executor.shutdown()
    progress_bar.close()


def main():
    convert_folder_to_speech()


if __name__ == "__main__":
    main()