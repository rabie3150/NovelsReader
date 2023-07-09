import os
import re
import unicodedata
import sys
from tqdm import tqdm


replacements = {
    "?": " ?",
    "!": " !",
    "“": " \" ",
    "”": " \" ",
    "‘": " ' ",
    '´': "'",
    "’": " ' ",
    "–": "-",
    "—": "-",
    "…": "...",
    "‐": "-",
    "−": "-",
    "•": "*",
    "·": ".",
	"★": 'One star',
	"★★": 'two stars',
	"★★★": 'tree stars',
	"★★★★": 'four stars',
	"★★★★★": 'five stars',
    "§": "section",
    "†": "+",
    "‡": "++",
    "°": " degrees",
    "µ": " micro",
    "€": " Euro",
    "£": " pound",
    "¥": " yen",
    "©": "(c)",
    "®": "(R)",
    "™": "(TM)",
    "≈": " approximately ",
    "≠": " not equal to ",
    "≤": " less than or equal to ",
    "≥": " greater than or equal to ",
    "±": " plus-minus ",
    "∞": " infinity ",
    "√": " square root ",
    "π": " pi ",
    "×": " multiplied by ",
    "÷": " divided by ",
    "   ": " ",
    "   ": " ",
    "   ": " ",
    "→": " ",
    '\n..\n':' ',
    '!'
    '""' :'',
}

def sort_files_by_name(file_list):
    sorted_files = sorted(file_list, key=lambda x: [int(d) if d.isdigit() else d.lower() for d in re.split(r'(\d+)', x)])
    return sorted_files

def clean_text(text):

    # Define the Unicode ranges for characters to keep
    keep_ranges = [(0x0020,  0x00A0),(0x000A,0x000A)]

    # Filter out characters outside the specified Unicode ranges
    filtered_text = ''.join(c for c in text if any(start <= ord(c) <= end for start, end in keep_ranges))

    # Replace special or unusual characters
    for char, replacement in replacements.items():
        filtered_text = filtered_text.replace(char, replacement)
    
    # Avoid repeating characters, words, or groups of words more than three times
    filtered_text = re.sub(r'(\b\w+\b)( \1){3,}', r'\1', filtered_text)

    # Remove punctuation except apostrophes within words, question marks, and exclamation marks
    filtered_text = re.sub(r"(?<=\w)(')(?=\w)", r"\1", filtered_text)
    filtered_text = re.sub(r'(?![\'?!])([!"#$%&()*+,-./:;<=>@[\\]^_`{|}~])', r' \1 ', filtered_text)
    
    return filtered_text

def process_file(file_path):
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Apply text cleaning
    cleaned_content = clean_text(content)

    # Convert content to ASCII
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    
    # Replace consecutive spaces with one space
    content = re.sub(r'\s+', ' ', content)

    # Write the cleaned content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Filter out empty lines and lines containing only whitespace
    filtered_lines = [line for line in lines if line.strip() and any(c.isalpha() for c in line)]

    # Write the cleaned lines back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(filtered_lines)


    
    # with open(file_path, 'w', encoding='utf-8') as new_file:
    #     for line in lines:
    #         if line !='\n' :
    #             if '__________' in line:
    #                 break
    #             new_file.write(line.lstrip())
    
def clean_files_in_folder(folder_path,LIMIT_COUNT = None):
    # Get a list of text files in the folder
    file_list = [file_name for file_name in os.listdir(folder_path) if file_name.endswith('.txt')]
    file_list = sort_files_by_name (file_list)
    if LIMIT_COUNT: file_list = file_list[:LIMIT_COUNT]
    # Initialize a progress bar

    progress_bar = tqdm(total=len(file_list),desc="Cleaning text", unit='scrub')
    
    # Iterate through files in the folder
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        process_file(file_path)
        
        # Update the progress bar
        progress_bar.update(1)
    
    # Close the progress bar
    progress_bar.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        if sys.argv[2] :
            LIMIT_COUNT = int(sys.argv[2])
            clean_files_in_folder(folder_path,LIMIT_COUNT)
        else:
            clean_files_in_folder(folder_path)

    else:
        print("Please provide the folder path as an argument.")
        folder_path = "C:/Users/rabie/Desktop/Input"
        clean_files_in_folder(folder_path)