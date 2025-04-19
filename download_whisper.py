import os
import subprocess
import whisper
import torch
from utils import get_model_size_based_on_hardware

def download_whisper_if_not_available(model_name="base"):
    try:
        import whisper
        print("Whisper is installed.")
    except ImportError:
        print("Installing Whisper...")
        subprocess.check_call(["pip", "install", "-U", "openai-whisper"])

    whisper_model_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    if not os.path.exists(whisper_model_dir) or not any(f.startswith(model_name) for f in os.listdir(whisper_model_dir)):
        print(f"Downloading Whisper model: {model_name}")
        _ = whisper.load_model(model_name)
    else:
        print(f"Whisper model {model_name} already present.")

if __name__ == "__main__":
    size = get_model_size_based_on_hardware()
    download_whisper_if_not_available(size)
