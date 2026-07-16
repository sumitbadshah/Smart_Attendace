# Smart Attendance System (v2)

A Python-based face recognition attendance system with a PyQt5 GUI.
This version replaces the original custom pixel-comparison recognizer with
a deep-learning face embedding model, and fixes several bugs found during
code review.

## What changed from v1

| # | Issue in v1 | Fix in v2 |
|---|---|---|
| 1 | Registering a new face didn't take effect until you manually clicked "Train Model" | New encodings are added to the live in-memory model at registration time — recognized on the very next frame |
| 2 | Only one image was captured per person | Registration now captures 5 samples across ~2 seconds so lighting/angle variation is baked in |
| 3 | "Confidence" was actually an uncalibrated pixel-MSE value where *lower* was better, divided by an arbitrary `/10` | Replaced with `face_recognition`'s calibrated distance metric, converted to a real 0–100% confidence score where higher is always better |
| 4 | Every detected face was compared against the entire roster with a resize + full pixel MSE, on every ~20ms tick | Faces are now 128-d embeddings compared with one vectorized numpy operation; detection/recognition also only runs every 3rd frame instead of every frame |
| 5 | Attendance de-duplication was keyed on name, so two people with the same name would collide | Keyed on `face_id` instead, which is guaranteed unique |
| Core engine | Haar Cascade + raw-pixel similarity comparison | `face_recognition` (dlib ResNet-based deep metric learning) — far more robust to lighting, angle, and partial occlusion |

## Features

- Real-time face detection and recognition (`face_recognition` / dlib)
- Multi-sample registration for better accuracy per person
- Automatic model update on registration — no manual retrain step needed
- SQLite database for face encodings and attendance records
- PyQt5 GUI with live camera feed and attendance log
- Attendance history viewer

## Requirements

```
pip install -r requirements.txt
```

**Note on `dlib`:** it builds from C++ source and needs `cmake` and a C++
compiler available on your system.

- **macOS:** `brew install cmake`
- **Ubuntu/Debian:** `sudo apt install cmake build-essential`
- **Windows:** install "Desktop development with C++" via the Visual Studio
  Build Tools, plus [cmake.org](https://cmake.org/download/)

If the build is too slow for a hackathon deadline, `pip install dlib-binary`
or a prebuilt wheel for your platform/Python version can save time — check
what's available for your OS before the demo, not during it.

## Running

```
python attendance_system.py
```

1. Click **Start** to begin the camera feed.
2. Click **Register Face**, enter a name (and optional ID), then click
   **Start Capture**. Hold still and move your head slightly between the
   5 samples it captures.
3. The person is recognized immediately — no separate training step.
4. Attendance is marked automatically (once per person per day) when a
   recognized face appears on camera.
5. Use **View Attendance Records** to see the full history.

**Rebuild Model from DB** is only needed if you've edited the database
outside the app; normal registration keeps the live model in sync on its own.

## Known limitations / suggested next steps

These were flagged in the original review and are still open — scoped out
of this bug-fix pass to keep it focused, but worth doing before a judged demo:

- **No liveness/anti-spoofing check.** A printed photo or phone screen could
  currently pass. A blink-detection or "turn your head" challenge would close
  this gap.
- **Single file, single machine, SQLite.** Fine for a hackathon demo. For a
  multi-user deployment, split into `face_processor.py` / `database.py` /
  `gui.py` / `main.py`, move to a hosted Postgres/MySQL instance, and expose
  core functions via a REST API (Flask/FastAPI) so the PyQt5 GUI becomes just
  one client among possible web/mobile frontends.
- **No packaging.** A `Dockerfile` or `setup.py` would make this reproducible
  with one command, which judges tend to reward.
- **Registration capture blocks the UI thread briefly** (using
  `QApplication.processEvents()` to stay responsive during the ~2 second
  multi-sample capture). A dedicated `QThread` would be a more robust fix if
  you have time.
