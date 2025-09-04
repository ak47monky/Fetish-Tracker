import tkinter as tk
import sqlite3
import tkinter.messagebox as messagebox
import customtkinter
import requests
from PIL import Image, ImageTk
import io
import os
import threading
import textwrap

# --- Configuration & Setup (No Changes) ---
ANILIST_API_URL = 'https://graphql.anilist.co'
ANILIST_SEARCH_QUERY = '''
query ($search: String) {
  Page (page: 1, perPage: 10) {
    media (search: $search, type: ANIME) {
      id
      title {
        romaji
      }
      episodes
      coverImage {
        large
      }
    }
  }
}
'''
ANILIST_DETAIL_QUERY = '''
query ($id: Int) {
  Media (id: $id, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    description(asHtml: false)
    startDate {
      year
    }
    season
    episodes
    status
    genres
    coverImage {
      extraLarge
      large
    }
    relations {
      edges {
        relationType(version: 2)
        node {
          id
          title {
            romaji
          }
          type
          coverImage {
            large
          }
        }
      }
    }
  }
}
'''
STATUS_COLORS = {
    "Watching": "#4CAF50",
    "Completed": "#2196F3",
    "Plan to Watch": "#9E9E9E",
    "On Hold": "#FFC107",
    "Dropped": "#F44336"
}
api_results = []
search_panel_last_width = 350
sash_width = 6
def get_image_path(anime_id):
    return os.path.join("images", f"{anime_id}.png")
def save_image_from_url(url, anime_id):
    if not os.path.exists("images"): os.makedirs("images")
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(get_image_path(str(anime_id)), 'wb') as f:
                for chunk in response.iter_content(1024): f.write(chunk)
            return True
    except Exception as e:
        print(f"Failed to save image from URL: {e}")
    return False
