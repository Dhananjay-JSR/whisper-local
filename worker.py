import os
import whisper
import torch
import librosa
from bullmq import Worker
import asyncio
import signal

from download_whisper import get_model_size_based_on_hardware

MODEL = None
MODEL_SIZE = None

def format_duration(seconds):
    if seconds is None or seconds == 0:
        return "Unknown"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"


async def transcribe_file(job, job_token):
    global MODEL, MODEL_SIZE
    print(f"Transcribing file: {job.id}")
    print(f"Job token: {job_token}")
    print(f"Job data: {job.data}")
    filepath = job.data.get("filepath")
    if not filepath or not os.path.isfile(filepath):
        raise FileNotFoundError("Audio file not found.")
    print(f"Transcribing file: {filepath}")
    try:
        if MODEL is None:
            if MODEL_SIZE is None:
                MODEL_SIZE = get_model_size_based_on_hardware()
            print(f"Loading Whisper model: {MODEL_SIZE}")
            MODEL = whisper.load_model(MODEL_SIZE)

        try:
            y, sr = librosa.load(filepath, sr=None)
            audio_duration = librosa.get_duration(y=y, sr=sr)
        except Exception:
            audio_duration = None

        result = MODEL.transcribe(filepath, task="transcribe", fp16=torch.cuda.is_available())

        if result.get('duration', 0) == 0 and 'segments' in result and result['segments']:
            last_segment = result['segments'][-1]
            if 'end' in last_segment:
                result['duration'] = last_segment['end']
            if result.get('duration', 0) == 0 and audio_duration:
                result['duration'] = audio_duration

        duration_seconds = result.get('duration', 0)
        os.remove(filepath)
        return {
            'content': result['text'],
            'type': result['language'],
            'segments': len(result.get('segments', [])),
            'duration': {
                'seconds': duration_seconds,
                'formatted': format_duration(duration_seconds)
            },
            'segment_info': [
                {
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                } for seg in result.get('segments', [])
            ]
        }

    except Exception as e:
        print(f"Transcription error: {str(e)}")
        return {'error': str(e)}


async def main():
    global MODEL, MODEL_SIZE

    MODEL_SIZE = get_model_size_based_on_hardware()
    MODEL = whisper.load_model(MODEL_SIZE)

    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("Shutdown signal received.")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    print("Worker is starting...")
    worker = Worker("myQueue", transcribe_file, {})

    await shutdown_event.wait()

    print("Closing worker...")
    await worker.close()
    print("Worker closed.")

if __name__ == "__main__":
    asyncio.run(main())