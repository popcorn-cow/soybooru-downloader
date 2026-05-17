#This file is part of "SOYBOORU-DOWNLOADER"


#Copyright (C) 2026 POPCORN-COW

#This program is free software: you can redistribute it and/or modify

#it under the terms of the GNU Affero General Public License as published

#by the Free Software Foundation, either version 3 of the License, or

#(at your option) any later version, with the HWABAG License Modifier applied.

#The HWABAG License Modifier requires the inclusion of an additional image (HWABAG.png)

#in the top level this software's directory tree. This content is clearly

#separable from functional elements and does not restrict user freedoms.

#This program is distributed in the hope that it will be useful,

#but WITHOUT ANY WARRANTY; without even the implied warranty of

#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the

#GNU Affero General Public License for more details.

#You should have received a copy of the GNU Affero General Public License

#along with this program. If not, see <https://www.gnu.org/licenses/>.

#Modifier text is available in LICENSE file provided with this software 
import os
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from urllib.parse import quote_plus, urljoin
import xml.etree.ElementTree as ET
from datetime import datetime
from curl_cffi import requests
BASE_URL = "https://soybooru.com"
API_URL = BASE_URL + "/api/booru/posts/"
EXT_MAP = {
    "image": [".jpg", ".jpeg", ".png", ".webp", ".jfif", ".jfi", ".cbz", ".bmp", ".tif", ".tiff", ".tga", ".psd", ".ico", ".cur", ".cbz", ".ppm"],
    "gif": [".gif", ".webp"],
    "video": [".mp4", ".webm", ".mp4", ".m4v", ".ogv", ".mov", ".flv", ".avi", ".wmv", ".asf", ".asx"],
    "vector": [".svg"],
    "swf": [".swf"],
}
session = requests.Session(impersonate="firefox")
session.headers.update({
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": BASE_URL + "/",
})
def safe_filename(name):
    return "".join(c for c in name if c not in r'\/:*?"<>|')
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SoyBooru downloader")
        self.geometry("400x300")
        self.resizable(True, True)
        self.folder = tk.StringVar(value="No folder selected")
        self.max_items = tk.StringVar(value="50")
        self.format_vars = {
            "image": tk.BooleanVar(value=True),
            "gif": tk.BooleanVar(value=True),
            "video": tk.BooleanVar(value=True),
            "vector": tk.BooleanVar(value=False),
            "swf": tk.BooleanVar(value=False),
        }
        self.build_ui()
    def build_ui(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(main_frame, text="Tags:", anchor="e", width=15).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.tags_entry = tk.Entry(main_frame, fg="darkgreen")
        self.tags_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.start_btn = tk.Button(main_frame, text="Start Download", command=self.start)
        self.start_btn.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        tk.Label(main_frame, text="Exclude tags:", anchor="e", width=15).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.exclude_entry = tk.Entry(main_frame, fg="darkred")
        self.exclude_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        tk.Label(main_frame, text="Format:", anchor="e", width=15).grid(row=2, column=0, sticky="e", padx=5, pady=5)
        fmt_frame = tk.Frame(main_frame)
        fmt_frame.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        for i, (name, var) in enumerate(self.format_vars.items()):
            tk.Checkbutton(fmt_frame, text=name, variable=var).pack(side=tk.LEFT, padx=5)
        tk.Label(main_frame, text="Max items:", anchor="e", width=15).grid(row=3, column=0, sticky="e", padx=5, pady=5)
        max_frame = tk.Frame(main_frame)
        max_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        tk.Entry(max_frame, textvariable=self.max_items, width=10).pack(side=tk.LEFT)
        tk.Label(main_frame, text="Folder:", anchor="e", width=15).grid(row=4, column=0, sticky="e", padx=5, pady=5)
        folder_frame = tk.Frame(main_frame)
        folder_frame.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        tk.Button(folder_frame, text="Choose...", command=self.choose_folder).pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(folder_frame, textvariable=self.folder, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        log_frame = tk.Frame(main_frame)
        log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled', wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        self.log("Ready to download.")
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    def choose_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder.set(path)
            self.log(f"Selected folder: {path}")
    def start(self):
        if not os.path.isdir(self.folder.get()):
            messagebox.showerror("Error", "Please choose a valid folder.")
            return
        try:
            max_items = int(self.max_items.get())
            if max_items <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Max items must be a positive number, you retarded nigger")
            return
        self.start_btn.config(state="disabled")
        self.log("Starting download...")
        threading.Thread(target=self.run_scraper, daemon=True).start()
    def run_scraper(self):
        try:
            tags = self.tags_entry.get().strip()
            excludes = self.exclude_entry.get().strip()
            tag_list = tags.split()
            if excludes:
                tag_list.extend(f"-{t}" for t in excludes.split())
            tag_query = quote_plus(" ".join(tag_list))
            allowed_exts = []
            for name, enabled in self.format_vars.items():
                if enabled.get():
                    allowed_exts.extend(EXT_MAP[name])
            self.log(f"Tags: {' '.join(tag_list)}")
            self.log(f"Allowed formats: {', '.join(allowed_exts)}")
            downloaded = 0
            page = 1
            limit = 5
            max_items = int(self.max_items.get())
            while downloaded < max_items:
                url = f"{API_URL}?tags={tag_query}&limit={limit}&page={page}"
                self.log(f"Fetching page {page}...")
                try:
                    r = session.get(url, timeout=30)
                    r.raise_for_status()
                except Exception as e:
                    error_msg = f"Failed to fetch API: {type(e).__name__}: {str(e)}"
                    self.log(f"ERROR: {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    return
                try:
                    root = ET.fromstring(r.text)
                except ET.ParseError as e:
                    error_msg = f"Failed to parse XML response: {str(e)}"
                    self.log(f"ERROR: {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    return
                posts = root.findall("tag")
                self.log(f"Found {len(posts)} posts on page {page}")
                if not posts:
                    self.log("No more posts found.")
                    break
                for post in posts:
                    if downloaded >= max_items:
                        break
                    file_url = post.attrib.get("file_url")
                    if not file_url:
                        continue
                    full_url = urljoin(BASE_URL, file_url)
                    ext = os.path.splitext(full_url)[1].lower()
                    if allowed_exts and ext not in allowed_exts:
                        continue
                    fname = safe_filename(
                        f"{post.attrib.get('id','file')}_{os.path.basename(full_url)}"
                    )
                    out_path = os.path.join(self.folder.get(), fname)
                    if os.path.exists(out_path):
                        self.log(f"Skipping {fname} (already exists)")
                        continue
                    self.log(f"Downloading {fname} ({downloaded + 1}/{max_items})")
                    try:
                        dl = session.get(full_url, stream=True, timeout=60)
                        dl.raise_for_status()
                        with open(out_path, "wb") as f:
                            for chunk in dl.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                        downloaded += 1
                        self.log(f"Downloaded {fname}")
                    except Exception as e:
                        self.log(f"Failed to download {fname}: {str(e)}")
                        continue
                page += 1
            final_msg = f"Downloaded {downloaded} 'jaks."
            self.log(final_msg)
            messagebox.showinfo("Complete", final_msg)
        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.log(f"FATAL ERROR: {error_msg}")
            self.log(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
        finally:
            self.start_btn.config(state="normal")
if __name__ == "__main__":
    App().mainloop()
