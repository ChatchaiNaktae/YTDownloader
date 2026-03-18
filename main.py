import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import yt_dlp
import threading
import requests
import re
import sys
import os
from PIL import Image
from io import BytesIO

# --- Application UI Setup (Minimalist Style) ---
# Set theme and color
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller จะสร้างตัวแปร sys._MEIPASS ขึ้นมาเก็บ path ชั่วคราว
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def progress_hook(d):
    """Callback function to update progress bar and percentage"""
    if d['status'] == 'downloading':
        # Extract percentage string and clean it
        p = d.get('_percent_str', '0%')
        p_clean = re.sub(r'\x1b\[[0-9;]*m', '', p).replace('%', '').strip()
        
        try:
            percent_val = float(p_clean)
            # Update UI elements
            progress_bar.set(percent_val / 100.0)
            percent_label.configure(text=f"{percent_val:.1f}%")
            root.update_idletasks()
        except ValueError:
            pass
    
    if d['status'] == 'finished':
        progress_bar.set(1.0)
        percent_label.configure(text="100%")


def get_preview(*args):
    """Fetch video title and thumbnail preview without downloading"""
    url = url_var.get()
    
    # List of supported domains for triggering the preview
    supported_domains = ["youtube.com", "youtu.be", "twitter.com", "x.com", "pixiv.net", "instagram.com"]
    
    # Check if the URL contains any of the supported domains
    if any(domain in url for domain in supported_domains):
        def fetch_info():
            try:
                title_label.configure(text="Fetching info... please wait.")
                
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'No Title Found')
                    thumbnail_url = info.get('thumbnail')

                    title_label.configure(text=f"Title: {title}")

                    if thumbnail_url:
                        response = requests.get(thumbnail_url)
                        img_raw = Image.open(BytesIO(response.content))
                        
                        # Max bounding box
                        max_size = (450, 250) 
                        img_raw.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        my_image = ctk.CTkImage(light_image=img_raw, dark_image=img_raw, size=img_raw.size)
                        
                        preview_label.configure(image=my_image, text="")
                        preview_label.image = my_image
                    else:
                        preview_label.configure(image='', text="[ No Thumbnail Available ]")

            except Exception as e:
                title_label.configure(text="Status: Could not fetch info (Might be private/restricted).")
                preview_label.configure(image='', text="[ Error or Unsupported Link ]")

        threading.Thread(target=fetch_info, daemon=True).start()
    elif url == "":
        title_label.configure(text="No video selected")
        preview_label.configure(image='', text="[ Waiting for Link ]")


def download_video():
    """Main download function with progress tracking"""
    url = url_var.get()
    custom_name = name_entry.get()
    format_choice = format_var.get()

    if not url:
        messagebox.showerror("Error", "Please enter a URL first!")
        return

    # --- FIX 1: ดักจับเงื่อนไข Thumbnail ก่อนที่จะให้เลือกโฟลเดอร์เซฟ ---
    # ถ้าผู้ใช้เลือกโหลด Thumbnail แต่ลิงก์ไม่ใช่ YouTube ให้แจ้งเตือนและหยุดการทำงานทันที
    if format_choice == "thumbnail":
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showerror("Error", "Thumbnail download is ONLY supported for YouTube links!")
            return
    # --- END FIX 1 ---

    save_path = filedialog.askdirectory()
    if not save_path:
        return

    # Reset progress bar
    progress_bar.set(0)
    percent_label.configure(text="0%")
    
    # Show progress widgets
    progress_bar.pack(side="left", padx=(0, 10), expand=True, fill="x")
    percent_label.pack(side="right")

    # ตั้งค่าเริ่มต้นของชื่อไฟล์
    ydl_opts = {
        'outtmpl': f'{save_path}/{custom_name if custom_name else "%(title)s"}.%(ext)s',
        'progress_hooks': [progress_hook],
    }

    # --- FIX 2: ตั้งค่าการโหลดตาม Format ที่ผู้ใช้เลือก ---
    if format_choice == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif format_choice == "thumbnail":
        ydl_opts.update({
            'skip_download': True,      # ข้ามการโหลดวิดีโอ/เสียง
            'writethumbnail': True,     # สั่งให้โหลดเฉพาะรูปภาพ Thumbnail
            # ลบ .%(ext)s ออก เพราะรูปภาพจะใส่นามสกุลให้เองอัตโนมัติ (เช่น .webp หรือ .jpg)
            'outtmpl': f'{save_path}/{custom_name if custom_name else "%(title)s"}' 
        })
    else:
        # Default MP4 (Video)
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        })
    # --- END FIX 2 ---

    def run_dl():
        try:
            status_label.configure(text="Status: Downloading...", text_color="#3498db")
            download_btn.configure(state="disabled")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            status_label.configure(text="Status: Download Finished!", text_color="#2ecc71")
            messagebox.showinfo("Success", "Your file has been saved!")
        except Exception as e:
            status_label.configure(text="Status: Download Failed", text_color="#e74c3c")
            
            # Clean up ANSI color codes from yt-dlp error messages
            error_msg = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
            
            # Show the cleaned error message to the user
            messagebox.showerror("Download Error", f"Error: {error_msg}")
        finally:
            download_btn.configure(state="normal")
            
            # Hide progress widgets
            progress_bar.pack_forget()
            percent_label.pack_forget()

    threading.Thread(target=run_dl, daemon=True).start()


