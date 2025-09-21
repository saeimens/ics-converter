# This is the main application file for Replit
import io
from flask import Flask, render_template, request, send_file

# --- The Core Conversion Logic ---
def convert_ics_content(original_content):
    """
    Takes the text content of an Abaplan ICS file and converts it 
    to be Google Calendar compatible.
    """
    lines = original_content.splitlines()
    converted_lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//ICS-Converter-for-Abacus//EN',
        'CALSCALE:GREGORIAN'
    ]
    in_event = False
    current_event_buffer = []

    for line in lines:
        trimmed_line = line.strip()
        if trimmed_line == 'BEGIN:VEVENT':
            in_event = True
            current_event_buffer = [trimmed_line]
        elif trimmed_line == 'END:VEVENT':
            in_event = False
            processed_event = process_event_block(current_event_buffer)
            converted_lines.extend(processed_event)
            converted_lines.append(trimmed_line)
        elif in_event:
            current_event_buffer.append(trimmed_line)

    converted_lines.append('END:VCALENDAR')
    return "\r\n".join(converted_lines)

def process_event_block(event_lines):
    """Processes a single VEVENT block to clean it for Google Calendar."""
    processed_lines = []
    description = ''

    # Find the description content from the non-standard field
    for line in event_lines:
        if line.startswith('X-ALT-DESC'):
            parts = line.split(':', 1)
            if len(parts) > 1:
                description = parts[1]

    # Build the new event with only the fields Google Calendar needs
    for line in event_lines:
        if any(line.startswith(p) for p in ['DTSTART', 'DTEND', 'SUMMARY', 'UID', 'DTSTAMP', 'BEGIN:VEVENT']):
            processed_lines.append(line)

    # Add the standard DESCRIPTION field if content was found
    if description:
        # Escape special characters as required by the ICS format
        escaped = description.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')
        processed_lines.append(f"DESCRIPTION:{escaped}")

    return processed_lines

# --- The Web Application Setup ---
app = Flask(__name__)

@app.route('/')
def index():
    """Serves the main upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles the file upload and returns the converted file."""
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and file.filename.endswith('.ics'):
        original_content = file.stream.read().decode("utf-8")
        converted_content = convert_ics_content(original_content)
        buffer = io.BytesIO(converted_content.encode("utf-8"))
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name='google_compatible_calendar.ics',
            mimetype='text/calendar'
        )
    else:
        return "Invalid file type. Please upload a .ics file.", 400

# This command runs the web server.
app.run(host='0.0.0.0', port=81)
