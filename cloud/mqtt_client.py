# cloud/mqtt_client.py
# ================================================================
# MQTT Publisher for Smart Traffic Management System
# Publishes lane density telemetry to a cloud platform (e.g. ThingsBoard).
# Designed to be non-blocking so it never stalls the main vision loop.
# ================================================================

import json
import time
import threading

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("[WARN] paho-mqtt not installed — cloud publishing disabled.")
    print("       Install with:  pip install paho-mqtt")


class TrafficMQTTClient:
    """
    Lightweight MQTT client that publishes traffic telemetry as JSON.

    Features:
      • Auto-reconnect with exponential backoff (doesn't crash the system)
      • Publishes on a background thread so the vision loop is never blocked
      • Batches telemetry into a simple JSON payload compatible with ThingsBoard
    """

    def __init__(self, broker, port, topic, access_token, client_id="smt_edge_device"):
        """
        Args:
            broker:        MQTT broker hostname (e.g. "mqtt.thingsboard.cloud")
            port:          Broker port (typically 1883 for non-TLS)
            topic:         Publish topic (ThingsBoard uses "v1/devices/me/telemetry")
            access_token:  Device access token (used as MQTT username for ThingsBoard)
            client_id:     Unique client identifier
        """
        self.broker = broker
        self.port = port
        self.topic = topic
        self.access_token = access_token
        self.connected = False
        self._client = None

        if not MQTT_AVAILABLE:
            return

        self._client = mqtt.Client(client_id=client_id)

        # ThingsBoard authenticates via the username field
        self._client.username_pw_set(access_token)

        # Callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------
    def connect(self):
        """Connect to the MQTT broker in the background (non-blocking)."""
        if not MQTT_AVAILABLE or self._client is None:
            print("[MQTT] Skipped — paho-mqtt not available.")
            return

        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            # Start a background thread for the network loop
            self._client.loop_start()
            print(f"[MQTT] Connecting to {self.broker}:{self.port}...")
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            print("[MQTT] System will continue without cloud publishing.")

    def disconnect(self):
        """Gracefully disconnect from the broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            print("[MQTT] Disconnected.")

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------
    def publish_lane_telemetry(self, lane_counts, green_lane, lane_states, inference_ms=0.0):
        """
        Publish a 4-lane telemetry payload to the cloud.

        Args:
            lane_counts:  Dict {"Lane 1": 3, "Lane 2": 7, "Lane 3": 0, "Lane 4": 2}
            green_lane:   Name of the lane currently green (e.g. "Lane 2")
            lane_states:  Dict {"Lane 1": "RED", "Lane 2": "GREEN", ...}
            inference_ms: DNN inference time in milliseconds

        Payload format (JSON):
        {
            "ts": 1720278000000,
            "values": {
                "lane_1_vehicles": 3,
                "lane_2_vehicles": 7,
                "lane_3_vehicles": 0,
                "lane_4_vehicles": 2,
                "total_vehicles": 12,
                "green_lane": "Lane 2",
                "lane_1_signal": "RED",
                "lane_2_signal": "GREEN",
                "lane_3_signal": "RED",
                "lane_4_signal": "RED",
                "inference_ms": 850.2
            }
        }
        """
        if not self.connected:
            return

        total = sum(lane_counts.values())

        values = {}
        for lane_name, count in lane_counts.items():
            key = lane_name.lower().replace(" ", "_") + "_vehicles"
            values[key] = count

        for lane_name, state in lane_states.items():
            key = lane_name.lower().replace(" ", "_") + "_signal"
            values[key] = state

        values["total_vehicles"] = total
        values["green_lane"] = green_lane
        values["inference_ms"] = round(inference_ms, 1)

        payload = {
            "ts": int(time.time() * 1000),
            "values": values,
        }

        try:
            result = self._client.publish(self.topic, json.dumps(payload), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] Published — Total: {total}  Green: {green_lane}")
            else:
                print(f"[MQTT] Publish failed (rc={result.rc})")
        except Exception as e:
            print(f"[MQTT] Publish error: {e}")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"[MQTT] Connected to {self.broker} successfully.")
        else:
            self.connected = False
            print(f"[MQTT] Connection refused (code {rc}).")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            print(f"[MQTT] Unexpected disconnect (code {rc}). Auto-reconnecting...")
        else:
            print("[MQTT] Disconnected cleanly.")
