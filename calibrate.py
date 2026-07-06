import cv2
from vision.camera import CameraHandler
from config import VIDEO_SOURCE, CAMERA_RESOLUTION

def calibrate_rois():
    print("=" * 50)
    print(" ROI Calibration Tool")
    print("=" * 50)
    print("1. A window will open showing a frame from your video.")
    print("2. Use your mouse to click and drag a rectangle for Lane 1.")
    print("3. Press ENTER or SPACE to confirm the box.")
    print("4. Repeat for Lanes 2, 3, and 4.")
    print("5. Press 'c' to cancel a box and redraw it.")
    print("=" * 50)
    
    # Grab a single frame
    cam = CameraHandler(source=VIDEO_SOURCE, resolution=CAMERA_RESOLUTION)
    cam.start()
    ret, frame = cam.get_frame()
    cam.release()

    if not ret:
        print("[ERROR] Could not read from the video source.")
        return

    lane_names = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]
    new_rois = {}

    for lane in lane_names:
        # Clone frame to draw instructions
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Draw box for: {lane} (Press ENTER to confirm)", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Open ROI selector
        roi = cv2.selectROI(f"Calibration - {lane}", display_frame, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(f"Calibration - {lane}")
        
        if roi == (0, 0, 0, 0):
            print(f"[WARN] Skipped {lane}. Using dummy values.")
            new_rois[lane] = (10, 10, 100, 100)
        else:
            new_rois[lane] = roi
            # Draw the confirmed ROI onto the base frame so they can see previous boxes
            x, y, w, h = roi
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, lane, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Generate the new dictionary string
    new_rois_str = "LANE_ROIS = {\n"
    for lane, roi in new_rois.items():
        new_rois_str += f'    "{lane}": {roi},\n'
    new_rois_str += "}"

    # Auto-update config.py
    import re
    try:
        with open('config.py', 'r') as f:
            config_content = f.read()
        
        # Replace the entire LANE_ROIS block
        updated_content = re.sub(
            r'LANE_ROIS\s*=\s*\{[^\}]+\}', 
            new_rois_str, 
            config_content
        )
        
        with open('config.py', 'w') as f:
            f.write(updated_content)
            
        print("\n" + "=" * 55)
        print(" SUCCESS! config.py has been AUTO-UPDATED.")
        print(" The new coordinates are now actively saved:")
        print("=" * 55)
        print(new_rois_str)
        print("\nYou can now run `python3 main.py` to see your changes.")
    except Exception as e:
        print(f"[ERROR] Could not auto-update config.py: {e}")

if __name__ == "__main__":
    calibrate_rois()
