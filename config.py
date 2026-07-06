# config.py
# ================================================================
# Configuration — 4-Lane Intersection Smart Traffic Management
# ================================================================

# --- Video Source ---
# Choose ONE of the following input modes:
#
# 1. WEBCAM (default for Raspberry Pi / laptop):
# VIDEO_SOURCE = 0
#
# 2. LOCAL VIDEO FILE (for testing/demo without a camera):
# VIDEO_SOURCE = "videos/traffic_sample.mp4"
#
# 3. YOUTUBE URL (live stream or recorded traffic footage):
# VIDEO_SOURCE = "https://www.youtube.com/watch?v=EXAMPLE_ID"
#   → Requires: pip install yt-dlp
#
VIDEO_SOURCE = "TrafficSample_6.mp4"  # ← Change this to a file path or YouTube URL as needed
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 24
LOOP_VIDEO = True  # If True, local video files restart when they end

# --- MobileNet-SSD Model Settings ---
MODEL_PROTOTXT = "model/MobileNetSSD_deploy.prototxt"
MODEL_CAFFEMODEL = "model/MobileNetSSD_deploy.caffemodel"
DNN_CONFIDENCE_THRESHOLD = 0.5
DNN_INPUT_SIZE = (300, 300)

# PASCAL VOC class indices treated as "vehicles"
# 6 = bus, 7 = car, 14 = motorbike
VEHICLE_CLASS_IDS = {6, 7, 14}

# --- Frame Skipping (Pi Zero Thermal Management) ---
FRAME_SKIP = 24  # At 24 FPS → ~1 inference per second

# --- ROI Definitions (4 Lanes) ---
# Each ROI is (x, y, width, height) in pixel coordinates.
# Layout on a 640×480 frame:
#
#              LANE 2 (North)
#          ┌──────────────────┐
#          │    (220,10)      │
#          │    200×110       │
#          └──────────────────┘
#   LANE 3               LANE 1
# ┌────────┐             ┌────────┐
# │(10,160)│             │(470,160)│
# │160×160 │             │ 160×160│
# └────────┘             └────────┘
#          ┌──────────────────┐
#          │   (220,360)      │
#          │   200×110        │
#          └──────────────────┘
#              LANE 4 (South)
#
LANE_ROIS = {
    "Lane 1": (393, 196, 243, 251),
    "Lane 2": (100, 89, 210, 69),
    "Lane 3": (13, 170, 131, 211),
    "Lane 4": (384, 83, 165, 86),
}

# --- GPIO Pins (BCM numbering) — 4 Lanes × 3 LEDs each ---
# Each lane has its own Red, Yellow, Green LED
LANE_GPIO_PINS = {
    "Lane 1": {"red": 17, "yellow": 27, "green": 22},
    "Lane 2": {"red":  5, "yellow":  6, "green": 13},
    "Lane 3": {"red": 19, "yellow": 26, "green": 21},
    "Lane 4": {"red": 20, "yellow": 16, "green": 12},
}

# --- Timing (seconds) ---
MIN_GREEN_TIME = 5    # Minimum green before allowing a switch
YELLOW_DURATION = 2   # Yellow light duration during transitions

# --- MQTT / Cloud Settings ---
MQTT_BROKER = "mqtt.thingsboard.cloud"
MQTT_PORT = 1883
MQTT_TOPIC = "v1/devices/me/telemetry"
MQTT_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
