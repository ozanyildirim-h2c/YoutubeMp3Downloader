# 🎵 YouTube to MP3 Converter

A simple, thread-safe, and GUI-based YouTube to MP3 downloader and converter written in Python. It downloads videos using `pytubefix` and converts them to MP3 using `ffmpeg`.


## 🚀 Features
* **Batch Processing:** Import links from a `.txt` file or paste them manually.
* **Clean UI:** Built with `tkinter`, featuring a progress bar and log window.
* **Smart Conversion:** Automatically downloads the best audio stream and converts it to MP3.
* **Duplicate Check:** Skips files if they already exist.
* **Standalone EXE:** Can be used without installing Python (see Releases).

## 🛠️ Installation & Usage (Source Code)

1.  **Clone the repo**
    ```bash
    git clone [https://github.com/KULLANICI_ADINIZ/YoutubeMp3Converter.git](https://github.com/KULLANICI_ADINIZ/YoutubeMp3Converter.git)
    cd YoutubeMp3Converter
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App**
    ```bash
    python app.py
    ```

## 📦 How to Build EXE
If you want to build the executable yourself:
```bash
pyinstaller --noconsole --onefile --name "YoutubeMp3Converter" App.py
