import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import logging
import re

app = Flask(__name__)

# Set the path to your Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Change this path

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set logging level to debug
app.logger.setLevel(logging.DEBUG)

# Function to check if file type is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from the image using Tesseract
def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()  # Remove leading/trailing whitespace
    except Exception as e:
        return str(e)

# Function to clean up and normalize the text (case insensitive, remove extra spaces and symbols)
def clean_text(text):
    text = text.lower()  # Convert text to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove non-alphanumeric characters (including slashes, dashes, etc.)
    return text.strip()

# Function to normalize DOB format (ensure it's in a consistent format like dd-mm-yyyy)
def normalize_dob_format(dob):
    # This assumes the format is dd/mm/yyyy or similar
    dob = re.sub(r'[^\d]', '', dob)  # Remove non-digit characters
    if len(dob) == 8:  # if we have 8 digits like 07012005
        return f"{dob[:2]}-{dob[2:4]}-{dob[4:]}"  # Convert to dd-mm-yyyy format
    return dob

@app.route('/', methods=['GET', 'POST'])
def upload_and_verify():
    app.logger.debug("Request method: %s", request.method)  # Log the request method
    
    if request.method == 'POST':
        app.logger.debug("POST request triggered")  # Confirm POST request is triggered
        
        # Get the uploaded files
        govt_id = request.files['govt_id']
        marks_card = request.files['marks_card']

        # Check if files are allowed
        if govt_id and allowed_file(govt_id.filename) and marks_card and allowed_file(marks_card.filename):
            app.logger.debug("Files are valid: %s, %s", govt_id.filename, marks_card.filename)  # Log valid file names
            
            # Save the files
            govt_id_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(govt_id.filename))
            marks_card_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(marks_card.filename))
            govt_id.save(govt_id_path)
            marks_card.save(marks_card_path)

            # Extract text from the uploaded images
            govt_id_text = extract_text_from_image(govt_id_path)
            marks_card_text = extract_text_from_image(marks_card_path)

            # Log the extracted text for debugging
            app.logger.debug("Extracted Govt ID text: %s", govt_id_text)
            app.logger.debug("Extracted Marks Card text: %s", marks_card_text)

            # Get the name and DOB entered by the user
            entered_name = request.form['name'].strip().lower()
            entered_dob = request.form['dob'].strip().lower()

            # Log entered name and DOB for debugging
            app.logger.debug("Entered Name: %s", entered_name)
            app.logger.debug("Entered DOB: %s", entered_dob)

            # Clean and normalize the extracted text and user input
            govt_id_text_cleaned = clean_text(govt_id_text)
            marks_card_text_cleaned = clean_text(marks_card_text)
            entered_name_cleaned = clean_text(entered_name)
            entered_dob_cleaned = clean_text(entered_dob)

            # Log cleaned text for debugging
            app.logger.debug("Cleaned Govt ID text: %s", govt_id_text_cleaned)
            app.logger.debug("Cleaned Marks Card text: %s", marks_card_text_cleaned)
            app.logger.debug("Cleaned Entered Name: %s", entered_name_cleaned)
            app.logger.debug("Cleaned Entered DOB: %s", entered_dob_cleaned)

            # Compare the cleaned text
            if entered_name_cleaned in govt_id_text_cleaned and entered_name_cleaned in marks_card_text_cleaned:
                name_match = True
            else:
                name_match = False

            if entered_dob_cleaned in govt_id_text_cleaned and entered_dob_cleaned in marks_card_text_cleaned:
                dob_match = True
            else:
                dob_match = False

            # If both name and DOB match, show success message; else, show failure
            if name_match and dob_match:
                verification_status = "Verification Successful: Documents Verified!"
                status_class = "success"  # CSS class for success
                app.logger.debug(verification_status)  # Log success
            else:
                verification_status = "Verification Failed: Name or DOB mismatch."
                status_class = "failure"  # CSS class for failure
                app.logger.debug(verification_status)  # Log failure

            return render_template('upload_verification.html', verification_status=verification_status, status_class=status_class)

        else:
            app.logger.debug("Files are either missing or invalid")  # Log if files are invalid or missing

    return render_template('upload_verification.html')


if __name__ == '__main__':
    app.run(debug=True)  # Run Flask app in debug mode
    app.logger.debug("Flask app started")  # Log when the Flask app starts
