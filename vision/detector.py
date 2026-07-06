# vision/detector.py
# ================================================================
# MobileNet-SSD Vehicle Detector for Raspberry Pi Zero
# Uses OpenCV's DNN module — no TensorFlow/PyTorch runtime needed.
# Detects BOTH moving and stationary vehicles (unlike MOG2).
# ================================================================

import cv2
import numpy as np


# PASCAL VOC class labels that MobileNet-SSD was trained on (21 classes)
MOBILENET_SSD_CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair",
    "cow", "diningtable", "dog", "horse", "motorbike",
    "person", "pottedplant", "sheep", "sofa", "train",
    "tvmonitor"
]


class VehicleDetector:
    """
    Lightweight DNN-based vehicle detector using MobileNet-SSD (Caffe).

    Design decisions for Pi Zero (512 MB RAM, single-core 1 GHz):
      • Uses cv2.dnn which is written in C++ — faster than Python-only loops.
      • Input blob is resized to 300×300 regardless of camera resolution.
      • Frame skipping is handled externally; this class processes every
        frame it receives.
    """

    def __init__(self, prototxt_path, caffemodel_path,
                 confidence_threshold=0.5,
                 input_size=(300, 300),
                 vehicle_class_ids=None):
        """
        Args:
            prototxt_path:        Path to MobileNetSSD_deploy.prototxt
            caffemodel_path:      Path to MobileNetSSD_deploy.caffemodel
            confidence_threshold: Minimum probability to accept a detection
            input_size:           DNN input blob dimensions (width, height)
            vehicle_class_ids:    Set of PASCAL VOC class indices to count
                                  as vehicles. Defaults to {6, 7, 14}
                                  (bus, car, motorbike).
        """
        self.confidence_threshold = confidence_threshold
        self.input_size = input_size
        self.vehicle_class_ids = vehicle_class_ids or {6, 7, 14}

        # Load the Caffe model into OpenCV's DNN engine
        print("[INFO] Loading MobileNet-SSD model...")
        self.net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)

        # Force CPU backend (Pi Zero has no GPU / OpenCL)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        print("[INFO] Model loaded successfully.")

    # ------------------------------------------------------------------
    # Core detection
    # ------------------------------------------------------------------
    def detect(self, frame):
        """
        Run MobileNet-SSD inference on a single frame.

        Returns:
            List of detections, each being a dict:
            {
                "class_id":   int,
                "label":      str,
                "confidence": float,
                "box":        (x1, y1, x2, y2)   # absolute pixel coords
            }
        """
        h, w = frame.shape[:2]

        # Build a 300×300 mean-subtracted blob (MobileNet-SSD requirement)
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, self.input_size),
            scalefactor=0.007843,           # 1/127.5
            size=self.input_size,
            mean=(127.5, 127.5, 127.5),     # Mean subtraction
            swapRB=False,
            crop=False
        )
        self.net.setInput(blob)
        raw_detections = self.net.forward()  # shape: (1, 1, N, 7)

        results = []
        for i in range(raw_detections.shape[2]):
            confidence = float(raw_detections[0, 0, i, 2])
            if confidence < self.confidence_threshold:
                continue

            class_id = int(raw_detections[0, 0, i, 1])

            # Only keep vehicle classes
            if class_id not in self.vehicle_class_ids:
                continue

            # Scale bounding box back to original frame dimensions
            box = raw_detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype("int")

            # Clamp to frame boundaries
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            label = MOBILENET_SSD_CLASSES[class_id] if class_id < len(MOBILENET_SSD_CLASSES) else "vehicle"

            results.append({
                "class_id": class_id,
                "label": label,
                "confidence": confidence,
                "box": (x1, y1, x2, y2),
            })

        return results

    # ------------------------------------------------------------------
    # ROI intersection counting
    # ------------------------------------------------------------------
    @staticmethod
    def count_in_roi(detections, roi):
        """
        Count how many detected bounding boxes intersect with an ROI.

        Args:
            detections: List of detection dicts from self.detect()
            roi:        Tuple (rx, ry, rw, rh) defining the Region of Interest

        Returns:
            int — number of vehicles whose bounding box overlaps the ROI
        """
        rx, ry, rw, rh = roi
        roi_x2 = rx + rw
        roi_y2 = ry + rh
        count = 0

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            # Check for rectangle intersection (non-zero overlap area)
            if x1 < roi_x2 and x2 > rx and y1 < roi_y2 and y2 > ry:
                count += 1

        return count

    # ------------------------------------------------------------------
    # Visualization helpers
    # ------------------------------------------------------------------
    @staticmethod
    def draw_detections(frame, detections):
        """Draws bounding boxes and labels on the frame."""
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            label = f"{det['label']}: {det['confidence']:.0%}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Label background for readability
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw, y1), (0, 255, 0), -1)
            cv2.putText(frame, label, (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    @staticmethod
    def draw_roi(frame, roi, label, color=(255, 255, 0)):
        """Draws an ROI rectangle with a label."""
        rx, ry, rw, rh = roi
        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), color, 2)
        cv2.putText(frame, label, (rx + 4, ry + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
