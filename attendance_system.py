
import sys
import cv2
import numpy as np
import sqlite3
import datetime
import os
import pickle
import time

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                              QVBoxLayout, QHBoxLayout, QWidget,
                              QTableWidget, QTableWidgetItem, QLineEdit,
                              QMessageBox, QDialog, QTextEdit, QProgressBar)

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False



MATCH_THRESHOLD = 0.6          
                                
                                
SAMPLES_PER_REGISTRATION = 5   
REGISTRATION_SAMPLE_DELAY = 0.4  
DETECT_EVERY_N_FRAMES = 3      
FRAME_RESIZE_SCALE = 0.5      
TIMER_INTERVAL_MS = 30         


class FaceEncoder:


    def __init__(self):
        self.known_encodings = []   
        self.known_face_ids = []    
        self.label_names = {}      

    def add_encoding(self, encoding, face_id, name):
        
        self.known_encodings.append(encoding)
        self.known_face_ids.append(face_id)
        self.label_names[face_id] = name

    def train(self, encodings, face_ids, label_names):
        
        self.known_encodings = list(encodings)
        self.known_face_ids = list(face_ids)
        self.label_names = dict(label_names)

    def predict(self, encoding):
       
        if not self.known_encodings:
            return None, 0.0

        distances = face_recognition.face_distance(self.known_encodings, encoding)
        best_idx = int(np.argmin(distances))
        best_distance = float(distances[best_idx])

        if best_distance <= MATCH_THRESHOLD:
            confidence = max(0.0, (1.0 - best_distance)) * 100.0
            return self.known_face_ids[best_idx], confidence
        return None, 0.0


class FaceRegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Face")
        self.setModal(True)
        self.setFixedSize(420, 220)

        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter person's name")
        layout.addWidget(self.name_input)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter ID (optional)")
        layout.addWidget(self.id_input)

        layout.addWidget(QLabel(
            f"Will capture {SAMPLES_PER_REGISTRATION} samples - "
            "move your head slightly between shots."
        ))

        button_layout = QHBoxLayout()
        self.capture_btn = QPushButton("Start Capture")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.capture_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.capture_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)


class AttendanceSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Attendance System (v2)")
        self.setGeometry(100, 100, 1000, 700)

        if not FACE_RECOGNITION_AVAILABLE:
            QMessageBox.critical(
                self, "Missing dependency",
                "The 'face_recognition' package is not installed.\n\n"
                "Install it with:\n"
                "    pip install face_recognition\n\n"
                "(This requires dlib, which needs cmake + a C++ compiler "
                "to build. See README.md for platform-specific notes.)"
            )

        self.recognizer = FaceEncoder()
        self.init_database()
        self.model_trained = False
        self.load_trained_model()

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            for i in range(1, 5):
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    break

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_capturing = False
        self.current_frame = None

        # Performance: cache last detection result and only recompute every
        # DETECT_EVERY_N_FRAMES ticks instead of on every single frame.
        self._frame_counter = 0
        self._last_face_boxes = []       # [(x, y, w, h), ...] in full-frame coords
        self._last_face_labels = []      # [(name, confidence), ...] parallel list

        self.attendance_marked = set()   # keyed by f"{face_id}_{date}" (BUG 5 fix)

        self.init_ui()

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    def init_database(self):
        self.conn = sqlite3.connect('attendance.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                face_id TEXT,
                encoding BLOB,
                image BLOB
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                face_id TEXT,
                name TEXT,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def load_trained_model(self):
        """Bulk-load every stored encoding into the in-memory recognizer.

        Only needed on startup now - registration no longer depends on this
        being re-run (see FaceEncoder.add_encoding).
        """
        try:
            self.cursor.execute("SELECT face_id, name, encoding FROM faces")
            rows = self.cursor.fetchall()
            if not rows:
                return

            encodings, face_ids, label_names = [], [], {}
            for face_id, name, enc_blob in rows:
                if enc_blob is None:
                    continue  # skip legacy rows saved before this upgrade
                encoding = pickle.loads(enc_blob)
                encodings.append(encoding)
                face_ids.append(face_id)
                label_names[face_id] = name

            self.recognizer.train(encodings, face_ids, label_names)
            self.model_trained = len(encodings) > 0
        except Exception as e:
            print(f"Error loading trained model: {e}")
            self.model_trained = False

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("border: 1px solid black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        if not self.cap.isOpened():
            self.video_label.setText("Webcam not available\nPlease check your camera connection")
        else:
            self.video_label.setText("Webcam Feed\nClick Start to begin")
        left_layout.addWidget(self.video_label)

        self.status_label = QLabel("Status: Not started")
        left_layout.addWidget(self.status_label)

        self.capture_progress = QProgressBar()
        self.capture_progress.setVisible(False)
        left_layout.addWidget(self.capture_progress)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.register_btn = QPushButton("Register Face")
        self.train_btn = QPushButton("Rebuild Model from DB")
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.register_btn)
        control_layout.addWidget(self.train_btn)
        right_layout.addLayout(control_layout)

        right_layout.addWidget(QLabel("Attendance Log:"))
        self.attendance_log = QTextEdit()
        self.attendance_log.setReadOnly(True)
        right_layout.addWidget(self.attendance_log)

        self.view_records_btn = QPushButton("View Attendance Records")
        right_layout.addWidget(self.view_records_btn)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        self.start_btn.clicked.connect(self.start_capture)
        self.stop_btn.clicked.connect(self.stop_capture)
        self.register_btn.clicked.connect(self.register_face)
        self.train_btn.clicked.connect(self.rebuild_model_from_db)
        self.view_records_btn.clicked.connect(self.view_attendance_records)

        self.stop_btn.setEnabled(False)
        if not self.cap.isOpened() or not FACE_RECOGNITION_AVAILABLE:
            self.start_btn.setEnabled(False)
            self.register_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Camera controls
    # ------------------------------------------------------------------
    def start_capture(self):
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Error", "Webcam is not available")
            return
        self.is_capturing = True
        self.timer.start(TIMER_INTERVAL_MS)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Running")

    def stop_capture(self):
        self.is_capturing = False
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")

    # ------------------------------------------------------------------
    # Main video loop
    # ------------------------------------------------------------------
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        self.current_frame = frame.copy()
        self._frame_counter += 1

        # Performance fix (BUG 4): only run detection + recognition every
        # Nth tick. In between ticks we just redraw the last known boxes,
        # so the video still looks smooth (~33fps) but the expensive work
        # only happens ~10x/second instead of ~50x/second.
        if self._frame_counter % DETECT_EVERY_N_FRAMES == 0:
            self._detect_and_recognize(frame)

        self._draw_overlays(frame)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def _detect_and_recognize(self, frame):
        """Detect faces on a downscaled frame (fast), then recognize each
        against the in-memory encodings with a single vectorized comparison.
        """
        small_frame = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE_SCALE, fy=FRAME_RESIZE_SCALE)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        boxes = []
        labels = []
        scale = 1.0 / FRAME_RESIZE_SCALE

        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            # scale coordinates back up to the full-size frame
            top, right, bottom, left = (int(top * scale), int(right * scale),
                                         int(bottom * scale), int(left * scale))
            x, y, w, h = left, top, right - left, bottom - top
            boxes.append((x, y, w, h))

            if self.model_trained:
                face_id, confidence = self.recognizer.predict(encoding)
                if face_id is not None:
                    name = self.recognizer.label_names.get(face_id, "Unknown")
                    labels.append((name, confidence))
                    self._maybe_mark_attendance(face_id, name)
                else:
                    labels.append(("Unknown", 0.0))
            else:
                labels.append(("Model not trained", 0.0))

        self._last_face_boxes = boxes
        self._last_face_labels = labels

    def _draw_overlays(self, frame):
        for (x, y, w, h), (name, confidence) in zip(self._last_face_boxes, self._last_face_labels):
            is_recognized = name not in ("Unknown", "Model not trained")
            box_color = (255, 0, 0) if is_recognized else (0, 0, 255)
            text_color = (36, 255, 12) if is_recognized else (0, 0, 255)

            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
            label = f"{name} ({confidence:.0f}%)" if is_recognized else name
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, text_color, 2)

    def _maybe_mark_attendance(self, face_id, name):
        today = datetime.date.today().strftime("%Y-%m-%d")
        key = f"{face_id}_{today}"          # BUG 5 fix: keyed on face_id, not name
        if key not in self.attendance_marked:
            self.mark_attendance(face_id, name)
            self.attendance_marked.add(key)

    def mark_attendance(self, face_id, name):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO attendance (face_id, name, timestamp) VALUES (?, ?, ?)",
            (face_id, name, timestamp)
        )
        self.conn.commit()
        self.attendance_log.append(f"{timestamp} - {name} marked present")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_face(self):
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Warning", "Please start the camera first")
            return

        dialog = FaceRegistrationDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        name = dialog.name_input.text().strip()
        face_id = dialog.id_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a name")
            return
        if not face_id:
            face_id = f"{name}_{int(time.time())}"

        # BUG 2 fix: capture multiple samples instead of a single frame.
        self.capture_progress.setVisible(True)
        self.capture_progress.setMinimum(0)
        self.capture_progress.setMaximum(SAMPLES_PER_REGISTRATION)
        self.capture_progress.setValue(0)

        captured = 0
        attempts = 0
        max_attempts = SAMPLES_PER_REGISTRATION * 4  # allow retries for missed detections

        while captured < SAMPLES_PER_REGISTRATION and attempts < max_attempts:
            attempts += 1
            ret, frame = self.cap.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")

            if len(locations) == 0:
                self.status_label.setText(
                    f"Status: No face detected, retrying... ({captured}/{SAMPLES_PER_REGISTRATION})"
                )
                QApplication.processEvents()
                time.sleep(REGISTRATION_SAMPLE_DELAY)
                continue

            encodings = face_recognition.face_encodings(rgb, locations)
            encoding = encodings[0]
            top, right, bottom, left = locations[0]
            face_crop = frame[top:bottom, left:right]

            ret2, buffer = cv2.imencode('.jpg', face_crop)
            image_blob = buffer.tobytes() if ret2 else None

            self.cursor.execute(
                "INSERT INTO faces (name, face_id, encoding, image) VALUES (?, ?, ?, ?)",
                (name, face_id, pickle.dumps(encoding), image_blob)
            )
            self.conn.commit()

            # BUG 1 fix: update the in-memory model immediately - no separate
            # "Train Model" click required before this person is recognized.
            self.recognizer.add_encoding(encoding, face_id, name)
            self.model_trained = True

            captured += 1
            self.capture_progress.setValue(captured)
            self.status_label.setText(
                f"Status: Captured {captured}/{SAMPLES_PER_REGISTRATION} - move your head slightly"
            )
            QApplication.processEvents()
            time.sleep(REGISTRATION_SAMPLE_DELAY)

        self.capture_progress.setVisible(False)
        self.status_label.setText("Status: Running" if self.is_capturing else "Status: Not started")

        if captured == 0:
            QMessageBox.warning(self, "Warning",
                                 "No face could be captured. Make sure your face is "
                                 "clearly visible and well-lit, then try again.")
        else:
            QMessageBox.information(
                self, "Success",
                f"Registered {captured} sample(s) for {name} (ID: {face_id}).\n"
                "They can be recognized immediately - no retraining needed."
            )

    def rebuild_model_from_db(self):
        """Manual full reload from the database. No longer required for normal
        use (registration keeps the in-memory model in sync automatically),
        but useful if the database was edited outside the app.
        """
        self.load_trained_model()
        count = len(self.recognizer.known_encodings)
        if count == 0:
            QMessageBox.warning(self, "Warning", "No faces registered in the database")
        else:
            QMessageBox.information(self, "Success", f"Model rebuilt with {count} face sample(s)")

    # ------------------------------------------------------------------
    # Records
    # ------------------------------------------------------------------
    def view_attendance_records(self):
        records_dialog = QDialog(self)
        records_dialog.setWindowTitle("Attendance Records")
        records_dialog.setModal(True)
        records_dialog.setFixedSize(600, 400)

        layout = QVBoxLayout()
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Date", "Time"])

        self.cursor.execute("SELECT name, timestamp FROM attendance ORDER BY timestamp DESC")
        records = self.cursor.fetchall()
        table.setRowCount(len(records))

        for row, record in enumerate(records):
            name, timestamp = record
            date, time_ = timestamp.split(' ')
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(date))
            table.setItem(row, 2, QTableWidgetItem(time_))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(records_dialog.accept)
        layout.addWidget(close_btn)

        records_dialog.setLayout(layout)
        records_dialog.exec_()

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AttendanceSystem()
    window.show()
    sys.exit(app.exec_())
