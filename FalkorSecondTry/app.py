from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image
import os
import io
import base64
import time
import cv2
import numpy as np
import pytesseract
from CalcScore import query_car_details  # Ensure this import is correct and the function is available
import threading

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Save frame to disk
FRAME_FILENAME = os.path.join(UPLOAD_FOLDER, f'frame.jpg')

image_log = []

lock = threading.Lock()

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust this path for your system

def extract_license_plate(img):
    try:
        custom_config = r'--oem 3 --psm 6 outputbase digits'

        # Perform text extraction
        text = pytesseract.image_to_string(img, config=custom_config)
        text = ''.join(filter(str.isdigit, text))  # Filter out non-digits

        if text:
            print(f"Detected license plate: {text}")
        return text
    except Exception as e:
        print(f"Error in extracting license plate: {e}")
        return ""

def capture_rtsp_stream(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print('No camera')
        return
    print('yes camera')

    while True:
        ret, frame = cap.read()
        if not ret:
            print('Failed to read from camera')
            break

        # Cut the first 30 lines of pixels and the last 50 lines - they contain text and are not needed
        frame = frame[30:-50, :]

        #frame = cv2.threshold(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 50, 200, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        with lock:
            cv2.imwrite(FRAME_FILENAME, frame)

        # Display the frame for debugging purposes (optional)
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

@app.route('/')
def upload_form():
    return render_template('camera.html')

@app.route('/upload_base64', methods=['POST'])
def upload_base64():
    try:
        with lock:
            img = cv2.imread(FRAME_FILENAME)
        _, buffer = cv2.imencode('.jpg', img)
        image_data = f'data:image/jpeg;base64,{base64.b64encode(buffer).decode()}'

        # Extract license plate
        license_plate = extract_license_plate(img)
        if not license_plate:
            return jsonify({'error': 'License plate not detected'}), 434

        result = query_car_details(license_plate)

        # Save the image
        timestamp = int(time.time())

        # Log the image
        image_log.append({
            'license_plate': license_plate,
            'timestamp': timestamp,
            'result': result,
            'img': image_data
        })

        return jsonify({
            "license_plate": license_plate,
            'result': result
        })
    except Exception as e:
        print(f"Error during image processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/image_log')
def get_image_log():
    return jsonify(image_log)

@app.route('/uploads/<filename>')
def send_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/display_images')
def display_images():
    image_files = os.listdir(UPLOAD_FOLDER)
    image_urls = [f'/uploads/{filename}' for filename in image_files]
    return render_template('display_images.html', image_urls=image_urls)

if __name__ == '__main__':
    rtsp_url = 'rtsp://123456:123456@192.168.84.252/stream2'
    # Start the RTSP stream in a separate thread
    threading.Thread(target=capture_rtsp_stream, args=(rtsp_url,), daemon=True).start()
    app.run(debug=True)
