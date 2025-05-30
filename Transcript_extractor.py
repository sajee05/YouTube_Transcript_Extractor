import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import re
from urllib.parse import urlparse, parse_qs
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound # MODIFIED_LINE
from youtube_transcript_api.formatters import TextFormatter
import time

class YouTubeTranscriptExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Playlist Transcript Extractor")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.output_dir = tk.StringVar()
        self.playlist_url = tk.StringVar()
        self.videos = []
        self.video_vars = []
        self.is_fetching = False
        
        self.setup_gui()
        
    def setup_gui(self):
        """Set up the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Output directory section
        ttk.Label(main_frame, text="Output Directory:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir, width=60)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(
            row=0, column=1)
        
        # Playlist URL section
        ttk.Label(main_frame, text="YouTube Playlist URL:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, textvariable=self.playlist_url, width=60)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(url_frame, text="Load Playlist", command=self.load_playlist).grid(
            row=0, column=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(0, 15))
        
        # Videos list section
        ttk.Label(main_frame, text="Videos in Playlist:", font=('Arial', 10, 'bold')).grid(
            row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        # Frame for videos list with scrollbar
        videos_frame = ttk.Frame(main_frame)
        videos_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        videos_frame.columnconfigure(0, weight=1)
        videos_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # Create scrollable text widget for videos
        self.videos_text = scrolledtext.ScrolledText(
            videos_frame, height=15, width=80, wrap=tk.WORD)
        self.videos_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=8, column=0, columnspan=3, pady=(10, 0))
        
        self.fetch_all_btn = ttk.Button(
            buttons_frame, text="Fetch All Transcripts", command=self.fetch_all_transcripts)
        self.fetch_all_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.fetch_selected_btn = ttk.Button(
            buttons_frame, text="Fetch Selected Transcripts", command=self.fetch_selected_transcripts)
        self.fetch_selected_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Select/Deselect all buttons
        select_frame = ttk.Frame(main_frame)
        select_frame.grid(row=9, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(select_frame, text="Select All", command=self.select_all).grid(
            row=0, column=0, padx=(0, 10))
        ttk.Button(select_frame, text="Deselect All", command=self.deselect_all).grid(
            row=0, column=1, padx=(10, 0))

    def browse_directory(self):
        """Open file dialog to select output directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def extract_playlist_id(self, url):
        """Extract playlist ID from YouTube URL"""
        try:
            print(f"[DEBUG] extract_playlist_id: Received URL: {url}") # ADDED_LINE
            parsed_url = urlparse(url)
            print(f"[DEBUG] extract_playlist_id: Parsed netloc: {parsed_url.netloc}") # ADDED_LINE
            playlist_id_to_return = None # ADDED_LINE
            if 'youtube.com' in parsed_url.netloc:
                query_params = parse_qs(parsed_url.query)
                if 'list' in query_params:
                    playlist_id_to_return = query_params['list'][0] # MODIFIED_LINE
            elif 'youtu.be' in parsed_url.netloc:
                # Handle youtu.be links with playlist parameter
                query_params = parse_qs(parsed_url.query)
                if 'list' in query_params:
                    playlist_id_to_return = query_params['list'][0] # MODIFIED_LINE
            print(f"[DEBUG] extract_playlist_id: Extracted ID: {playlist_id_to_return}") # ADDED_LINE
            return playlist_id_to_return # MODIFIED_LINE
        except Exception as e:
            print(f"Error extracting playlist ID: {e}")
            print(f"[DEBUG] extract_playlist_id: Extracted ID (on error): None") # ADDED_LINE
            return None

    def sanitize_filename(self, filename):
        """Remove or replace invalid characters for filenames"""
        # Remove invalid characters for Windows filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and limit length
        filename = re.sub(r'\s+', ' ', filename.strip())
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename

    def update_status(self, message, color="black"):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_var.set(value)
        self.root.update_idletasks()

    def load_playlist(self):
        """Load videos from YouTube playlist"""
        if not self.playlist_url.get().strip():
            messagebox.showerror("Error", "Please enter a YouTube playlist URL")
            return
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=self._load_playlist_thread, daemon=True).start()

    def _load_playlist_thread(self):
        """Thread function to load playlist"""
        try:
            current_url = self.playlist_url.get() # ADDED_LINE
            print(f"[DEBUG] _load_playlist_thread: Loading URL: {current_url}") # ADDED_LINE
            self.update_status("Loading playlist...", "blue")
            self.update_progress(10)
            
            playlist_id = self.extract_playlist_id(current_url) # MODIFIED_LINE
            print(f"[DEBUG] _load_playlist_thread: Playlist ID from extract_playlist_id: {playlist_id}") # ADDED_LINE
            if not playlist_id:
                self.update_status("Invalid playlist URL", "red")
                return
            
            # Configure yt-dlp options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlist_items': '1-1000',  # Limit to prevent excessive loading
            }
            
            self.update_progress(30)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(
                    f'https://www.youtube.com/playlist?list={playlist_id}', 
                    download=False
                )
            
            self.update_progress(60)
            
            if not playlist_info or 'entries' not in playlist_info:
                self.update_status("No videos found in playlist", "red")
                return
            
            # Clear previous videos
            self.videos = []
            self.video_vars = []
            
            # Process videos
            for entry in playlist_info['entries']:
                if entry:  # Some entries might be None for private/deleted videos
                    video_info = {
                        'id': entry.get('id', ''),
                        'title': entry.get('title', 'Unknown Title'),
                        'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}")
                    }
                    self.videos.append(video_info)
                    self.video_vars.append(tk.BooleanVar(value=True))
            
            self.update_progress(80)
            
            # Update GUI with video list
            self.display_videos()
            
            self.update_progress(100)
            self.update_status(f"Loaded {len(self.videos)} videos from playlist", "green")
            
            # Reset progress bar after a delay
            self.root.after(2000, lambda: self.update_progress(0))
            
        except Exception as e:
            self.update_status(f"Error loading playlist: {str(e)}", "red")
            self.update_progress(0)

    def display_videos(self):
        """Display videos list with checkboxes"""
        self.videos_text.config(state=tk.NORMAL)  # Enable editing to insert widgets
        self.videos_text.delete(1.0, tk.END)
        
        if not self.videos:
            self.videos_text.insert(tk.END, "No videos loaded. Please load a playlist first.")
            self.videos_text.config(state=tk.DISABLED) # Disable after modification
            return
        
        self.videos_text.insert(tk.END, f"Found {len(self.videos)} videos in playlist:\n\n")
        
        for i, video in enumerate(self.videos):
            if i < len(self.video_vars):
                var = self.video_vars[i]
                # Create Checkbutton with the video title
                # Ensure the title is not excessively long for display in the checkbutton
                display_title = video['title']
                if len(display_title) > 70: # Truncate if too long
                    display_title = display_title[:67] + "..."

                cb = ttk.Checkbutton(self.videos_text, text=f"{i+1:3}. {display_title}", variable=var)
                
                # Embed Checkbutton in ScrolledText
                self.videos_text.window_create(tk.END, window=cb)
                self.videos_text.insert(tk.END, "\n")  # Add a newline after each checkbutton
            else:
                # Fallback for safety, though this shouldn't happen with correct logic
                self.videos_text.insert(tk.END, f"{i+1:3}. {video['title']} (Error: Selection state unavailable)\n")
        
        self.videos_text.insert(tk.END, "\n\nNote: All videos are selected by default. Use 'Select All' or 'Deselect All' buttons to manage selection.")
        self.videos_text.config(state=tk.DISABLED)  # Disable editing after inserting widgets

    def select_all(self):
        """Select all videos"""
        for var in self.video_vars:
            var.set(True)
        self.update_status("All videos selected", "green")

    def deselect_all(self):
        """Deselect all videos"""
        for var in self.video_vars:
            var.set(False)
        self.update_status("All videos deselected", "orange")

    def fetch_all_transcripts(self):
        """Fetch transcripts for all videos"""
        if not self.videos:
            messagebox.showerror("Error", "Please load a playlist first")
            return
        
        # Select all videos
        self.select_all()
        self._fetch_transcripts()

    def fetch_selected_transcripts(self):
        """Fetch transcripts for selected videos only"""
        if not self.videos:
            messagebox.showerror("Error", "Please load a playlist first")
            return
        
        selected_count = sum(1 for var in self.video_vars if var.get())
        if selected_count == 0:
            messagebox.showwarning("Warning", "No videos selected. Please select at least one video.")
            return
        
        self._fetch_transcripts()

    def _fetch_transcripts(self):
        """Start transcript fetching in separate thread"""
        if self.is_fetching:
            messagebox.showwarning("Warning", "Already fetching transcripts. Please wait.")
            return
        
        if not self.output_dir.get().strip():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        if not os.path.exists(self.output_dir.get()):
            messagebox.showerror("Error", "Selected output directory does not exist")
            return
        
        threading.Thread(target=self._fetch_transcripts_thread, daemon=True).start()

    def _fetch_transcripts_thread(self):
        """Thread function to fetch transcripts"""
        self.is_fetching = True
        
        try:
            # Get selected videos
            selected_videos = [
                video for i, video in enumerate(self.videos) 
                if i < len(self.video_vars) and self.video_vars[i].get()
            ]
            
            total_videos = len(selected_videos)
            successful_downloads = 0
            failed_downloads_count = 0 # Renamed for clarity
            failed_video_details = [] # To store (serial_num, title) of failed videos
            
            self.update_status(f"Fetching transcripts for {total_videos} videos...", "blue")
            
            for i, video in enumerate(selected_videos):
                video_serial_number = i + 1 # 1-based serial number for display
                transcript_fetched_successfully = False
                last_exception = None

                for attempt in range(1, 4): # Max 3 attempts
                    try:
                        progress = (video_serial_number / total_videos) * 100
                        self.update_progress(progress)
                        status_message = f"Processing ({video_serial_number}/{total_videos}): {video['title'][:40]}..."
                        if attempt > 1:
                            status_message += f" (Attempt {attempt})"
                        self.update_status(status_message, "blue")

                        # Log available transcripts for diagnostics
                        print(f"[DIAGNOSTIC] Processing video ID: {video['id']}, Title: {video['title']}")
                        try:
                            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video['id'])
                            print(f"[DIAGNOSTIC] Available transcripts for {video['id']}:")
                            found_any = False
                            for ts in transcript_list_obj:
                                found_any = True
                                print(f"  - Language: {ts.language}, Code: {ts.language_code}, Generated: {ts.is_generated}, Translatable: {ts.is_translatable}")
                                if ts.is_translatable:
                                    translation_codes = [t_lang.language_code for t_lang in ts.translation_languages] # MODIFIED_LINE
                                    print(f"    Can be translated to: {translation_codes}")
                            if not found_any:
                                print("      None found by list_transcripts.")
                        except Exception as log_e:
                            print(f"[DIAGNOSTIC] Error listing transcripts for {video['id']}: {log_e}")
                        
                        # Get transcript (original problematic line)
                        # --- MODIFICATION START ---
                        # Try to get Hindi, then English, then any available transcript
                        transcript_data_to_format = None
                        fetched_lang_code = "N/A"

                        try:
                            available_transcripts_obj = YouTubeTranscriptApi.list_transcripts(video['id'])
                            
                            preferred_langs = ['hi', 'en']
                            found_preferred = False

                            for lang in preferred_langs:
                                try:
                                    # find_transcript searches both manual and generated
                                    target_transcript = available_transcripts_obj.find_transcript([lang])
                                    transcript_data_to_format = target_transcript.fetch()
                                    fetched_lang_code = target_transcript.language_code
                                    print(f"[INFO] Fetched '{fetched_lang_code}' transcript for {video['title']}.")
                                    found_preferred = True
                                    break # Found a preferred transcript
                                except NoTranscriptFound: # MODIFIED_LINE
                                    print(f"[INFO] No '{lang}' transcript found for {video['title']}. Trying next preferred.")
                                    continue # Try next preferred language
                            
                            if not found_preferred:
                                print(f"[INFO] No preferred transcript (hi, en) found for {video['title']}. Trying first available.")
                                # Convert iterator to list to safely access first element if it exists
                                all_available_list = list(available_transcripts_obj)
                                if all_available_list:
                                    first_available_transcript = all_available_list[0]
                                    transcript_data_to_format = first_available_transcript.fetch()
                                    fetched_lang_code = first_available_transcript.language_code
                                    print(f"[INFO] Fetched first available transcript '{fetched_lang_code}' for {video['title']}.")
                                else:
                                    # No transcripts at all were listed
                                    print(f"[WARN] No transcripts listed by API for {video['title']}.")
                                    raise NoTranscriptFound(video['id'], video['title'], "No transcripts found after checking preferred and available.") # MODIFIED_LINE

                            if transcript_data_to_format is None:
                                # This case implies no transcripts were found by any method.
                                print(f"[ERROR] transcript_data_to_format is None for {video['title']} after all checks.")
                                raise NoTranscriptFound(video['id'], video['title'], "No transcript data could be fetched.") # MODIFIED_LINE

                        except Exception as e_fetch_custom:
                            # This catch block is for errors during the custom fetching logic itself
                            # (e.g., list_transcripts fails, or NoTranscriptFound was raised by our logic).
                            # We want the outer retry loop to handle this.
                            print(f"[WARN] Custom transcript fetch failed for {video['title']} (attempt {attempt}): {e_fetch_custom}")
                            raise e_fetch_custom # Re-raise to be caught by the main retry loop for this video

                        # The variable 'transcript_list' is expected by the formatter
                        transcript_list = transcript_data_to_format
                        # --- MODIFICATION END ---
                        
                        # Format transcript with timestamps
                        # This line now uses the 'transcript_list' populated by the new logic
                        formatted_transcript = self.format_transcript_with_timestamps(
                            transcript_list, video['title']
                        )
                        
                        # Save to file
                        filename = self.sanitize_filename(video['title']) + '.md'
                        filepath = os.path.join(self.output_dir.get(), filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(formatted_transcript)
                        
                        successful_downloads += 1
                        transcript_fetched_successfully = True
                        break # Exit retry loop on success
                        
                    except Exception as e:
                        last_exception = e
                        print(f"Attempt {attempt} failed for {video['title']}: {e}")
                        if attempt < 3:
                            self.update_status(f"Retrying {video['title'][:40]}... (Attempt {attempt+1})", "orange")
                            time.sleep(2) # Wait 2 seconds before retrying
                        else:
                            # All retries failed
                            print(f"All retries failed for {video['title']}: {last_exception}")
                            failed_downloads_count += 1
                            failed_video_details.append((video_serial_number, video['title']))
                
                if not transcript_fetched_successfully and last_exception:
                    # This case should be covered by the else in the retry loop,
                    # but as a safeguard if loop finishes without success or final exception.
                    # This ensures it's counted if something unexpected happens.
                    if not any(vd[0] == video_serial_number for vd in failed_video_details): # Avoid double counting
                        print(f"Final error processing {video['title']} after retries: {last_exception}")
                        failed_downloads_count += 1
                        failed_video_details.append((video_serial_number, video['title']))
            
            # Final update
            self.update_progress(100)
            
            completion_message = f"Transcript extraction completed!\n"
            completion_message += f"Successful: {successful_downloads}\n"
            completion_message += f"Failed: {failed_downloads_count}\n"
            completion_message += f"Files saved to: {self.output_dir.get()}\n"

            if failed_downloads_count == 0:
                self.update_status(
                    f"Successfully downloaded {successful_downloads} transcripts!", "green"
                )
            else:
                status_text = f"Downloaded {successful_downloads}, {failed_downloads_count} failed. See pop-up for details."
                self.update_status(status_text, "orange")
                completion_message += "\nFailed Videos:\n"
                for sn, title in failed_video_details:
                    completion_message += f"  {sn}. {title}\n"

            # Show completion message
            messagebox.showinfo("Complete", completion_message)
            
            # Reset progress bar after delay
            self.root.after(3000, lambda: self.update_progress(0))
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.is_fetching = False

    def format_transcript_with_timestamps(self, transcript_list, title):
        """Format transcript with timestamps in markdown"""
        formatted_content = f"# {title}\n\n"
        formatted_content += f"**Video Title:** {title}\n\n"
        formatted_content += f"**Transcript extracted on:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        formatted_content += "---\n\n"
        
        for i, entry in enumerate(transcript_list): # Added enumerate for indexed logging
            # --- DIAGNOSTIC PRINT START ---
            if i == 0: # Print only for the first entry to avoid flooding console
                print(f"[FORMATTER_DIAG] Type of entry: {type(entry)}")
                print(f"[FORMATTER_DIAG] Content of entry (raw): {entry}")
                # Attempt to print attributes if it's an object, or keys if dict
                if hasattr(entry, '__dict__'):
                    print(f"[FORMATTER_DIAG] Content of entry (__dict__): {entry.__dict__}")
                elif isinstance(entry, dict):
                    print(f"[FORMATTER_DIAG] Content of entry (keys): {list(entry.keys())}")
            # --- DIAGNOSTIC PRINT END ---
            start_time = entry.start # MODIFIED_LINE
            duration = entry.duration # MODIFIED_LINE
            text = entry.text # MODIFIED_LINE
            
            # Convert seconds to MM:SS format
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"
            
            formatted_content += f"**[{timestamp}]** {text}\n\n"
        
        return formatted_content

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = YouTubeTranscriptExtractor(root)
    
    # Set minimum window size
    root.minsize(600, 500)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
