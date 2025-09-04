# Fetish Tracker

![App Screenshot](https://github.com/ak47monky/Fetish-Tracker/blob/main/Screenshot.png?raw=true)

A sleek, modern desktop application for tracking your anime collection, built from the ground up with Python, CustomTkinter, and the AniList GraphQL API.

This app allows you to search for any anime, add it to your personal library, track your watch status and episode progress, and browse detailed information and related media in a rich, visual interface.

## Core Features

* **Modern & Responsive UI:** Built with CustomTkinter for a clean, dark-mode-native look and feel.
* **Resizable Layout:** Features a collapsible search panel and a draggable sash to resize panes dynamically.
* **Powerful API Integration:** Search for any anime using the official **AniList API (GraphQL)**.
* **Persistent Local Database:** Your library is saved locally using **SQLite3**.
* **Full Anime Page:** Click any anime to open a detailed page with:
    * Full description, genres, premiere date, and episode count.
    * A grid of clickable cards for all related media (sequels, prequels, side stories, etc.).
* **Visual Status Tracking:** Cards in your library are marked with colored icons (Watching, Completed, etc.) for an at-a-glance overview.
* **Flexible Progress Editor:** Track episodes using `+` and `-` buttons or by typing the number directly into an entry box.
* **Local Image Caching:** All anime images are downloaded once and cached locally for instant load times.

## Setup & Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/YourUsername/Fetish-Tracker.git](https://github.com/YourUsername/Fetish-Tracker.git)
    cd Fetish-Tracker
    ```

2.  **Create a virtual environment (recommended):**
    ```sh
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    (First, create the `requirements.txt` file from the section below and save it in your project folder.)
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    The app will start and automatically create the `anime.db` database file and `images/` folder in the project directory.
    ```sh
    python Fetish_Tracker.py
    ```

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for full details.
