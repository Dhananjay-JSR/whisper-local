from quart import Quart, request, jsonify
import os
import torch
import whisper
from werkzeug.utils import secure_filename
import librosa
import numpy as np
from bullmq import Queue,Job
import uuid

PORT = os.getenv("PORT", 5000)

app = Quart(__name__)

queue = Queue("myQueue")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload size (increased)

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
async def index():
    return '''
    <!doctype html>
    <title>Whisper Transcription Service</title>
    <h1>Upload an audio file for full transcription</h1>
    <form method=post action="/transcribe" enctype=multipart/form-data>
      <input type=file name=file accept=".mp3,.wav,.ogg,.m4a,.flac">
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/transcribe', methods=['POST'])
async def transcribe_audio():
    
    # Check if the post request has the file part
    
    files = await request.files
    
    if 'file' not in files:
        return jsonify({'error': 'No file part'}), 400
    
    file = files['file']

    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        await file.save(filepath)
        random_job_name = str(uuid.uuid4())
        job = await queue.add(random_job_name, {"filepath":filepath})
        return {
            'status': 'File is being processed',
            'job_id': job.id,
            'message': "Check Job Status with /status/<job_id>"
        }
        

    
    return jsonify({'error': 'File type not allowed'}), 400


@app.route('/status/<job_id>', methods=['GET'])
async def get_job_status(job_id):
    job = await Job.fromId(queue=queue, jobId=job_id)

    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    # Determine status solely from returnvalue
    if job.returnvalue is None:
        status = 'processing'
    else:
        status = 'completed'

    return jsonify({
        'id': job.id,
        'status': status,
        'result': job.returnvalue,
        'attemptsMade': job.attemptsMade,
        'failedReason': job.failedReason
    })

    
@app.after_serving
async def shutdown():
    """Called after the app stops serving."""
    print("Shutting down server, closing the queue...")
    await queue.close()

if __name__ == '__main__':

    
    print(f"Listening on port   {PORT}...")
    app.run(debug=False, host='0.0.0.0', port=PORT)