# main.py
# ================================================================
# Smart Traffic Management System v3.0 — 4-Lane Intersection
# MobileNet-SSD  •  4 ROI Lanes  •  R/Y/G Signals  •  MQTT Cloud
# ================================================================

import cv2
import time

from config import (
    VIDEO_SOURCE, CAMERA_RESOLUTION, LOOP_VIDEO, CAMERA_FRAMERATE,
    MODEL_PROTOTXT, MODEL_CAFFEMODEL,
    DNN_CONFIDENCE_THRESHOLD, DNN_INPUT_SIZE,
    VEHICLE_CLASS_IDS, FRAME_SKIP,
    LANE_ROIS, LANE_GPIO_PINS,
    MIN_GREEN_TIME, YELLOW_DURATION,
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_ACCESS_TOKEN,
)
from vision.camera import CameraHandler
from vision.detector import VehicleDetector
from control.traffic_light import TrafficLightController
from cloud.mqtt_client import TrafficMQTTClient


# Colors for drawing each lane's ROI (BGR)
LANE_COLORS = {
    "Lane 1": (0, 255, 255),   # Cyan    (East)
    "Lane 2": (255, 0, 255),   # Magenta (North)
    "Lane 3": (255, 255, 0),   # Yellow  (West)
    "Lane 4": (0, 165, 255),   # Orange  (South)
}

# Map traffic light state to an overlay color
SIGNAL_COLORS = {
    "GREEN":  (0, 255, 0),
    "YELLOW": (0, 255, 255),
    "RED":    (0, 0, 255),
}


def main():
    print("=" * 60)
    print("  Smart Traffic Management System v3.0")
    print("  MobileNet-SSD  •  4-Lane Intersection  •  R/Y/G Logic")
    print("=" * 60)

    # ---- Initialize subsystems ----
    camera = CameraHandler(source=VIDEO_SOURCE, resolution=CAMERA_RESOLUTION, loop_video=LOOP_VIDEO)

    detector = VehicleDetector(
        prototxt_path=MODEL_PROTOTXT,
        caffemodel_path=MODEL_CAFFEMODEL,
        confidence_threshold=DNN_CONFIDENCE_THRESHOLD,
        input_size=DNN_INPUT_SIZE,
        vehicle_class_ids=VEHICLE_CLASS_IDS,
    )

    controller = TrafficLightController(
        lane_gpio_pins=LANE_GPIO_PINS,
        min_green_time=MIN_GREEN_TIME,
        yellow_duration=YELLOW_DURATION,
    )

    mqtt_client = TrafficMQTTClient(
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        topic=MQTT_TOPIC,
        access_token=MQTT_ACCESS_TOKEN,
    )
    mqtt_client.connect()

    # Cached results between inference frames
    last_detections = []
    lane_counts = {lane: 0 for lane in LANE_ROIS}
    frame_number = 0
    inference_ms = 0.0

    try:
        camera.start()

        while True:
            ret, frame = camera.get_frame()
            if not ret:
                print("[ERROR] Failed to grab frame. Is the camera connected?")
                break

            frame_number += 1

            # ---- Frame Skipping: run DNN only every Nth frame ----
            if frame_number % FRAME_SKIP == 0:
                t0 = time.time()
                last_detections = detector.detect(frame)
                inference_ms = (time.time() - t0) * 1000.0

                # Count vehicles inside each of the 4 ROIs
                for lane_name, roi in LANE_ROIS.items():
                    lane_counts[lane_name] = VehicleDetector.count_in_roi(last_detections, roi)

                # Update traffic light — highest density lane gets GREEN
                controller.update(lane_counts)

                # Publish telemetry to cloud
                mqtt_client.publish_lane_telemetry(
                    lane_counts, controller.green_lane,
                    controller.lane_states, inference_ms
                )

                # Console log
                counts_str = "  ".join(f"{ln}: {c}" for ln, c in lane_counts.items())
                print(f"[DET] Frame #{frame_number:>6}  |  {counts_str}  |  "
                      f"Inference: {inference_ms:.0f} ms  |  "
                      f"Green: {controller.green_lane}")

            # ---- Always draw the latest cached results for smooth display ----
            VehicleDetector.draw_detections(frame, last_detections)

            # Draw each lane's ROI with its count
            for lane_name, roi in LANE_ROIS.items():
                color = LANE_COLORS.get(lane_name, (255, 255, 255))
                count = lane_counts[lane_name]
                VehicleDetector.draw_roi(frame, roi, f"{lane_name}: {count}", color)

            # ---- HUD: Traffic Light Status Panel ----
            y_offset = 22
            cv2.putText(frame, "SIGNAL STATUS", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 24

            for lane_name in LANE_ROIS:
                state = controller.lane_states.get(lane_name, "RED")
                color = SIGNAL_COLORS.get(state, (255, 255, 255))

                # Draw a small filled circle as the signal indicator
                cv2.circle(frame, (20, y_offset - 5), 7, color, -1)
                cv2.circle(frame, (20, y_offset - 5), 7, (255, 255, 255), 1)

                label = f"{lane_name}: {state} ({lane_counts[lane_name]} vehicles)"
                cv2.putText(frame, label, (34, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
                y_offset += 22

            # Inference timer
            cv2.putText(frame, f"Inference: {inference_ms:.0f} ms (every {FRAME_SKIP} frames)",
                        (10, y_offset + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

            # Display (disable cv2.imshow on headless Pi Zero in production)
            cv2.imshow("Smart Traffic Management v3 — 4 Lane", frame)

            # Determine delay to maintain roughly the configured framerate
            delay = int(1000 / CAMERA_FRAMERATE)
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                print("[INFO] Exiting...")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
    finally:
        camera.release()
        controller.cleanup()
        mqtt_client.disconnect()
        cv2.destroyAllWindows()
        print("[INFO] System shut down cleanly.")


if __name__ == "__main__":
    main()