# --- GUI Construction (Modern Version) ---
root = ctk.CTk()
root.title("Universal Downloader Pro - By Chai")
root.iconbitmap(resource_path("icon.ico"))

# Center the window perfectly on the screen
window_width = 650 # ขยายหน้าต่างให้กว้างขึ้นนิดหน่อยเพื่อวางปุ่มที่ 3
window_height = 875
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int((screen_width / 2) - (window_width / 2))
center_y = int((screen_height / 2) - (window_height / 2))
root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

# Main container to hold everything with padding
main_frame = ctk.CTkFrame(root, fg_color="transparent")
main_frame.pack(fill="both", expand=True, padx=30, pady=30)

# URL Input Section
ctk.CTkLabel(main_frame, text="Step 1: Paste Link (YouTube, Twitter, Pixiv, Instagram)", font=ctk.CTkFont(family="Arial", size=14, weight="bold")).pack(pady=(0, 5))
url_var = tk.StringVar()
url_var.trace_add("write", get_preview)
url_entry = ctk.CTkEntry(main_frame, width=500, height=40, textvariable=url_var, placeholder_text="https://...")
url_entry.pack(pady=5)

# Preview Area
preview_frame = ctk.CTkFrame(main_frame, width=500, corner_radius=10)
preview_frame.pack(fill="x", pady=20)

preview_inner = ctk.CTkFrame(preview_frame, fg_color="transparent")
preview_inner.pack(padx=15, pady=15, fill="both")

preview_label = ctk.CTkLabel(preview_inner, text="[ Waiting for Link ]", width=450, height=250, fg_color=("gray80", "gray25"), corner_radius=8)
preview_label.pack(pady=10)

title_label = ctk.CTkLabel(preview_inner, text="No video selected", font=ctk.CTkFont(family="Arial", size=12, weight="bold"), wraplength=450)
title_label.pack(pady=5)

# Progress Section Container
progress_container = ctk.CTkFrame(main_frame, height=30, fg_color="transparent")
progress_container.pack(fill="x", pady=5)
progress_container.pack_propagate(False)

progress_bar = ctk.CTkProgressBar(progress_container, width=400, height=15)
progress_bar.set(0)
percent_label = ctk.CTkLabel(progress_container, text="0%", font=ctk.CTkFont(family="Arial", size=12, weight="bold"))

# Naming Input Section
ctk.CTkLabel(main_frame, text="Step 2: Custom File Name (Optional)", font=ctk.CTkFont(family="Arial", size=14, weight="bold")).pack(pady=(15, 5))
name_entry = ctk.CTkEntry(main_frame, width=500, height=40, placeholder_text="Leave blank to use original title")
name_entry.pack(pady=5)

# Format Selection Section
ctk.CTkLabel(main_frame, text="Step 3: Choose Format", font=ctk.CTkFont(family="Arial", size=14, weight="bold")).pack(pady=(15, 5))
format_var = tk.StringVar(value="mp4")
format_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
format_frame.pack(pady=5)

# --- FIX 3: เพิ่มปุ่มวิทยุ (Radio Button) สำหรับ Thumbnail ---
radio_mp4 = ctk.CTkRadioButton(format_frame, text="Video (MP4)", variable=format_var, value="mp4", font=ctk.CTkFont(family="Arial", size=12))
radio_mp4.pack(side="left", padx=15)

radio_mp3 = ctk.CTkRadioButton(format_frame, text="Audio (MP3)", variable=format_var, value="mp3", font=ctk.CTkFont(family="Arial", size=12))
radio_mp3.pack(side="left", padx=15)

radio_thumb = ctk.CTkRadioButton(format_frame, text="Thumbnail (YouTube Only)", variable=format_var, value="thumbnail", font=ctk.CTkFont(family="Arial", size=12))
radio_thumb.pack(side="left", padx=15)
# --- END FIX 3 ---

# Download Button
download_btn = ctk.CTkButton(main_frame, text="START DOWNLOAD", command=download_video, 
                             font=ctk.CTkFont(family="Arial", size=16, weight="bold"), 
                             height=50, width=300, corner_radius=8)
download_btn.pack(pady=30)

# Status Footer
status_label = ctk.CTkLabel(main_frame, text="Status: Ready", font=ctk.CTkFont(family="Arial", size=12, slant="italic"))
status_label.pack()

root.mainloop()