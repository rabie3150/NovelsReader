# -*- coding: utf-8 -*-
import os
import json
import sourceManager as SM
import tiktok_tts
import concurrent.futures
from tqdm import tqdm
from halo import Halo
import win32api
import win32con
import re


from MadaraScraper import MadaraScraper
from ReadwnScraper import ReadwnScraper




            




def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def print_sources(sources):
    print("Available Sources:")
    for i, source in enumerate(sources, start=1):
        print(f"{i}. {source['sourceName']}")
    print()

def get_source_choice(sources):
    while True:
        choice = input("Choose a source (enter the corresponding number): ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(sources):
                return sources[index]
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def browse_hot_novels(scraper):
    if scraper.scraper == "MadaraScraper" :
        page = input("Enter the page number to browse (default is 1): ")
        page = int(page) if page.isdigit() else 1
        show_latest_novels = input("Show latest novels instead of most viewed? (Y/N): ").lower() == 'y'
        result = scraper.popularNovels(page=page, show_latest_novels=show_latest_novels)
        novels = result['novels']
    else :
        novels = scraper.popularNovels()
    

    clear_screen()
    print("Hot Novels:")
    for i, novel in enumerate(novels, start=1):
        print(f"{i}. {novel['novelName']}")
    print()

    return novels

def search_novels(scraper):
    search_term = input("Enter the search term: ")
    novels = scraper.searchNovels(search_term)

    clear_screen()
    print(f"Search results for '{search_term}':")
    for i, novel in enumerate(novels, start=1):
        print(f"{i}. {novel['novelName'].encode('utf-8').decode('utf-8')}")

    print()

    return novels

def select_novel(novels, scraper):
    while True:
        choice = input("Choose a novel (enter the corresponding number): ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(novels):
                novel = novels[index]
                novel_details = scraper.parseNovelAndChapters(novel['novelUrl'])
                novel.update(novel_details)
                return novel
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def print_chapters(novel, use_pages=True):
    chapters = novel['chapters']
    per_page = 10  # Number of chapters to display per page
    total_pages = (len(chapters) + per_page - 1) // per_page
    current_page = 1

    if use_pages:
        while True:
            clear_screen()
            print(f"Novel: {novel['novelName']}\n")
            print("Chapters:")

            start_index = (current_page - 1) * per_page
            end_index = start_index + per_page
            displayed_chapters = chapters[start_index:end_index]

            for i, chapter in enumerate(displayed_chapters, start=start_index+1):
                print(f"{i}. {chapter['chapterName']}")

            print()
            print("Pagination:")
            print(f"Page {current_page}/{total_pages}")
            print("Options: First | Previous | Next | Last | Custom | Quit")

            choice = input("Enter your choice: ")
            if choice.lower() == 'first':
                current_page = 1
            elif choice.lower() == 'previous':
                current_page = max(current_page - 1, 1)
            elif choice.lower() == 'next':
                current_page = min(current_page + 1, total_pages)
            elif choice.lower() == 'last':
                current_page = total_pages
            elif choice.lower() == 'custom':
                page = input("Enter the page number: ")
                try:
                    page = int(page)
                    if 1 <= page <= total_pages:
                        current_page = page
                    else:
                        print("Invalid page number. Please enter a valid page.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            elif (choice.lower() == 'quit') or (choice.lower() == ''):
                break
            else:
                print("Invalid choice. Please enter a valid option.")
    else:
        clear_screen()
        print(f"Novel: {novel['novelName']}\n")
        print("Chapters:")

        for i, chapter in enumerate(chapters, start=1):
            print(f"{i}. {chapter['chapterName']}")

def read_chapter(novel, scraper, use_pages=True):
    print_chapters(novel, use_pages=True)
    while True:
        choice = input("Choose a chapter to read (enter the corresponding number or 'q' to go back): ")
        if choice.lower() == 'q':
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(novel['chapters']):
                chapter = novel['chapters'][index]
                chapter_text = scraper.parseChapter(novel['novelUrl'], chapter['chapterUrl'])
                
                clear_screen()
                print(f"Chapter: {chapter['chapterName']}\n")
                print(chapter_text['chapterText'])
                input("\nPress Enter to continue...")
                break
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def download_chapters(novel, scraper, default_output_dir=False ,download_option =None,start_chapter=None,end_chapter=None, show_progress_bar=True):
    if default_output_dir :
        output_dir =".\downloads"
    else :
        output_dir = input("Enter the output directory path (default is current directory): ") or ".\downloads"
        
    novel_folder_name = abbreviate_name(novel['novelName'])

    novel_dir = os.path.join(output_dir, novel_folder_name)
    os.makedirs(novel_dir, exist_ok=True)

    if not download_option :
        download_option = input("Choose download option (1: Single chapter, 2: Range of chapters): ")

    if download_option == "1":
        # Download a single chapter
        chapter_number = int(input("Enter the chapter number: "))
        chapter = novel['chapters'][chapter_number - 1]  # Adjust index to match chapter numbers
        chapter_filename = abbreviate_name(novel['novelName'], chapter['chapterName'], extension='.txt')
        chapter_file_path = os.path.join(novel_dir, chapter_filename)

        if os.path.exists(chapter_file_path):
            #print(f"Chapter {chapter_number} already exists. Skipping download.")
            pass
        else:
            chapter_text = scraper.parseChapter(novel['novelUrl'], chapter['chapterUrl'])
            with open(chapter_file_path, 'w', encoding='utf-8') as f:
                f.write(chapter_text['chapterText'])
            print(f"Chapter {chapter_number} downloaded to: {chapter_file_path}")
    else :
        # Download a range of chapters
        if not start_chapter :
            start_chapter = int(input("Enter the start chapter number (default: 1): ") or 1)
        if not end_chapter :
            end_chapter = int(input(f"Enter the end chapter number (default: {len(novel['chapters'])}): ")
                          or len(novel['chapters']))
        chapters = novel['chapters'][start_chapter - 1:end_chapter]  # Adjust indices to match chapter numbers

        for chapter in tqdm(chapters, desc="Downloading Chapters", disable=not show_progress_bar):
            chapter_filename = abbreviate_name(novel['novelName'], chapter['chapterName'], extension='.txt')
            chapter_file_path = os.path.join(novel_dir, chapter_filename)
            chapter_done_file_path = os.path.join(novel_dir,'Done' ,chapter_filename)
            if os.path.exists(chapter_file_path) or os.path.exists(chapter_done_file_path):
                #print(f"Chapter {chapter['chapterName']} already exists. Skipping download.")
                pass
            else:
                chapter_text = scraper.parseChapter(novel['novelUrl'], chapter['chapterUrl'])
                with open(chapter_file_path, 'w', encoding='utf-8') as f:
                    f.write(chapter_text['chapterText'])

        print(f"Chapters {start_chapter} to {end_chapter} downloaded to: {novel_dir}")

    return novel_dir

def sort_files_by_name(file_list):
    sorted_files = sorted(file_list, key=lambda x: [int(d) if d.isdigit() else d.lower() for d in re.split(r'(\d+)', x)])
    return sorted_files

def transform_to_audio(output_dir,LIMIT_COUNT=None):

    # voice = tiktok_tts.voice_selector() # Prompt the user to choose a voice using the voice_selector() function
    voice = "en_us_010"
    '''
    text_files = [file for file in os.listdir(output_dir) if file.endswith('.txt')] # Get the list of text files in the output directory

    if not text_files:
        print("No text files found in the output directory. Please download chapters first.")
        return
    '''
    # Create a directory to store the audio
    audio_dir = os.path.join(output_dir, "Audio")
    os.makedirs(audio_dir, exist_ok=True)

    # Convert the folder to speech using convert_folder_to_speech() function
    tiktok_tts.convert_folder_to_speech(voice=voice, input_folder=output_dir, output_folder=audio_dir,LIMIT_COUNT=LIMIT_COUNT)

    print("Conversion completed. Audio files are saved in the 'Audio' directory.")

def search_novel_in_sources(novel_name, get_chapters_count=True, use_loading_bar=True, use_halo_spinner=False, display_result=True):
    sources_file = r"C:\Users\rabie\Desktop\scraper\Sources.json"
    with open(sources_file, 'r', encoding='utf-8') as f:
        sources = json.load(f)

    novels_found = []

    def search_source(source):
        try:
            scraper = init_source_instance(source)
            novels = scraper.searchNovels(novel_name)

            # if get_chapters_count:
            #     for novel in novels:
            #         novel_details = scraper.parseNovelAndChapters(novel['novelUrl'])
            #         novel['chaptersCount'] = len(novel_details['chaptersCount'])
                    

            for novel in novels:
                novel['sourceName'] = source['sourceName']
                novels_found.append(novel)

        except Exception as e:
            pass  # Ignore the error silently without displaying it

    total_sources = len(sources)

    if use_loading_bar:
        with tqdm(total=total_sources, desc="Searching") as pbar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(search_source, source) for source in sources]
                for future in concurrent.futures.as_completed(futures):
                    pbar.update(1)
    elif use_halo_spinner:
        with Halo(text="Searching", spinner="dots") as spinner:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(search_source, source) for source in sources]
                for future in concurrent.futures.as_completed(futures):
                    spinner.start()
            spinner.stop()

    novels_found = sorted(novels_found, key=lambda x: x.get('chaptersCount', 0), reverse=True)

    if display_result :
        if novels_found:
            print("Search results:")
            for i, novel in enumerate(novels_found, start=1):
                print(f"{i}. Novel: {novel['novelName']} (Source: {novel['sourceName']}) (chapters count: {novel['chaptersCount']})")

            selected_novel_index = int(input("Select a result to add to favorites (enter the corresponding number): "))
            if 1 <= selected_novel_index <= len(novels_found):
                selected_novel = (novels_found[selected_novel_index - 1])
            else:
                print("Invalid selection. No novel added to favorites.")

        else:
            print("No novels found.")
    if selected_novel:
        return selected_novel

def choose_a_novel(novels):
    if len(novels) == 0:
        print("No novels in favorites.")
    else:
        print("Novels in favorites:")
        for i, novel in enumerate(novels, start=1):
            print(f"{i}. {novel['novelName']}")

        while True:
            selection = input("Enter the number of the novel to select (q to quit): ")
            if selection.lower() == 'q':
                return None

            try:
                index = int(selection) - 1
                if 0 <= index < len(novels):
                    return novels[index]
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'q' to quit.")

    return None

def show_novel_details(novel):
    print("Novel Details:")
    print("--------------")
    if 'sourceId' in novel:
        print(f"Source ID: {novel['sourceId']}")
    if 'novelName' in novel:
        print(f"Novel Name: {novel['novelName']}")
    if 'novelCover' in novel:
        print(f"Novel Cover: {novel['novelCover']}")
    if 'novelFullUrl' in novel:
        print(f"Novel URL: {novel['novelFullUrl']}")
    if 'chaptersCount' in novel:
        print(f"Chapters Count: {novel['chaptersCount']}")
    if 'sourceName' in novel:
        print(f"Source Name: {novel['sourceName']}")
    if 'author' in novel:
        print(f"Author: {novel['author']}")
    if 'genre' in novel:
        print(f"Genre: {novel['genre']}")
    if 'status' in novel:
        print(f"Status: {novel['status']}")
    if 'summary' in novel:
        print(f"Summary: {novel['summary']}")
  
def abbreviate_name(novel_name,chapter_name=None,extension=''):
    novel_name= sanitize_filename(novel_name)
    if len(novel_name) > 40 :
        novelName = ''.join(word[0].upper() for word in novel_name.split(' '))
    else : novelName = novel_name
    if chapter_name : 
        chapter_name= sanitize_filename(chapter_name)
        if len(f"{novelName} - {chapter_name}") > 64 :
            chapter_filename = f"{novelName} - {chapter_name}"[:64]
        else : chapter_filename = f"{novelName} - {chapter_name}"
    else : chapter_filename = novelName
    if extension : chapter_filename = f"{chapter_filename}{extension}"
    return chapter_filename

def sanitize_filename(filename):
    # Replace invalid characters in the filename with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def set_file_title(file_path, title):
    # Get the absolute path
    abs_file_path = os.path.abspath(file_path)
    
    # Set the title property using the Windows API
    try:
        win32api.SetFileAttributes(abs_file_path, win32con.FILE_ATTRIBUTE_NORMAL)
        win32api.SetFileTitle(abs_file_path, title)
    except Exception as e:
        print(f"Error setting file title: {e}")

def get_subdirectories(folder_path = r'.\downloads'):
    subdirectories = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            subdirectories.append(item_path)
    return subdirectories

def init_source_instance (source):
    # Create an instance of source
    source_scraper_type = source['scraper']
    if source_scraper_type == 'MadaraScraper':
        scraper_instance = MadaraScraper(source['sourceId'], source['baseUrl'],source['sourceName'], source['options'])
    elif source_scraper_type == 'ReadwnScraper':
        scraper_instance = ReadwnScraper(source['sourceId'], source['baseUrl'],source['sourceName'], source['options'])
    return scraper_instance



def browse_novel(novel, scraper):
    while True:
        clear_screen()
        print(f"Novel: {novel['novelName']}\n")
        print("1. Show details")
        print("2. Read Chapter")
        print("3. Download Chapters")
        print("4. Add to Favorites")
        print("Q. Go back")
        choice = input("Enter your choice: ")

        if choice == '1':
            show_novel_details(novel)
            input('\nPress Enter to continue...')
        elif choice == '2':
            read_chapter(novel, scraper)
        elif choice == '3':
            transform_choice = input("Do you want to transform the chapters to audio? (Y/N): ").lower()
            output_dir = download_chapters(novel, scraper)
            if transform_choice == 'y':
                transform_to_audio(output_dir)
        elif choice == '4':
            SM.add_to_favorites(novel)
        elif choice.lower() == 'q':
            break
        else:
            print("Invalid choice. Please enter a valid option.")

def search_novel(novel_name):
    novel = search_novel_in_sources(novel_name, get_chapters_count=True, use_loading_bar=True, use_halo_spinner=False)

    if novel:
        source_choice_r = SM.get_source_from_source_id(novel['sourceId'], sources_file)
        scrape_r = init_source_instance(source_choice_r)
        novel_details = scrape_r.parseNovelAndChapters(novel['novelUrl'])
        novel.update(novel_details)
        browse_novel(novel, scrape_r)

def browse_source(scraper):
    while True:
        clear_screen()
        print("1. Browse Hot Novels")
        print("2. Search Novels")
        print("Q. Quit")
        choice = input("Enter your choice: ")

        if choice == '1':
            clear_screen()
            novels = browse_hot_novels(scraper)
            if novels:
                novel = select_novel(novels, scraper)
                if novel:
                    browse_novel(novel, scraper)
        elif choice == '2':
            clear_screen()
            novels = search_novels(scraper)
            if novels:
                novel = select_novel(novels, scraper)
                if novel:
                    browse_novel(novel, scraper)
        elif choice.lower() == 'q':
            break
        else:
            print("Invalid choice. Please enter a valid option.")


def main():

    # Load Madara sources from JSON file
    sources_file = r"C:\Users\rabie\Desktop\scraper\Sources.json"
    with open(sources_file, 'r', encoding='utf-8') as f:
        sources = json.load(f)

    while True:
        clear_screen()
        print("1. Browse a source")
        print("2. Check for Updated Chapters")
        print("3. Search Novels in all Sources")
        print("4. Transform all downloads to speech")
        print("Q. Quit")
        choice = input("Enter your choice: ")

        if choice == '1':
            clear_screen()
            print_sources(sources)
            source_choice = get_source_choice(sources)
            scraper = init_source_instance(source_choice)
            browse_source(scraper)
        elif choice == '2':
            clear_screen()
            updated_novels = SM.check_for_updated_chapters()
            if updated_novels:
                for novel in updated_novels:
                    source_choice_r = SM.get_source_from_source_id(novel['sourceId'], sources_file)
                    scrape_r = init_source_instance(source_choice_r)
                    novel_details = scrape_r.parseNovelAndChapters(novel['novelUrl'])
                    novel.update(novel_details)
                    #need to be changed to only download the new chapters start from previous last chapter to new last chapter
                    output_dir = download_chapters(novel, scrape_r, default_output_dir=True, download_option=2,
                                                   start_chapter=1, end_chapter=len(novel['chapters']),
                                                   show_progress_bar=True)
                    SM.add_to_favorites(novel)
            else:
                print("No novels with updated chapters found.")
        elif choice == '3':
            clear_screen()
            novel_name = input("Enter the name of the novel: ")
            search_novel(novel_name)
        elif choice == '4':
            clear_screen()
            subdirectories = get_subdirectories()
            if len(subdirectories) == 0:
                print("No downloaded novels found.")
                continue

            print("Downloaded Novels:")
            for i, directory in enumerate(subdirectories):
                print(f"{i + 1}. {os.path.basename(directory)}")

            novels_to_transform = input("Enter the numbers of the novels to transform (separated by spaces), "
                                        "or 'all' for all of them: ")
            LIMIT_COUNT = input("Enter the limit number of chapters to convert, or 'all' for all of them: ")
            if novels_to_transform == 'all':
                novels_to_transform = range(1, len(subdirectories) + 1)
            else:
                novels_to_transform = map(int, novels_to_transform.split())

            for i in novels_to_transform:
                if i < 1 or i > len(subdirectories):
                    print(f"Invalid novel number: {i}")
                    continue

                directory = subdirectories[i - 1]

                if LIMIT_COUNT == 'all':
                    transform_to_audio(directory)
                else:
                    transform_to_audio(directory, int(LIMIT_COUNT))
        elif choice.lower() == 'q':
            break
        else:
            print("Invalid choice. Please enter a valid option.")


if __name__ == "__main__":
    main()
