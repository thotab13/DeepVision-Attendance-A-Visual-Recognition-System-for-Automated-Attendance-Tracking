from flask import Flask, render_template, jsonify
import face_recognition
import pickle
import cv2
from imutils.video import VideoStream
import imutils
import time
import datetime
import os
from xlwt import Workbook
import threading
import json

app = Flask(__name__)

# Load the known faces and their encodings from the pickle file
known_faces_file = "facial_encodings.pkl"
with open(known_faces_file, "rb") as f:
    known_faces = pickle.load(f)

# Initialize some variables for face recognition
face_locations = []
face_names = []
video_stream = None
stop_recognition_flag = threading.Event()
recognizing_flag = False

def face_recognition_process():
    global face_locations, face_names, video_stream, recognizing_flag

    # Start the video stream
    video_stream = VideoStream(src=0).start()
    time.sleep(2.0)

    # Initialize the Excel workbook to save recognized names and timestamps
    workbook = Workbook()
    sheet = workbook.add_sheet("Recognitions")
    sheet.write(0, 0, "Name")
    sheet.write(0, 1, "Timestamp")

    # Start the recognition loop
    while not stop_recognition_flag.is_set():
        recognizing_flag = True
        # Capture frame-by-frame
        frame = video_stream.read()
        frame = imutils.resize(frame, width=500)

        # Convert the frame from BGR to RGB (for face_recognition library)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Find all face locations and face encodings in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # Match each face with the known faces
            matches = face_recognition.compare_faces(known_faces["encodings"], face_encoding)
            name = "Unknown"

            # If a match is found, use the name of the known face
            if True in matches:
                matched_indices = [i for i, matched in enumerate(matches) if matched]
                name = ", ".join([known_faces["names"][i] for i in matched_indices])

                # Save the recognized name and timestamp to the Excel sheet
                row = sheet.last_used_row + 1
                sheet.write(row, 0, name)
                sheet.write(row, 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            face_names.append(name)

        recognizing_flag = False

    # Save the Excel sheet and stop the video stream
    workbook.save("recognitions.xls")
    video_stream.stop()
    face_locations = []
    face_names = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_recognition', methods=['POST'])
def start_recognition():
    global recognizing_flag

    if not recognizing_flag:
        stop_recognition_flag.clear()
        threading.Thread(target=face_recognition_process).start()
        return jsonify({'message': 'Recognition started'})
    else:
        return jsonify({'message': 'Recognition already in progress'})

@app.route('/stop_recognition', methods=['POST'])
def stop_recognition():
    global stop_recognition_flag

    if video_stream is not None:
        stop_recognition_flag.set()
        return jsonify({'message': 'Recognition stopped'})
    else:
        return jsonify({'message': 'Recognition not running'})

@app.route('/current_recognition_status', methods=['GET'])
def current_recognition_status():
    global recognizing_flag
    return jsonify({'recognizing': recognizing_flag})

@app.route('/recognized_faces', methods=['GET'])
def recognized_faces():
    global face_locations, face_names
    return jsonify({'face_locations': face_locations, 'face_names': face_names})

if __name__ == "__main__":
    app.run(debug=True)
