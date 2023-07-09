import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image
import requests
import json
import os
import pickle
from io import BytesIO
from collections import deque
from bs4 import BeautifulSoup
import requests
from novelmt_scraper import NovelmtScraper

# Global variables
novels = []
selected_novel = None
novel_index = -1
image_cache = {}
deleted_novels = deque()


def load_novels():
    global novels
    with open('C:/Users/rabie/Desktop/scraper/novels.json') as file:
        novels = json.load(file)


def save_novels():
    with open('C:/Users/rabie/Desktop/scraper/novels.json', 'w') as file:
        json.dump(novels, file, indent=4)


def delete_novel():
    selected_index = novel_listbox.curselection()
    if selected_index:
        deleted_novels.append(novels[selected_index[0]])
        del novels[selected_index[0]]
        update_novel_listbox()
        clear_novel_details()


def save_novel_details():
    novel_name = novel_name_entry.get().strip()
    novel_cover_url = novel_cover_url_entry.get().strip()
    novel_url = novel_url_entry.get().strip()

    if novel_name == '' or novel_cover_url == '' or novel_url == '':
        messagebox.showinfo('Error', 'Please enter all fields.')
        return

    global selected_novel, novel_index
    if selected_novel is None:
        new_novel = {
            'novelName': novel_name,
            'novelCover': novel_cover_url,
            'novelUrl': novel_url
        }
        novels.append(new_novel)
    else:
        selected_novel['novelName'] = novel_name
        selected_novel['novelCover'] = novel_cover_url
        selected_novel['novelUrl'] = novel_url

    save_novels()
    update_novel_listbox()
    clear_novel_details()


def select_novel(event):
    global selected_novel, novel_index
    index = novel_listbox.curselection()
    if index:
        novel_index = int(index[0])
        selected_novel = novels[novel_index]
        clear_novel_details()  # Clear the details before displaying the selected novel
        display_novel_details()


def display_novel_details():
    global selected_novel
    if selected_novel is None:
        return

    novel_name_entry.delete(0, tk.END)
    novel_name_entry.insert(tk.END, selected_novel['novelName'])

    novel_cover_url_entry.delete(0, tk.END)
    novel_cover_url_entry.insert(tk.END, selected_novel['novelCover'])

    novel_url_entry.delete(0, tk.END)
    novel_url_entry.insert(tk.END, selected_novel['novelUrl'])

    # Check if placeholder image exists, if not, create it
    placeholder_path = 'placeholder.jpg'
    if not os.path.exists(placeholder_path):
        create_placeholder_image(placeholder_path)

    # Display the novel cover image
    if selected_novel['novelCover'] in image_cache:
        cover_image = image_cache[selected_novel['novelCover']]
        novel_cover_label.configure(image=cover_image)
        novel_cover_label.image = cover_image
    else:
        load_cover_image(selected_novel['novelCover'])

    # Scrape additional details using NovelmtScraper
    scraper = NovelmtScraper(selected_novel['novelUrl'])
    novel_details = scraper.scrape_novel_details()

    # Display additional details
    novel_summary_text.configure(state=tk.NORMAL)
    novel_summary_text.delete('1.0', tk.END)
    novel_summary_text.insert(tk.END, novel_details['summary'])
    novel_summary_text.configure(state=tk.DISABLED)

    novel_genre_label.configure(text=novel_details['genre'])
    novel_status_label.configure(text=novel_details['status'])
    novel_author_label.configure(text=novel_details['author'])


def create_placeholder_image(file_path):
    placeholder_image = Image.new('RGB', (150, 200), (200, 200, 200))
    placeholder_image.save(file_path)


def load_cover_image(url):
    global image_cache
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        image_data = response.raw.read()
        image = Image.open(BytesIO(image_data))
        image = image.resize((150, 200), Image.ANTIALIAS)
        cover_image = ImageTk.PhotoImage(image)
        image_cache[url] = cover_image
        novel_cover_label.configure(image=cover_image)
        novel_cover_label.image = cover_image
    except (requests.RequestException, IOError):
        pass


def clear_novel_details():
    novel_name_entry.delete(0, tk.END)
    novel_cover_url_entry.delete(0, tk.END)
    novel_url_entry.delete(0, tk.END)
    novel_cover_label.configure(image=None)


def open_file_dialog():
    filename = filedialog.askopenfilename(initialdir='/', title='Select JSON file')
    if filename:
        load_novels()
        update_novel_listbox()


def update_novel_listbox():
    novel_listbox.delete(0, tk.END)
    for novel in novels:
        novel_listbox.insert(tk.END, novel['novelName'])


def save_image_cache():
    with open('image_cache.pkl', 'wb') as file:
        pickle.dump(image_cache, file, protocol=pickle.HIGHEST_PROTOCOL)


def load_image_cache():
    global image_cache
    if os.path.exists('image_cache.pkl'):
        with open('image_cache.pkl', 'rb') as file:
            image_cache = pickle.load(file)


