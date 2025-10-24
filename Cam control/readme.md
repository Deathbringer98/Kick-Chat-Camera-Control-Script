# Kick Chat Camera Controller v1 (DSLR Ready)

This project allows you to control your camera through Kick.com chat messages in real time.  
Viewers can type commands such as `up`, `down`, `left`, and `right` in your chat to move the camera viewport or send movement signals to a servo or DSLR setup.

---

## Features

- Real-time Kick chat command listening  
- Works with:
  - Standard webcams (OpenCV)
  - OBS Virtual Cameras
  - Physical servo rigs (Arduino, Raspberry Pi, etc.)
  - DSLR cameras via gPhoto2  
- Optional Kick API token authentication  
- Anti-spam protection and automatic reconnection  

---

## Requirements

- Python 3.10 or newer
- One of the following camera setups:
  - USB or HDMI webcam
  - OBS Virtual Camera
  - DSLR with gPhoto2 installed
  - Servo-based camera rig (optional)
- Kick.com account for chat access

Install dependencies:

```bash
pip install opencv-python websocket-client
