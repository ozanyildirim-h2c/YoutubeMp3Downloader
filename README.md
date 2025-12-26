# 🎵 YouTube to MP3 Converter (Link & Search)

A smart, thread-safe, and GUI-based YouTube to MP3 downloader written in Python. You can paste **direct links** OR type **video names** to search and download automatically.


## 🚀 Features
* **Dual Mode Input:**
    * Paste YouTube links (e.g., `https://youtube.com/...`) -> Downloads directly.
    * Type search terms (e.g., `Tarkan Yolla`) -> Finds the best match and downloads.
* **Batch Processing:** Import mixed inputs (links & names) from a `.txt` file or paste manually.
* **Clean UI:** Built with `tkinter`, featuring a progress bar, log window, and non-freezing thread architecture.
* **Smart Conversion:** Automatically grabs the best audio stream, converts to MP3 using `ffmpeg`, and cleans up temp files.
* **Duplicate Check:** Skips files if they already exist.

## 🛠️ Installation & Usage (Source Code)

1.  **Clone the repo**
    ```bash
    git clone [https://github.com/ozanyildirim-h2c/YoutubeMp3Downloader.git](https://github.com/ozanyildirim-h2c/YoutubeMp3Downloader.git)
    cd YoutubeMp3Downloader
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App**
    ```bash
    python app.py
    ```

4.  **How to Use**
    * Select an Output Folder.
    * In the text box, you can mix links and names:
        ```text
        [https://www.youtube.com/watch?v=dQw4w9WgXcQ](https://www.youtube.com/watch?v=dQw4w9WgXcQ)
        Michael Jackson Billie Jean
        [https://youtu.be/xyz123](https://youtu.be/xyz123)
        Coldplay Yellow
        ```
    * Click **Start**.

## 📦 Build EXE
To create a standalone executable:
```bash
pyinstaller --noconsole --onefile --name "YoutubeMp3Converter" App.py
