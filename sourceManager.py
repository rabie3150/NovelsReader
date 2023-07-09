import json
from MadaraScraper import MadaraScraper
from ReadwnScraper import ReadwnScraper
import pickle

def init_source_instance (source):
    # Create an instance of source
    source_scraper_type = source['scraper']
    if source_scraper_type == 'MadaraScraper':
        scraper_instance = MadaraScraper(source['sourceId'], source['baseUrl'],source['sourceName'], source['options'])
    elif source_scraper_type == 'ReadwnScraper':
        scraper_instance = ReadwnScraper(source['sourceId'], source['baseUrl'],source['sourceName'], source['options'])
    return scraper_instance

def get_source_from_source_id(source_id, file_path):
    with open(file_path, 'r') as file:
        sources = json.load(file)

    for source in sources:
        if source['sourceId'] == source_id:
            return source

    return None

def get_source(file_path):
    with open(file_path, 'r') as file:
        sources = json.load(file)

    # Display the available sources
    for i, source in enumerate(sources, start=1):
        print(f"{i}. {source['sourceName']}")

    # Prompt the user to choose a source
    while True:
        choice = input("Choose a source (enter the corresponding number): ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(sources):
                selected_source = sources[index]
                break
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    return selected_source

def check_for_updated_chapters():
    favorites = load_favorites()
    novels = []
    for favorite in favorites:
        
        source_id = favorite['sourceId']
        novel_name = favorite['novelName']
        stored_chapter_count = favorite['chaptersCount']
        novel_url = favorite['novelUrl']
        

        try:    
            # Retrieve the latest chapter count from the source
            source = get_source_from_source_id(source_id,'Sources.json')
            scraper = init_source_instance (source)
            novel_new_meta_data = scraper.parseNovelAndChapters(novel_url)
            latest_chapter_count=novel_new_meta_data['chaptersCount']
        except Exception as e:
            latest_chapter_count = 0
        if latest_chapter_count > stored_chapter_count:
            print(f"New chapters available for '{novel_name}'!  {stored_chapter_count}/{latest_chapter_count}")
            novels.append(favorite)
        else :
            print(f"No updates available for '{novel_name}'!")
            
    if not novels == []:
        return novels
    else:
        return None

# def get_latest_chapter_count(source_id, novel_url):
#     file_path = r"C:\Users\rabie\Desktop\scraper\Madara\MadaraSources.json"
#     source = get_source_from_source_id(source_id, file_path)
    
#     if source:
#         source_id = source['sourceId']
#         base_url = source['baseUrl']
#         source_name = source['sourceName']
#         options = source.get('options', {})  # Provide a default empty dictionary if 'options' key is missing

#         madara_scraper = MadaraScraper(source_id, base_url, source_name, options)

#         novel = madara_scraper.parseNovelAndChapters(novel_url)
        
#         if 'chapters' in novel:
#             latest_chapter_count = len(novel['chapters'])
#             return latest_chapter_count
#         else:
#             print(f"No chapters found for '{novel_url}'.")
#             return 0
#     else:
#         print(f"Source with ID {source_id} not found.")
#         return None



import pickle

def load_favorites():
    try:
        with open('favorites.pkl', 'rb') as file:
            return pickle.load(file)
    except (FileNotFoundError, EOFError):
        return []

def save_favorites(favorites):
    with open('favorites.pkl', 'wb') as file:
        pickle.dump(favorites, file)

def add_to_favorites(novel):
    favorites = load_favorites()

    for fav_novel in favorites:
        if fav_novel['novelUrl'] == novel['novelUrl']:
            # Update the novel if it already exists in favorites
            fav_novel.update(novel)
            save_favorites(favorites)
            print("Novel updated in favorites.")
            return

    favorites.append(novel)
    save_favorites(favorites)
    print("Novel added to favorites successfully.")


def delete_from_favorites(novel):
    favorites = load_favorites()
    found = False
    for fav_novel in favorites:
        if fav_novel['novelUrl'] == novel['novelUrl']:
            favorites.remove(fav_novel)
            found = True
            break

    if found:
        save_favorites(favorites)
        print("Novel deleted from favorites successfully.")
    else:
        print("Novel not found in favorites.")

def list_favorites():
    favorites = load_favorites()
    if len(favorites) == 0:
        print("No novels in favorites.")
    else:
        print("Novels in favorites:")
        for i, novel in enumerate(favorites, start=1):
            print(f"{i}. {novel['novelName']}")

def manage_favorites_menu():
    while True:
        print("\n--- Manage Favorites ---")
        list_favorites()
        print("\n---------------------")        
        print("1. Delete from Favorites")
        print("2. Update Favorites")
        print("Q. Quit")

        choice = input("Enter your choice (1/2/Q): ")

            

        if choice == '1':
            selection = input("Enter the number of the novel to delete (q to quit): ")
            if selection.lower() == 'q':
                continue
            try:
                index = int(selection) - 1
                favorites = load_favorites()
                if 0 <= index < len(favorites):
                    delete_from_favorites(favorites[index])
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'q' to quit.")

        elif choice == '2':
            check_for_updated_chapters()


        elif choice == 'q':
            print("Quitting the favorites menu.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    manage_favorites_menu()
