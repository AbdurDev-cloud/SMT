# vision/camera.py
# ================================================================
# Multi-Source Video Handler
#
# Supports three input modes:
#   1. Webcam        → VIDEO_SOURCE = 0  (or any integer)
#   2. Local file    → VIDEO_SOURCE = "path/to/traffic_video.mp4"
#   3. YouTube URL   → VIDEO_SOURCE = "https://www.youtube.com/watch?v=..."
#
# YouTube streams require yt-dlp:  pip install yt-dlp
# ================================================================

import cv2
import time
import subprocess
import re


class CameraHandler:
    """
    Unified video source handler.

    Automatically detects the input type from the source value:
      • int           → webcam index
      • str ending in common video extensions → local file
      • str containing "youtube" or "youtu.be" → YouTube stream
      • any other str → treated as a direct URL / file path
    """

    def __init__(self, source=0, resolution=(640, 480), loop_video=True):
        """
        Args:
            source:      Webcam index (int), file path (str), or YouTube URL (str)
            resolution:  Desired output resolution (width, height)
            loop_video:  If True, local video files restart when they end
        """
        self.source = source
        self.resolution = resolution
        self.loop_video = loop_video
        self.cap = None
        self._source_type = None  # "webcam", "file", or "youtube"
        self._resolved_url = None  # The actual URL/path passed to VideoCapture

    def start(self):
        """Detects the source type and opens the video capture."""
        self._resolve_source()

        print(f"[CAM] Opening source: {self._source_type} → {self._display_source()}")
        self.cap = cv2.VideoCapture(self._resolved_url)

        # Only set resolution for webcams (files have their own resolution)
        if self._source_type == "webcam":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            time.sleep(2.0)  # Warm-up time for the camera sensor

        if not self.cap.isOpened():
            raise RuntimeError(
                f"[CAM] Error: Could not open video source.\n"
                f"      Type: {self._source_type}\n"
                f"      Path: {self._resolved_url}"
            )

        # Read actual resolution from the opened source
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS) or "N/A"
        print(f"[CAM] Started — {actual_w}×{actual_h} @ {fps} FPS")

    def get_frame(self):
        """
        Captures and returns a single frame, resized to self.resolution.
        For video files with loop_video=True, restarts when the video ends.
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None

        ret, frame = self.cap.read()

        # Handle end-of-video for local files
        if not ret and self._source_type == "file" and self.loop_video:
            print("[CAM] Video ended — looping back to start.")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        if not ret:
            return False, None

        # Resize to target resolution for consistent ROI coordinates
        frame = cv2.resize(frame, self.resolution)
        return True, frame

    def release(self):
        """Releases the video capture resources."""
        if self.cap:
            self.cap.release()
            print("[CAM] Released.")

    # ------------------------------------------------------------------
    # Source resolution
    # ------------------------------------------------------------------
    def _resolve_source(self):
        """Detect the source type and resolve to a usable URL/path."""

        # Webcam (integer index)
        if isinstance(self.source, int):
            self._source_type = "webcam"
            self._resolved_url = self.source
            return

        source_str = str(self.source).strip()

        # YouTube URL
        if self._is_youtube_url(source_str):
            self._source_type = "youtube"
            self._resolved_url = self._extract_youtube_stream(source_str)
            return

        # Local file or direct URL
        self._source_type = "file"
        self._resolved_url = source_str

    @staticmethod
    def _is_youtube_url(url):
        """Check if a URL points to YouTube."""
        patterns = [
            r"(https?://)?(www\.)?youtube\.com/watch",
            r"(https?://)?(www\.)?youtube\.com/live",
            r"(https?://)?youtu\.be/",
            r"(https?://)?(www\.)?youtube\.com/shorts",
        ]
        for pattern in patterns:
            if re.search(pattern, url):
                return True
        return False

    @staticmethod
    def _extract_youtube_stream(youtube_url):
        """
        Use yt-dlp to extract the direct stream URL from a YouTube video.
        Returns the best available MP4 stream URL that OpenCV can read.
        """
        try:
            print(f"[CAM] Extracting stream URL from YouTube...")
            print(f"      {youtube_url}")

            # Get the direct video URL using yt-dlp
            # -f best[ext=mp4]  → best quality MP4
            # -g               → print URL only (don't download)
            result = subprocess.run(
                [
                    "yt-dlp",
                    "-f", "best[ext=mp4][height<=720]",  # Cap at 720p for Pi Zero
                    "-g",                                 # Output URL only
                    "--no-warnings",
                    youtube_url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"yt-dlp failed:\n{result.stderr.strip()}\n"
                    f"Install/update with:  pip install -U yt-dlp"
                )

            stream_url = result.stdout.strip().split("\n")[0]
            print(f"[CAM] YouTube stream URL extracted successfully.")
            return stream_url

        except FileNotFoundError:
            raise RuntimeError(
                "[CAM] yt-dlp is not installed.\n"
                "      Install with:  pip install yt-dlp"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "[CAM] yt-dlp timed out. Check your internet connection."
            )

    def _display_source(self):
        """Return a shortened version of the source for logging."""
        if self._source_type == "webcam":
            return f"Webcam index {self.source}"
        if self._source_type == "youtube":
            return f"{self.source} (resolved)"
        # For files, show just the filename
        return str(self._resolved_url).split("/")[-1]