def setup_database():
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS anime (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            episodes INTEGER,
            status TEXT DEFAULT 'Watching',
            image_url TEXT
        )
    ''')
    try:
        c.execute("PRAGMA table_info(anime)")
        columns = [info[1] for info in c.fetchall()]
        if 'status' not in columns: c.execute("ALTER TABLE anime ADD COLUMN status TEXT DEFAULT 'Watching'")
        if 'episodes' not in columns: c.execute("ALTER TABLE anime ADD COLUMN episodes INTEGER")
        if 'image_url' not in columns: c.execute("ALTER TABLE anime ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()
def add_anime_to_db(anime_id, title, episodes, image_url, initial_progress=0, initial_status="Watching"):
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO anime (id, title, progress, episodes, status, image_url) VALUES (?, ?, ?, ?, ?, ?)",
              (str(anime_id), title, initial_progress, episodes, initial_status, image_url))
    conn.commit()
    conn.close()
def get_all_anime(search_query="", status_filter="All"):
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    sql_query = "SELECT id, title, progress, status, episodes, image_url FROM anime WHERE title LIKE ?"
    params = ('%' + search_query + '%',)
    if status_filter != "All":
        sql_query += " AND status = ?"
        params += (status_filter,)
    c.execute(sql_query, params)
    anime_data = c.fetchall()
    conn.close()
    return anime_data
def get_anime_data(anime_id):
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    c.execute("SELECT title, progress, status, episodes, image_url FROM anime WHERE id = ?", (str(anime_id),))
    data = c.fetchone()
    conn.close()
    return data
def update_anime_progress(anime_id, new_progress):
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    c.execute("UPDATE anime SET progress = ? WHERE id = ?", (new_progress, str(anime_id)))
    conn.commit()
    conn.close()
def update_anime_status(anime_id, new_status):
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    c.execute("UPDATE anime SET status = ? WHERE id = ?", (new_status, str(anime_id)))
    conn.commit()
    conn.close()
def delete_anime_from_db(anime_id):
    conn = sqlite3.connect('anime.db')
    c = conn.cursor()
    c.execute("DELETE FROM anime WHERE id = ?", (str(anime_id),))
    conn.commit()
    conn.close()
def display_main_anime_grid(event=None):
    if my_list_panel.winfo_width() > 1:
        for widget in my_list_frame_content.winfo_children(): widget.destroy()
        search_query = my_list_search_entry.get().strip()
        status_filter = my_list_status_var.get()
        anime_data = get_all_anime(search_query, status_filter)
        panel_width = my_list_frame_content.winfo_width()
        card_width = 120 + 20
        num_columns = max(1, panel_width // card_width)
        for i, (anime_id, title, progress, status, episodes, image_url) in enumerate(anime_data):
            row = i // num_columns
            col = i % num_columns
            card_frame = customtkinter.CTkFrame(my_list_frame_content, width=120, height=200)
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
            status_color = STATUS_COLORS.get(status, "transparent")
            status_indicator = customtkinter.CTkFrame(card_frame, width=15, height=15, fg_color=status_color, bg_color="transparent", border_color="gray10", border_width=1, corner_radius=10)
            status_indicator.place(relx=1.0, rely=0.0, x=-5, y=5, anchor="ne")
            local_image_path = get_image_path(anime_id)
            if os.path.exists(local_image_path):
                try:
                    img = Image.open(local_image_path)
                    photo_image = customtkinter.CTkImage(light_image=img, dark_image=img, size=(100,150))
                    image_label = customtkinter.CTkLabel(card_frame, image=photo_image, text="")
                    image_label.pack(pady=(5, 0))
                except Exception:
                    image_label = customtkinter.CTkLabel(card_frame, text="Image\nFailed", width=100, height=150).pack(pady=(5,0))
            else:
                image_label = customtkinter.CTkLabel(card_frame, text="Image\nMissing", width=100, height=150).pack(pady=(5,0))
            title_text = f"{title}\n({progress}/{episodes if episodes else '?'})"
            title_label = customtkinter.CTkLabel(card_frame, text=title_text, font=("Arial", 10), wraplength=100)
            title_label.pack(pady=(0, 5), fill="x", expand=True)
            status_indicator.lift()
            card_frame.bind("<Button-1>", lambda event, id=anime_id: open_details_window(id, is_new_anime=False))
            for child in card_frame.winfo_children():
                if child is not status_indicator: child.bind("<Button-1>", lambda event, id=anime_id: open_details_window(id, is_new_anime=False))
def search_anime(event=None):
    global api_results
    api_results = []
    for widget in search_results_frame.winfo_children(): widget.destroy()
    search_query = search_entry_add.get().strip()
    if not search_query: return
    loading_label = customtkinter.CTkLabel(search_results_frame, text="Searching...", font=("Arial", 12))
    loading_label.pack(pady=20)
    root.update_idletasks()
    def do_search():
        try:
            variables = {'search': search_query}
            response = requests.post(ANILIST_API_URL, json={'query': ANILIST_SEARCH_QUERY, 'variables': variables})
            loading_label.destroy()
            if response.status_code == 200:
                data = response.json()
                results = data['data']['Page']['media']
                if not results:
                    customtkinter.CTkLabel(search_results_frame, text="No results found.").pack(pady=10)
                    return
                panel_width = search_results_frame.winfo_width()
                card_width = 120 + 20
                num_columns = max(1, panel_width // card_width)
                for i, anime in enumerate(results):
                    api_results.append(anime)
                    row = i // num_columns
                    col = i % num_columns
                    card_frame = customtkinter.CTkFrame(search_results_frame, width=120, height=200)
                    card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
                    image_url = anime['coverImage']['large']
                    placeholder = customtkinter.CTkLabel(card_frame, text="Loading...", width=100, height=150)
                    placeholder.pack(pady=(5,0))
                    threading.Thread(target=load_image_and_display_search, args=(card_frame, image_url, anime['title']['romaji'], len(api_results)-1, placeholder), daemon=True).start()
            else:
                customtkinter.CTkLabel(search_results_frame, text="Error fetching results.").pack(pady=10)
        except requests.exceptions.RequestException:
            loading_label.destroy()
            customtkinter.CTkLabel(search_results_frame, text="Network Error.").pack(pady=10)
    threading.Thread(target=do_search, daemon=True).start()
def load_image_and_display_search(parent_frame, image_url, title, index, placeholder_widget):
    try:
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            image_data = Image.open(io.BytesIO(image_response.content))
            photo_image = customtkinter.CTkImage(light_image=image_data, dark_image=image_data, size=(100, 150))
            def update_ui():
                placeholder_widget.destroy()
                display_image_on_card_search(parent_frame, photo_image, title, index)
            root.after(0, update_ui)
    except Exception as e:
        print(f"Failed to load image for {title}: {e}")
        root.after(0, lambda: placeholder_widget.configure(text="Image\nFailed"))
def display_image_on_card_search(parent_frame, photo_image, title, index):
    image_label = customtkinter.CTkLabel(parent_frame, image=photo_image, text="").pack(pady=(5, 0))
    title_label = customtkinter.CTkLabel(parent_frame, text=title, font=("Arial", 10), wraplength=100).pack(pady=(0, 5), fill="x", expand=True)
    parent_frame.bind("<Button-1>", lambda event: open_details_window(api_results[index], is_new_anime=True))
    for child in parent_frame.winfo_children(): child.bind("<Button-1>", lambda event: open_details_window(api_results[index], is_new_anime=True))
def delete_anime_from_main_list(anime_id, details_window_to_close):
    response = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this anime?")
    if response:
        delete_anime_from_db(anime_id)
        try: os.remove(get_image_path(anime_id))
        except FileNotFoundError: pass
        display_main_anime_grid()
        details_window_to_close.destroy()
        messagebox.showinfo("Deleted", "Anime has been deleted.")
def fetch_anime_details_from_api(anime_id):
    variables = {'id': anime_id}
    try:
        response = requests.post(ANILIST_API_URL, json={'query': ANILIST_DETAIL_QUERY, 'variables': variables})
        if response.status_code == 200: return response.json()['data']['Media']
    except requests.exceptions.RequestException as e: print(f"API request failed: {e}")
    return None
def open_details_window(anime_data, is_new_anime=False):
    anilist_id = anime_data['id'] if is_new_anime else anime_data
    details_window = customtkinter.CTkToplevel(root)
    details_window.geometry("800x600")
    details_window.title("Loading Anime Details...")
    details_window.grab_set()
    loading_label = customtkinter.CTkLabel(details_window, text="Fetching Details from AniList...", font=("Arial", 16))
    loading_label.pack(expand=True)
    def populate_window(api_data):
        loading_label.destroy()
        if not api_data:
            details_window.title("Error")
            customtkinter.CTkLabel(details_window, text="Failed to fetch anime details.").pack(expand=True)
            return
        details_window.title(f"Anime Page: {api_data['title']['romaji']}")
        main_frame = customtkinter.CTkFrame(details_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        left_frame = customtkinter.CTkFrame(main_frame, width=250, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(0, 10), sticky="ns")
        right_frame = customtkinter.CTkScrollableFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        def display_image(url):
            try:
                response = requests.get(url)
                img_data = Image.open(io.BytesIO(response.content))
                ctk_image = customtkinter.CTkImage(light_image=img_data, dark_image=img_data, size=(220, 310))
                customtkinter.CTkLabel(left_frame, image=ctk_image, text="").pack(pady=5)
            except Exception as e:
                print(f"Failed to load image: {e}")
                customtkinter.CTkLabel(left_frame, text="Image\nnot available").pack(pady=5)
        threading.Thread(target=display_image, args=(api_data['coverImage']['extraLarge'],), daemon=True).start()
        customtkinter.CTkLabel(right_frame, text=api_data['title']['romaji'], font=("Arial", 20, "bold"), wraplength=500).pack(anchor="w", pady=(0, 5))
        if api_data['title']['english']: customtkinter.CTkLabel(right_frame, text=api_data['title']['english'], font=("Arial", 14), wraplength=500).pack(anchor="w", pady=(0, 10))
        genres = ", ".join(api_data['genres'])
        customtkinter.CTkLabel(right_frame, text=f"Genres: {genres}", font=("Arial", 12, "italic"), wraplength=500).pack(anchor="w", pady=(0, 15))
        description = api_data['description'].replace('<br>', '\n') if api_data['description'] else "No description available."
        customtkinter.CTkLabel(right_frame, text="Description", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 2))
        customtkinter.CTkLabel(right_frame, text=description, wraplength=500, justify="left").pack(anchor="w", fill="x", pady=(0, 15))
        info_frame = customtkinter.CTkFrame(right_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=10)
        info_data = {"Premiere": f"{api_data.get('season', 'N/A')} {api_data.get('startDate', {}).get('year', '')}", "Episodes": api_data.get('episodes', 'N/A'), "Status": api_data.get('status', 'N/A').replace('_', ' ').title()}
        for i, (key, value) in enumerate(info_data.items()):
            customtkinter.CTkLabel(info_frame, text=f"{key}:", font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="w", padx=(0,10))
            customtkinter.CTkLabel(info_frame, text=value).grid(row=i, column=1, sticky="w")
        relations = [edge for edge in api_data['relations']['edges'] if edge['node']['type'] == 'ANIME']
        if relations:
            customtkinter.CTkLabel(right_frame, text="Related Media", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 5))
            relations_frame = customtkinter.CTkFrame(right_frame, fg_color="transparent")
            relations_frame.pack(fill="x")
            for i, edge in enumerate(relations):
                col = i % 4
                row = i // 4
                rel_card = customtkinter.CTkFrame(relations_frame, width=120, height=200)
                rel_card.grid(row=row, column=col, padx=5, pady=5, sticky="nw")
                rel_type = edge['relationType'].replace('_', ' ').title()
                placeholder = customtkinter.CTkLabel(rel_card, text="...", width=100, height=150)
                placeholder.pack(pady=5)
                customtkinter.CTkLabel(rel_card, text=rel_type, font=("Arial", 10, "bold")).pack(pady=(5,2))
                if edge['node']['coverImage'] and edge['node']['coverImage']['large']:
                    threading.Thread(target=load_relation_card_image, args=(rel_card, placeholder, edge['node'], details_window), daemon=True).start()
                else:
                    placeholder.configure(text="No Image")
        user_data = get_anime_data(anilist_id) if not is_new_anime else None
        initial_progress = user_data[1] if user_data else 0
        initial_status = user_data[2] if user_data else "Plan to Watch"
        edit_frame = customtkinter.CTkFrame(left_frame)
        edit_frame.pack(pady=20, fill="x", padx=5)
        customtkinter.CTkLabel(edit_frame, text="My Progress", font=("Arial", 14, "bold")).pack(pady=(0,10))
        current_progress_var = tk.StringVar(value=str(initial_progress))
        last_valid_progress = str(initial_progress)
        def validate_and_sanitize_progress(*args):
            nonlocal last_valid_progress
            value = current_progress_var.get()
            if value.isdigit():
                num_value = int(value)
                max_episodes = api_data.get('episodes')
                if max_episodes is not None and num_value > max_episodes:
                    current_progress_var.set(str(max_episodes))
                else:
                    last_valid_progress = value
            elif value != "":
                current_progress_var.set(last_valid_progress)
        current_progress_var.trace_add("write", validate_and_sanitize_progress)
        def increment_progress():
            try:
                val = int(current_progress_var.get())
                current_progress_var.set(str(val + 1))
            except ValueError:
                current_progress_var.set(last_valid_progress)
        def decrement_progress():
            try:
                val = int(current_progress_var.get())
                if val > 0: current_progress_var.set(str(val - 1))
            except ValueError:
                current_progress_var.set(last_valid_progress)
        progress_frame = customtkinter.CTkFrame(edit_frame, fg_color="transparent")
        progress_frame.pack()
        customtkinter.CTkButton(progress_frame, text="-", command=decrement_progress, width=30).pack(side=tk.LEFT, padx=5)
        progress_entry = customtkinter.CTkEntry(progress_frame, textvariable=current_progress_var, width=50, justify="center")
        progress_entry.pack(side=tk.LEFT, padx=5)
        customtkinter.CTkButton(progress_frame, text="+", command=increment_progress, width=30).pack(side=tk.LEFT, padx=5)
        current_status_var = customtkinter.StringVar(value=initial_status)
        status_options = ["Watching", "Completed", "Plan to Watch", "On Hold", "Dropped"]
        customtkinter.CTkOptionMenu(edit_frame, variable=current_status_var, values=status_options).pack(pady=10)
        def save_and_close():
            db_id = str(api_data['id'])
            db_title = api_data['title']['romaji']
            db_episodes = api_data['episodes']
            db_image_url = api_data['coverImage']['large']
            if not os.path.exists(get_image_path(db_id)): save_image_from_url(db_image_url, db_id)
            try: final_progress = int(current_progress_var.get())
            except ValueError: final_progress = int(last_valid_progress)
            add_anime_to_db(db_id, db_title, db_episodes, db_image_url, final_progress, current_status_var.get())
            display_main_anime_grid()
            details_window.destroy()
        save_button_text = "Save Changes" if not is_new_anime else "Add to My List"
        customtkinter.CTkButton(edit_frame, text=save_button_text, command=save_and_close).pack(pady=(10,0))
        if not is_new_anime:
            def delete_and_close(): delete_anime_from_main_list(str(anilist_id), details_window)
            customtkinter.CTkButton(edit_frame, text="Delete Anime", fg_color="red", hover_color="#8B0000", command=delete_and_close).pack(pady=10)
    def thread_target():
        api_data = fetch_anime_details_from_api(anilist_id)
        root.after(0, populate_window, api_data)
    threading.Thread(target=thread_target, daemon=True).start()
def load_relation_card_image(card, placeholder, node, parent_window):
    try:
        response = requests.get(node['coverImage']['large'])
        img_data = Image.open(io.BytesIO(response.content))
        ctk_image = customtkinter.CTkImage(light_image=img_data, dark_image=img_data, size=(100, 150))
        def update_card_ui():
            placeholder.destroy()
            image_label = customtkinter.CTkLabel(card, image=ctk_image, text="")
            image_label.pack(pady=5)
            customtkinter.CTkLabel(card, text=node['title']['romaji'], font=("Arial", 10), wraplength=100).pack(pady=2, fill="x")
            def open_new_page(event, anime_id):
                parent_window.destroy()
                open_details_window(anime_id, is_new_anime=False)
            card.bind("<Button-1>", lambda e, id=node['id']: open_new_page(e, id))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, id=node['id']: open_new_page(e, id))
        root.after(0, update_card_ui)
    except Exception as e:
        root.after(0, lambda: placeholder.configure(text="No Image"))
        print(f"Failed to load relation image: {e}")
def update_button_position(panel_width): toggle_button.place(x=panel_width + (sash_width // 2), rely=0.5, anchor="center")
def toggle_search_panel():
    global search_panel_last_width
    current_width = search_panel.winfo_width()
    if current_width > 1:
        search_panel_last_width = current_width
        search_panel.configure(width=0)
        toggle_button.configure(text="▶")
        update_button_position(0)
    else:
        search_panel.configure(width=search_panel_last_width)
        toggle_button.configure(text="◀")
        update_button_position(search_panel_last_width)
    root.after(50, display_main_anime_grid)

# --- UI Setup ---
customtkinter.set_appearance_mode("Dark")
root = customtkinter.CTk()
root.title("My Anime Tracker")
root.state('zoomed')
main_content_frame = customtkinter.CTkFrame(root, corner_radius=0, fg_color="transparent")
main_content_frame.pack(fill="both", expand=True)
search_panel = customtkinter.CTkFrame(main_content_frame, width=search_panel_last_width, corner_radius=0)
search_panel.pack(side="left", fill="y")
search_panel.pack_propagate(False)
class Sash(customtkinter.CTkFrame):
    def __init__(self, parent, target_widget):
        super().__init__(parent, width=sash_width, cursor="sb_h_double_arrow", fg_color="gray25")
        self.target = target_widget
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
    def on_drag(self, event):
        global search_panel_last_width
        new_width = event.x_root - main_content_frame.winfo_rootx()
        if 50 < new_width < 800:
            self.target.configure(width=new_width)
            search_panel_last_width = new_width
            update_button_position(new_width)
    def on_release(self, event): display_main_anime_grid()
sash = Sash(main_content_frame, search_panel)
sash.pack(side="left", fill="y")
toggle_button = customtkinter.CTkButton(main_content_frame, text="◀", command=toggle_search_panel, width=20, height=40, corner_radius=8, fg_color="transparent", text_color="white", anchor="center")
update_button_position(search_panel_last_width)
my_list_panel = customtkinter.CTkFrame(main_content_frame, corner_radius=0, fg_color="transparent")
my_list_panel.pack(side="left", fill="both", expand=True)

# --- MODIFIED: Filter Section ---
my_list_filter_frame = customtkinter.CTkFrame(my_list_panel, fg_color="transparent")
my_list_filter_frame.pack(pady=10, padx=10, fill="x")

customtkinter.CTkLabel(my_list_filter_frame, text="Search My List:").pack(side=tk.LEFT, padx=(0, 5))
my_list_search_entry = customtkinter.CTkEntry(my_list_filter_frame, width=200)
my_list_search_entry.pack(side=tk.LEFT, padx=(0, 20))
my_list_search_entry.bind('<KeyRelease>', display_main_anime_grid)

my_list_status_var = customtkinter.StringVar(value="All")
status_options = ["All", "Watching", "Completed", "Plan to Watch", "On Hold", "Dropped"]
status_buttons = {}

def filter_by_status(status):
    my_list_status_var.set(status)
    display_main_anime_grid()
    # Update button appearance to show active state
    for s, btn in status_buttons.items():
        if s == status:
            btn.configure(border_width=2)
        else:
            btn.configure(border_width=0)

status_button_frame = customtkinter.CTkFrame(my_list_filter_frame, fg_color="transparent")
status_button_frame.pack(side=tk.LEFT, padx=10)

for status in status_options:
    color = STATUS_COLORS.get(status, "#565b5e") # Default customtkinter button color for "All"
    
    button = customtkinter.CTkButton(status_button_frame, text=status,
                                     fg_color=color,
                                     border_color="#00AFFF", # A bright blue to indicate selection
                                     border_width=0, # Initially not selected
                                     command=lambda s=status: filter_by_status(s))
    button.pack(side=tk.LEFT, padx=4)
    status_buttons[status] = button

# --- END MODIFIED Filter Section ---

my_list_frame_content = customtkinter.CTkScrollableFrame(my_list_panel, fg_color="transparent")
my_list_frame_content.pack(pady=10, padx=10, fill="both", expand=True)

# --- Initial setup ---
search_bix_frame = customtkinter.CTkFrame(search_panel, fg_color="transparent")
search_bix_frame.pack(pady=10, padx=10, fill="x")
customtkinter.CTkLabel(search_bix_frame, text="Search Anime").pack(anchor="w")
search_entry_add = customtkinter.CTkEntry(search_bix_frame, placeholder_text="Search...")
search_entry_add.pack(fill="x", pady=(0, 5))
search_entry_add.bind('<Return>', search_anime)
search_button = customtkinter.CTkButton(search_bix_frame, text="Search", command=search_anime)
search_button.pack()
search_results_frame = customtkinter.CTkScrollableFrame(search_panel, fg_color="gray17")
search_results_frame.pack(pady=10, padx=10, fill="both", expand=True)

setup_database()
filter_by_status("All") # Set the initial filter to "All" and highlight the button
root.after(100, display_main_anime_grid)
root.mainloop()