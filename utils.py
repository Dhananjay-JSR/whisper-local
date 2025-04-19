import torch

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp3', 'wav', 'ogg', 'm4a', 'flac'}

def get_model_size_based_on_hardware():
    if torch.cuda.is_available():
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if gpu_mem > 10:
            return "medium"
        elif gpu_mem > 6:
            return "small"
    return "base"

def format_duration(seconds):
    if seconds is None or seconds == 0:
        return "Unknown"
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
