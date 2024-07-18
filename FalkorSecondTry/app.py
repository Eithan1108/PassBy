from flask import Flask, request, jsonify, render_template
from PIL import Image
import os
import io
import base64
import time
import cv2
import numpy as np
import pytesseract
from CalcScore import query_car_details

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

image_log = []

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust this path for your system

def extract_license_plate(img):
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    custom_config = r'--oem 3 --psm 6 outputbase digits'

    # Perform text extraction
    text = pytesseract.image_to_string(gray, config='--psm 11')
    text = pytesseract.image_to_string(gray, config=custom_config)
    if text != '' and text[-1] == '\n':
        text = text[:-1]
    text = ''.join(filter(str.isdigit , text)) # filter out non-digits

    if text !='': print(text)
    return text

@app.route('/')
def upload_form():
    return render_template('camera.html')

@app.route('/upload_base64', methods=['POST'])
def upload_base64():
    if 'image' not in request.json:
        return jsonify({'error': 'No image data'}), 400
    image_data = request.json['image']
    try:
        # Decode base64 image data
        image_data = image_data.split(',')[1]  # Remove the data URL prefix
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Extract license plate
        license_plate = extract_license_plate(img)
        result = query_car_details(license_plate)


        # Save the image
        timestamp = int(time.time())
        #filename = f'image_{timestamp}.jpg'
        #cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], filename), img)

        # Log the image
        image_log.append({
            #'filename': filename,
            'license_plate': license_plate,
            'timestamp': timestamp,
            'result': result
        })

        return jsonify({
            "license_plate": license_plate,
            #"filename": filename
            'result': result
        })
    except Exception as e:
        print('Error',e)
        return jsonify({'error': str(e)}), 500

@app.route('/image_log')
def get_image_log():
    return jsonify(image_log)

if __name__ == '__main__':
    app.run(debug=True)