import os
import re
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pytubefix import YouTube

# --- Configuration & Constants ---
APP_TITLE = "YouTube to MP3 Converter"
APP_GEOMETRY = "720x600"
COLOR_PRIMARY = "#4CAF50"  # Green
COLOR_TEXT_LOG = "Consolas 9"
DEFAULT_PADDING = 10

# Attempt to locate FFmpeg executable
try:
    import imageio_ffmpeg
    FFMPEG_EXECUTABLE = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_EXECUTABLE = "ffmpeg"


class YoutubeToMp3App:
    """
    Main application class for downloading YouTube videos and converting them to MP3.
    Handles the GUI and background processing threads.
    """

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)

        # Reactive Variables
        self.output_directory_var = tk.StringVar()
        self.is_processing = False

        # Initialize User Interface
        self._init_ui()

    def _init_ui(self):
        """Orchestrates the creation of all UI components."""
        self._setup_input_area()
        self._setup_output_area()
        self._setup_control_area()
        self._setup_logging_area()

    def _setup_input_area(self):
        """Creates the input text area and file import button."""
        lbl_instruction = tk.Label(
            self.root, 
            text="Paste YouTube links below or import from a file:", 
            font=("Arial", 10, "bold")
        )
        lbl_instruction.pack(pady=(10, 5))

        self.text_input_area = scrolledtext.ScrolledText(self.root, height=10, width=85)
        self.text_input_area.pack(padx=DEFAULT_PADDING, pady=5)

        btn_import = tk.Button(
            self.root, 
            text="Import from .TXT File", 
            command=self._import_links_from_file
        )
        btn_import.pack(pady=5)

    def _setup_output_area(self):
        """Creates the directory selection area."""
        frame_output = tk.Frame(self.root)
        frame_output.pack(pady=10, fill="x", padx=DEFAULT_PADDING)

        lbl_path = tk.Label(frame_output, text="Output Folder:")
        lbl_path.pack(side="left")

        entry_path = tk.Entry(
            frame_output, 
            textvariable=self.output_directory_var, 
            width=55
        )
        entry_path.pack(side="left", padx=5)

        btn_browse = tk.Button(
            frame_output, 
            text="Browse...", 
            command=self._browse_directory
        )
        btn_browse.pack(side="left")

    def _setup_control_area(self):
        """Creates the start button and progress bar."""
        self.btn_start = tk.Button(
            self.root, 
            text="Start Download & Conversion", 
            command=self._start_background_process, 
            bg=COLOR_PRIMARY, 
            fg="white", 
            font=("Arial", 11, "bold"), 
            height=2
        )
        self.btn_start.pack(pady=10, fill="x", padx=60)

        self.progress_bar = ttk.Progressbar(
            self.root, 
            orient="horizontal", 
            length=100, 
            mode="determinate"
        )
        self.progress_bar.pack(pady=5, fill="x", padx=20)

        self.lbl_status = tk.Label(self.root, text="Ready", fg="blue")
        self.lbl_status.pack(pady=5)

    def _setup_logging_area(self):
        """Creates the log output area."""
        lbl_logs = tk.Label(self.root, text="Process Logs:", font=("Arial", 9, "bold"))
        lbl_logs.pack(pady=(5, 0))

        self.text_log_area = scrolledtext.ScrolledText(
            self.root, 
            height=8, 
            width=85, 
            state='disabled', 
            font=COLOR_TEXT_LOG
        )
        self.text_log_area.pack(padx=DEFAULT_PADDING, pady=5)

    # --- Helper Methods (UI & Logic) ---

    def _log_message(self, message):
        """Thread-safe logging to the text area."""
        self.text_log_area.config(state='normal')
        self.text_log_area.insert(tk.END, message + "\n")
        self.text_log_area.see(tk.END)
        self.text_log_area.config(state='disabled')

    def _browse_directory(self):
        """Opens a dialog to select the output directory."""
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.output_directory_var.set(selected_folder)

    def _import_links_from_file(self):
        """Reads links from a text file and populates the input area."""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_input_area.insert(tk.END, content + "\n")
                self._log_message(f"File loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def _extract_unique_links(self):
        """Parses the input area for valid YouTube URLs."""
        raw_text = self.text_input_area.get("1.0", tk.END)
        # Regex for standard and shortened YouTube links
        pattern = r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+)'
        return list(set(re.findall(pattern, raw_text))) # Use set to remove duplicates

    def _start_background_process(self):
        """Validates inputs and starts the processing thread."""
        if self.is_processing:
            return
        
        target_dir = self.output_directory_var.get()
        if not target_dir:
            messagebox.showwarning("Warning", "Please select an output folder first.")
            return

        links = self._extract_unique_links()
        if not links:
            messagebox.showwarning("Warning", "No valid YouTube links found.")
            return

        # Lock UI and Start Thread
        self.is_processing = True
        self.btn_start.config(state="disabled")
        threading.Thread(
            target=self._process_queue, 
            args=(links, target_dir), 
            daemon=True
        ).start()

    # --- Core Business Logic ---

    def _process_queue(self, links, output_dir):
        """
        Iterates through the list of links and processes them one by one.
        Running in a separate thread.
        """
        total_count = len(links)
        self.progress_bar["maximum"] = total_count
        self.progress_bar["value"] = 0
        
        self._log_message(f"--- Started: Processing {total_count} videos ---")

        for index, url in enumerate(links, 1):
            self._process_single_video(url, index, total_count, output_dir)
            
            # Update Progress
            self.progress_bar["value"] = index

        # Finalize
        self.lbl_status.config(text="All tasks completed.")
        self._log_message("--- FINISHED ---")
        messagebox.showinfo("Success", "Download and conversion completed successfully.")
        
        self.is_processing = False
        self.btn_start.config(state="normal")

    def _process_single_video(self, url, index, total, output_dir):
        """
        Handles the download and conversion logic for a single video.
        Steps: 1. Get Info -> 2. Download MP4 -> 3. Convert to MP3 -> 4. Cleanup
        """
        try:
            self.lbl_status.config(text=f"Processing ({index}/{total}): Analyzing link...")
            
            # 1. Initialize YouTube Object
            yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
            
            # Get best audio stream
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not audio_stream:
                self._log_message(f"ERROR: No audio stream found for {url}")
                return

            # Sanitize filename
            safe_title = re.sub(r'[\\/*?:"<>|]', "", yt.title)
            base_filename = f"{index}- {safe_title}"
            mp4_filename = f"{base_filename}.mp4"
            mp3_filename = f"{base_filename}.mp3"
            
            mp4_full_path = os.path.join(output_dir, mp4_filename)
            mp3_full_path = os.path.join(output_dir, mp3_filename)

            # Skip if already exists
            if os.path.exists(mp3_full_path):
                self._log_message(f"SKIPPED (Exists): {mp3_filename}")
                return

            # 2. Download
            self.lbl_status.config(text=f"Downloading ({index}/{total}): {safe_title}")
            self._log_message(f"Downloading: {safe_title}...")
            audio_stream.download(output_path=output_dir, filename=mp4_filename)

            # 3. Convert (FFmpeg)
            self.lbl_status.config(text=f"Converting ({index}/{total}): {safe_title}")
            
            ffmpeg_cmd = [
                FFMPEG_EXECUTABLE, "-i", mp4_full_path, 
                "-vn",                 # No video
                "-acodec", "libmp3lame", 
                "-q:a", "2",           # High quality variable bitrate
                "-y",                  # Overwrite without asking
                "-loglevel", "error",  # Suppress logs
                mp3_full_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True)
            
            # 4. Cleanup
            if os.path.exists(mp4_full_path):
                os.remove(mp4_full_path)
            
            self._log_message(f"COMPLETED: {mp3_filename}")

        except Exception as e:
            self._log_message(f"ERROR ({url}): {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeToMp3App(root)
    root.mainloop()