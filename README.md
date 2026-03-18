# 🚀 Universal Downloader Pro

A modern, fast, and user-friendly desktop application for downloading videos, audio, and thumbnails from various platforms (YouTube, Twitter, Pixiv, Instagram). Built with Python, `customtkinter`, and `yt-dlp`.

## ✨ Features
- **Sleek UI:** Modern dark/light mode interface using `customtkinter`.
- **Multi-Format Support:** Download Video (MP4), Audio (MP3), or just the Thumbnail.
- **Live Preview:** Fetches and displays video titles and thumbnails before downloading.
- **Progress Tracking:** Real-time progress bar and percentage indicator.
- **Broad Compatibility:** Works with YouTube, Twitter/X, Instagram, and more.

## 🛠️ Prerequisites
To run this project or build it yourself, you will need:
- **Python 3.x**
- **FFmpeg:** Required for audio extraction (MP3) and merging high-quality video/audio. Ensure it is added to your system's PATH.
- **Node.js:** Required for bypassing certain YouTube API script decoding.

## 📦 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/Universal-YTDownloader.git](https://github.com/YOUR_GITHUB_USERNAME/Universal-YTDownloader.git)
   cd Universal-YTDownloader
   ```
2. **Install the required libraries:**
    ```bash
    pip install yt-dlp customtkinter Pillow requests
    ```
3. **Run the application:**
    ```bash
    python main.py
    ```