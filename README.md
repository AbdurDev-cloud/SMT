# Smart Traffic Management System (Edge AI) 🚦

An intelligent, real-time traffic management system designed for edge devices (specifically the **Raspberry Pi Zero**). This project uses Computer Vision to dynamically control traffic lights based on vehicle density across a 4-lane intersection, reducing congestion and waiting times.

It features an interactive GUI calibrator, multi-source video support (Webcams, MP4s, YouTube streams), hardware GPIO LED integration, and MQTT telemetry for cloud dashboards.

---

## 🌟 Key Features

*   **Edge AI Detection:** Uses a lightweight MobileNet-SSD model (Caffe) optimized for single-board computers. No heavy frameworks like PyTorch or TensorFlow are required.
*   **Dynamic Traffic Control:** Allocates "Green Light" time dynamically to the lane with the highest vehicle density. Includes safe Yellow light transitions.
*   **Multi-Source Video Input:** Automatically detects and handles video feeds from USB Webcams, local MP4 files, or live YouTube URLs.
*   **Thermal Management (Pi Zero):** Implements a frame-skipping inference pipeline to prevent the single-core CPU from overheating while maintaining a smooth visual output.
*   **Interactive ROI Calibrator:** Includes a point-and-click GUI tool to perfectly map detection zones to your specific camera angle.
*   **Cloud Telemetry:** Non-blocking background MQTT client pushes real-time traffic density data to cloud platforms (like ThingsBoard).
*   **Hardware / Simulation Mode:** Directly controls 12 GPIO pins for physical LEDs. If run on a PC/Mac without GPIO, it gracefully falls back to simulation mode.

---

## How it is made (system design)

The implementation follows a layered data-to-action flow:

### 1) Data Sources

- camera streams (USB webcam, MP4 samples, YouTube URL)
- manually calibrated lane ROIs

### 2) Ingestion Layer

- frame acquisition and source abstraction in `vision/camera.py`
- frame skipping to balance throughput and Pi Zero thermal limits

### 3) Processing & Decision Layer

- MobileNet-SSD inference in `vision/detector.py`
- lane-wise counting, congestion comparison, and green-lane selection logic

### 4) Control & Operations Layer

- traffic signal state machine in `control/traffic_light.py`
- GPIO control with simulation fallback for non-Pi environments

### 5) Visualization Layer

- OpenCV display windows for live inspection
- MQTT telemetry payloads for external dashboards

---

## End-to-end flow

1. Video frames are captured from the configured source.
2. Detector infers vehicles and maps detections into lane ROIs.
3. Counts are aggregated and the next green lane is selected.
4. Traffic light controller applies red/yellow/green transitions.
5. Telemetry is published to MQTT for dashboard visibility.

---

## 🛠️ Hardware Requirements

To build the physical IoT model, you will need:
*   **Raspberry Pi Zero W** (or any Pi model 3/4/5)
*   **Camera Module** (CSI PiCamera or USB Webcam)
*   **12x LEDs** (4x Red, 4x Yellow, 4x Green)
*   **12x 330Ω Resistors** & Jumper Wires
*   **Breadboard** or custom diorama

---

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AbdurDev-cloud/SMT.git
   cd SMT
   ```

2. **Set up a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   *Note: We pin OpenCV to `<5.0.0` because version 5 dropped support for the Caffe DNN module.*
   ```bash
   pip install "opencv-python<5.0.0" numpy paho-mqtt yt-dlp
   ```
   *(If you are on a Raspberry Pi, also install `RPi.GPIO`: `pip install RPi.GPIO`)*

4. **Download the MobileNet-SSD Model:**
   The `model/` folder includes a shell script to download the pre-trained weights.
   ```bash
   cd model
   sh download_model.sh
   cd ..
   ```

---

## 🚀 Usage

### 1. Configure your Video Source
Open `config.py` and set your `VIDEO_SOURCE`. It supports three modes:
```python
# 1. USB Webcam
VIDEO_SOURCE = 0

# 2. Local Video File (loops automatically)
VIDEO_SOURCE = "TrafficSample_6.mp4"

# 3. YouTube URL (requires yt-dlp)
VIDEO_SOURCE = "https://www.youtube.com/watch?v=EXAMPLE_ID"
```

### 2. Calibrate the Lanes
Because every camera angle is different, you must map the detection boxes to the physical roads. Run the calibrator tool:
```bash
python3 calibrate.py
```
* Use your mouse to draw a box for Lane 1, press `ENTER`. Repeat for all 4 lanes.
* The script will automatically parse and save your new coordinates directly into `config.py`.

### 3. Run the System
Start the main traffic controller:
```bash
python3 main.py
```
Press `q` to quit the application cleanly.

---

## 📁 Project Structure

```text
├── main.py                     # Main orchestrator loop
├── config.py                   # Central configuration (ROIs, GPIO, MQTT)
├── calibrate.py                # GUI tool for interactive ROI drawing
│
├── vision/
│   ├── camera.py               # Handles Webcams, MP4s, and YouTube streams
│   └── detector.py             # MobileNet-SSD DNN inference engine
│
├── control/
│   └── traffic_light.py        # 4-Lane State Machine and GPIO controller
│
├── cloud/
│   └── mqtt_client.py          # Background telemetry publisher
│
└── model/
    └── download_model.sh       # Script to fetch prototxt and caffemodel
```

---

## ☁️ Cloud Dashboard Integration (MQTT)

This system is pre-configured to send telemetry data to an MQTT broker.
1. Open `config.py`
2. Update the `MQTT_BROKER` and `MQTT_ACCESS_TOKEN` with your credentials (e.g., from ThingsBoard).
3. The system will publish JSON payloads formatted like this:
   ```json
   {
       "lane1_count": 4,
       "lane2_count": 0,
       "lane3_count": 1,
       "lane4_count": 2,
       "active_green_lane": 1
   }
   ```

---

## Roadmap

- [ ] Improve detection calibration and lane robustness
- [ ] Add reproducible dependency + environment lock files
- [ ] Add automated linting, tests, and CI checks
- [ ] Add dashboard templates for MQTT telemetry consumers

---

## Contribution guidelines

When contributing:

- keep modules focused and testable,
- include tests for new behavior,
- document architectural decisions,
- update this README whenever setup or structure changes.

---

## 📜 License
MIT License. Feel free to use this for your academic or personal IoT projects!
