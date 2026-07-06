# control/traffic_light.py
# ================================================================
# 4-Lane Intersection Traffic Light Controller
#
# Logic:
#   • The lane with the HIGHEST vehicle density gets GREEN.
#   • All other lanes get RED.
#   • During transitions: outgoing lane goes GREEN → YELLOW → RED,
#     then the new priority lane goes RED → GREEN.
#   • Minimum green time prevents rapid flickering.
#   • If all lanes have zero traffic, the current green lane holds.
# ================================================================

import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[WARN] RPi.GPIO not found — running in simulation mode.")


class TrafficLightController:
    """
    Controls a 4-lane intersection with independent R/Y/G LEDs per lane.

    State is represented by `self.green_lane` — the name of the lane
    that currently has a green signal (e.g. "Lane 1"). All other lanes
    are red.
    """

    def __init__(self, lane_gpio_pins, min_green_time=5, yellow_duration=2):
        """
        Args:
            lane_gpio_pins: Dict mapping lane names to GPIO pin dicts.
                            Example:
                            {
                                "Lane 1": {"red": 17, "yellow": 27, "green": 22},
                                "Lane 2": {"red":  5, "yellow":  6, "green": 13},
                                ...
                            }
            min_green_time:   Minimum seconds a lane stays green before switch
            yellow_duration:  Seconds the yellow light is held during transition
        """
        self.lane_pins = lane_gpio_pins
        self.lane_names = list(lane_gpio_pins.keys())
        self.min_green_time = min_green_time
        self.yellow_duration = yellow_duration

        # Start with the first lane green
        self.green_lane = self.lane_names[0]
        self._last_switch_time = time.time()

        # Per-lane light state for display purposes: "RED", "YELLOW", or "GREEN"
        self.lane_states = {}

        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for lane, pins in self.lane_pins.items():
                for pin in pins.values():
                    GPIO.setup(pin, GPIO.OUT)

        self._apply_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update(self, lane_counts):
        """
        Decide which lane gets green based on vehicle density.

        Args:
            lane_counts: Dict mapping lane names to vehicle counts.
                         Example: {"Lane 1": 3, "Lane 2": 7, "Lane 3": 0, "Lane 4": 2}

        Returns:
            str — name of the lane that currently has green
        """
        elapsed = time.time() - self._last_switch_time

        # Respect minimum green time
        if elapsed < self.min_green_time:
            return self.green_lane

        # Find the lane with the highest density
        max_count = -1
        priority_lane = self.green_lane  # Default: keep current if tied

        for lane in self.lane_names:
            count = lane_counts.get(lane, 0)
            if count > max_count:
                max_count = count
                priority_lane = lane

        # If all lanes are empty (max_count == 0), hold current green
        if max_count == 0:
            return self.green_lane

        # Switch only if a different lane has higher density
        if priority_lane != self.green_lane:
            self._transition(priority_lane)

        return self.green_lane

    def get_state_summary(self):
        """Returns a formatted string of all lane states for logging."""
        parts = []
        for lane in self.lane_names:
            state = self.lane_states.get(lane, "RED")
            parts.append(f"{lane}: {state:6s}")
        return " | ".join(parts)

    def cleanup(self):
        """Release GPIO resources."""
        if GPIO_AVAILABLE:
            GPIO.cleanup()
            print("[INFO] GPIO cleaned up.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _transition(self, new_green_lane):
        """
        Transition sequence:
          1. Current green lane → YELLOW (all others stay RED)
          2. Hold yellow for YELLOW_DURATION seconds
          3. Current green lane → RED
          4. New priority lane → GREEN
        """
        old_lane = self.green_lane

        # Step 1: Old green → Yellow
        self._set_lane_light(old_lane, "YELLOW")
        self._log_transition(f"{old_lane}: GREEN → YELLOW")
        time.sleep(self.yellow_duration)

        # Step 2: Old lane → Red, New lane → Green
        self._set_lane_light(old_lane, "RED")
        self.green_lane = new_green_lane
        self._set_lane_light(new_green_lane, "GREEN")
        self._last_switch_time = time.time()

        self._log_transition(f"{new_green_lane}: RED → GREEN  (highest density)")

    def _apply_state(self):
        """Set all lanes to RED except the current green lane."""
        for lane in self.lane_names:
            if lane == self.green_lane:
                self._set_lane_light(lane, "GREEN")
            else:
                self._set_lane_light(lane, "RED")

    def _set_lane_light(self, lane, color):
        """
        Set a specific lane to RED, YELLOW, or GREEN.
        Turns off the other two LEDs for that lane.
        """
        self.lane_states[lane] = color
        pins = self.lane_pins[lane]

        if GPIO_AVAILABLE:
            # Turn all three LEDs off for this lane first
            GPIO.output(pins["red"],    GPIO.LOW)
            GPIO.output(pins["yellow"], GPIO.LOW)
            GPIO.output(pins["green"],  GPIO.LOW)

            # Turn on the correct one
            if color == "RED":
                GPIO.output(pins["red"], GPIO.HIGH)
            elif color == "YELLOW":
                GPIO.output(pins["yellow"], GPIO.HIGH)
            elif color == "GREEN":
                GPIO.output(pins["green"], GPIO.HIGH)

    def _log_transition(self, message):
        """Print a formatted transition log."""
        print(f"[LIGHT] {message}  |  {self.get_state_summary()}")
