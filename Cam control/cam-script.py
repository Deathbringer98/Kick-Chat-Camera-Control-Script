"""
KICK CHAT CAMERA CONTROLLER v3 — DSLR READY
-------------------------------------------
Control OpenCV, OBS VirtualCam, Servo rigs, or DSLR cameras via Kick.com chat.
"""

import cv2
import websocket
import threading
import json
import time
import traceback
import sys
import subprocess
import os
import shutil
# =========================================================
# CONFIGURATION
# =========================================================
CONFIG = {
    "KICK_CHANNEL": "your_kick_channel_here",
    "KICK_API_TOKEN": "",            # Optional
    "CAMERA_TYPE": "opencv",         # "opencv", "virtualcam", "servo", or "dslr"
    "CAMERA_INDEX": 0,               # For opencv/virtualcam
    "DSLR_DRIVER": "gphoto2",        # Only used if CAMERA_TYPE="dslr"
    "MOVE_STEP": 25,
    "CROP_W": 640,
    "CROP_H": 480,
    "ANTISPAM_DELAY": 1.5
}

x, y = 0, 0
last_move = 0
running = True

# =========================================================
# CAMERA INITIALIZATION
# =========================================================
def init_camera():
    """Initialize based on camera type."""
    ctype = CONFIG["CAMERA_TYPE"]

    if ctype in ["opencv", "virtualcam"]:
        cam = cv2.VideoCapture(CONFIG["CAMERA_INDEX"])
        if not cam.isOpened():
            sys.exit("❌ Could not open camera. Try another CAMERA_INDEX.")
        print(f"✅ Using {ctype} camera (index {CONFIG['CAMERA_INDEX']})")
        return cam

    elif ctype == "servo":
        print("🦾 Servo mode enabled — connect your motor controller here.")
        return None

    elif ctype == "dslr":
        print("📷 DSLR mode enabled using gPhoto2 driver.")
        if not shutil.which("gphoto2"):
            sys.exit("❌ gPhoto2 not found. Install with: sudo apt install gphoto2")
        class DSLR:
            def capture(self):
                try:
                    subprocess.run(
                        ["gphoto2", "--capture-image-and-download", "--filename", "frame.jpg", "--force-overwrite"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    if os.path.exists("frame.jpg"):
                        frame = cv2.imread("frame.jpg")
                        return frame is not None, frame
                    return False, None
                except Exception as e:
                    print("⚠️ DSLR capture error:", e)
                    return False, None
        return DSLR()
    else:
        sys.exit("❌ Invalid CAMERA_TYPE.")

cam = init_camera()

# =========================================================
# CAMERA CONTROL
# =========================================================
def move_camera(direction, frame=None):
    global x, y, last_move
    now = time.time()
    if now - last_move < CONFIG["ANTISPAM_DELAY"]:
        return
    last_move = now

    print(f"📡 Command: {direction}")
    ctype = CONFIG["CAMERA_TYPE"]

    if ctype in ["opencv", "virtualcam", "dslr"]:
        if frame is None:
            return
        h, w, _ = frame.shape
        if direction == "left":  x = max(0, x - CONFIG["MOVE_STEP"])
        if direction == "right": x = min(w - CONFIG["CROP_W"], x + CONFIG["MOVE_STEP"])
        if direction == "up":    y = max(0, y - CONFIG["MOVE_STEP"])
        if direction == "down":  y = min(h - CONFIG["CROP_H"], y + CONFIG["MOVE_STEP"])
        print(f"➡️ New crop: x={x}, y={y}")

    elif ctype == "servo":
        print(f"🦾 Move servo: {direction}")
        # TODO: send command via serial here

# =========================================================
# KICK CHAT HANDLER
# =========================================================
def on_message(ws, message):
    global running
    try:
        data = json.loads(message)
        msg = str(data.get("data", {}).get("content", "")).lower()

        if any(cmd in msg for cmd in ["left", "right", "up", "down"]):
            if CONFIG["CAMERA_TYPE"] == "dslr":
                ret, frame = cam.capture()
            elif CONFIG["CAMERA_TYPE"] in ["opencv", "virtualcam"]:
                ret, frame = cam.read()
            else:
                ret, frame = (True, None)
            if ret:
                move_camera(msg.strip(), frame)
        elif "quit" in msg:
            print("🛑 Quit command received.")
            running = False
    except Exception:
        traceback.print_exc()

def on_error(ws, error):
    print("⚠️ WebSocket error:", error)

def on_close(ws, code, msg):
    print("❌ Disconnected. Reconnecting in 5s...")
    time.sleep(5)
    start_websocket()

def on_open(ws):
    print(f"✅ Connected to Kick chat for '{CONFIG['KICK_CHANNEL']}'")

def start_websocket():
    headers = []
    if CONFIG["KICK_API_TOKEN"]:
        headers.append(f"Authorization: Bearer {CONFIG['KICK_API_TOKEN']}")
    ws = websocket.WebSocketApp(
        f"wss://chat.kick.com/ws?name={CONFIG['KICK_CHANNEL']}",
        header=headers,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()

threading.Thread(target=start_websocket, daemon=True).start()

# =========================================================
# MAIN LOOP
# =========================================================
while running:
    ctype = CONFIG["CAMERA_TYPE"]

    if ctype in ["opencv", "virtualcam"]:
        ret, frame = cam.read()
    elif ctype == "dslr":
        ret, frame = cam.capture()
    else:
        ret, frame = (False, None)

    if ret and frame is not None:
        crop = frame[y:y+CONFIG["CROP_H"], x:x+CONFIG["CROP_W"]]
        cv2.imshow("Kick Camera Control", crop)
    elif ctype == "servo":
        time.sleep(0.1)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("🧹 Exiting manually.")
        break

if cam and CONFIG["CAMERA_TYPE"] in ["opencv", "virtualcam"]:
    cam.release()
cv2.destroyAllWindows()
running = False
print("✅ Session ended.")