def search_novels():
    search_query = search_entry.get().strip().lower()
    if search_query == '':
        messagebox.showinfo('Error', 'Please enter a search query.')
        return

    search_results = []
    for novel in novels:
        if search_query in novel['novelName'].lower():
            search_results.append(novel)

    if len(search_results) == 0:
        messagebox.showinfo('Search Results', 'No matching novels found.')
    else:
        display_search_results(search_results)


def display_search_results(results):
    global selected_novel, novel_index
    novel_listbox.delete(0, tk.END)
    for index, novel in enumerate(novels):
        if novel in results:
            novel_listbox.insert(tk.END, novel['novelName'])
            if novel == selected_novel:
                novel_index = results.index(novel)  # Update the novel_index based on the search results
                novel_listbox.selection_set(len(novel_listbox.get(0, tk.END)) - 1)


def clear_search_results():
    search_entry.delete(0, tk.END)
    update_novel_listbox()


def undo_delete():
    if deleted_novels:
        novel = deleted_novels.pop()
        novels.append(novel)
        update_novel_listbox()


def move_novel_up():
    global selected_novel, novel_index
    if novel_index > 0:
        novels[novel_index], novels[novel_index - 1] = novels[novel_index - 1], novels[novel_index]
        novel_index -= 1
        update_novel_listbox()


def move_novel_down():
    global selected_novel, novel_index
    if novel_index < len(novels) - 1:
        novels[novel_index], novels[novel_index + 1] = novels[novel_index + 1], novels[novel_index]
        novel_index += 1
        update_novel_listbox()


def main():
    global novel_listbox, novel_name_entry, novel_cover_url_entry, novel_url_entry, novel_cover_label, search_entry
    global novel_summary_text, novel_genre_label, novel_status_label, novel_author_label

    root = tk.Tk()
    root.title('Novel Scraper')
    root.geometry('900x400')

    # Create listbox to display the novels
    novel_listbox = tk.Listbox(root, width=40)
    novel_listbox.bind('<<ListboxSelect>>', select_novel)

    # Create labels and entry fields for novel details
    novel_name_label = tk.Label(root, text='Novel Name:')
    novel_name_entry = tk.Entry(root, width=50)

    novel_cover_url_label = tk.Label(root, text='Novel Cover URL:')
    novel_cover_url_entry = tk.Entry(root, width=50)

    novel_url_label = tk.Label(root, text='Novel URL:')
    novel_url_entry = tk.Entry(root, width=50)

    # Create a label to display the novel cover image
    novel_cover_label = tk.Label(root)

    # Create labels to display additional novel details
    novel_summary_label = tk.Label(root, text='Summary:')
    novel_summary_text = tk.Text(root, width=50, height=5, state=tk.DISABLED)

    novel_genre_label = tk.Label(root, text='Genre:')
    novel_status_label = tk.Label(root, text='Status:')
    novel_author_label = tk.Label(root, text='Author:')

    # Create buttons
    save_button = tk.Button(root, text='Save', command=save_novel_details)
    delete_button = tk.Button(root, text='Delete', command=delete_novel)
    undo_button = tk.Button(root, text='Undo', command=undo_delete)
    save_changes_button = tk.Button(root, text='Save Changes', command=save_novels)
    load_button = tk.Button(root, text='Load', command=open_file_dialog)
    search_label = tk.Label(root, text='Search:')
    search_entry = tk.Entry(root, width=40)
    search_button = tk.Button(root, text='Search', command=search_novels)
    clear_search_button = tk.Button(root, text='Clear', command=clear_search_results)
    move_up_button = tk.Button(root, text='Move Up', command=move_novel_up)
    move_down_button = tk.Button(root, text='Move Down', command=move_novel_down)
    scrape_details_button = tk.Button(root, text='Scrape Details', command=display_novel_details)

    novel_listbox.place(x=10, y=10, width=250, height=300)
    novel_name_label.place(x=280, y=10)
    novel_name_entry.place(x=400, y=10, width=400)
    novel_cover_url_label.place(x=280, y=50)
    novel_cover_url_entry.place(x=400, y=50, width=400)
    novel_url_label.place(x=280, y=90)
    novel_url_entry.place(x=400, y=90, width=400)
    save_button.place(x=400, y=130)
    delete_button.place(x=470, y=130)
    undo_button.place(x=540, y=130)
    save_changes_button.place(x=620, y=130)
    load_button.place(x=700, y=130)
    novel_cover_label.place(x=280, y=180)
    novel_summary_label.place(x=280, y=220)
    novel_summary_text.place(x=400, y=220)
    novel_genre_label.place(x=280, y=290)
    novel_status_label.place(x=400, y=290)
    novel_author_label.place(x=500, y=290)
    search_label.place(x=10, y=330)
    search_entry.place(x=60, y=330, width=200)
    search_button.place(x=280, y=330)
    clear_search_button.place(x=330, y=330)
    move_up_button.place(x=750, y=10)
    move_down_button.place(x=750, y=50)
    scrape_details_button.place(x=750, y=90)

    # Load novels and image cache
    load_novels()
    load_image_cache()

    # Update the novel listbox
    update_novel_listbox()

    # Start the tkinter event loop
    root.mainloop()


if __name__ == '__main__':
    main()
