import os
import re
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pytubefix import YouTube, Search  # Search modülü eklendi

# --- Configuration & Constants ---
APP_TITLE = "YouTube to MP3 Converter (Link & Search)"
APP_GEOMETRY = "750x600"
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
    Supports both direct links and search queries.
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
            text="Paste YouTube links OR type video names (one per line):", 
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
        """Reads content from a text file."""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_input_area.insert(tk.END, content + "\n")
                self._log_message(f"File loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def _extract_inputs(self):
        """
        Parses the input area line by line.
        Returns a list of non-empty strings (URLs or Search Terms).
        """
        raw_text = self.text_input_area.get("1.0", tk.END)
        # Split by lines and remove empty ones
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        # Remove duplicates while preserving order
        return list(dict.fromkeys(lines))

    def _start_background_process(self):
        """Validates inputs and starts the processing thread."""
        if self.is_processing:
            return
        
        target_dir = self.output_directory_var.get()
        if not target_dir:
            messagebox.showwarning("Warning", "Please select an output folder first.")
            return

        inputs = self._extract_inputs()
        if not inputs:
            messagebox.showwarning("Warning", "Please enter links or video names.")
            return

        # Lock UI and Start Thread
        self.is_processing = True
        self.btn_start.config(state="disabled")
        threading.Thread(
            target=self._process_queue, 
            args=(inputs, target_dir), 
            daemon=True
        ).start()

    # --- Core Business Logic ---

    def _process_queue(self, inputs, output_dir):
        """
        Iterates through the list of inputs (URL or Search Term).
        Running in a separate thread.
        """
        total_count = len(inputs)
        self.progress_bar["maximum"] = total_count
        self.progress_bar["value"] = 0
        
        self._log_message(f"--- Started: Processing {total_count} items ---")

        for index, item in enumerate(inputs, 1):
            self._process_single_item(item, index, total_count, output_dir)
            
            # Update Progress
            self.progress_bar["value"] = index

        # Finalize
        self.lbl_status.config(text="All tasks completed.")
        self._log_message("--- FINISHED ---")
        messagebox.showinfo("Success", "Download and conversion completed successfully.")
        
        self.is_processing = False
        self.btn_start.config(state="normal")

    def _resolve_url(self, item, index, total):
        """
        Determines if the item is a URL or a Search Term.
        If Search Term, searches YouTube and returns the first video URL.
        """
        # Basic check: if it starts with http, assume it's a link
        if item.lower().startswith("http"):
            return item
        
        # Otherwise, treat as search query
        self.lbl_status.config(text=f"Searching ({index}/{total}): '{item}'...")
        self._log_message(f"Searching YouTube for: '{item}'")
        
        try:
            s = Search(item)
            if s.results:
                video_url = s.results[0].watch_url
                self._log_message(f"Found: {s.results[0].title}")
                return video_url
            else:
                self._log_message(f"WARNING: No results found for '{item}'")
                return None
        except Exception as e:
            self._log_message(f"SEARCH ERROR: {e}")
            return None

    def _process_single_item(self, item, index, total, output_dir):
        """
        Handles the logic for a single input item (Resolve -> Download -> Convert).
        """
        try:
            # Step 1: Resolve URL (Link or Search)
            url = self._resolve_url(item, index, total)
            if not url:
                return # Skip if search failed

            self.lbl_status.config(text=f"Processing ({index}/{total}): Getting info...")
            
            # Step 2: Initialize YouTube Object
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

            # Step 3: Download
            self.lbl_status.config(text=f"Downloading ({index}/{total}): {safe_title}")
            self._log_message(f"Downloading: {safe_title}...")
            audio_stream.download(output_path=output_dir, filename=mp4_filename)

            # Step 4: Convert (FFmpeg)
            self.lbl_status.config(text=f"Converting ({index}/{total}): {safe_title}")
            
            ffmpeg_cmd = [
                FFMPEG_EXECUTABLE, "-i", mp4_full_path, 
                "-vn",                 # No video
                "-acodec", "libmp3lame", 
                "-q:a", "2",           # High quality
                "-y",                  # Overwrite
                "-loglevel", "error",  # Quiet
                mp3_full_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True)
            
            # Step 5: Cleanup
            if os.path.exists(mp4_full_path):
                os.remove(mp4_full_path)
            
            self._log_message(f"COMPLETED: {mp3_filename}")

        except Exception as e:
            self._log_message(f"ERROR ({item}): {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeToMp3App(root)
    root.mainloop()