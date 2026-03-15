import os
import json
from typing import List, Dict

WHISPER_MODEL_PATH = os.path.join("models", "whisper-large-v2")
VOSK_MODEL_PATH = os.path.join("models", "vosk-model-small-cn-0.22")

whisper_model = None
vosk_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...")
        r"""
        Will automatically fetch pytorch_model.bin and other files from Hugging Face 
        (https://huggingface.co/openai/whisper-large-v2/tree/main).
        Stored in the cache folder:
        Windows: C:\Users\<YourUser>\.cache\huggingface\transformers
        """
        # --- Whisper imports ---
        try:
            from faster_whisper import WhisperModel
            whisper_model = WhisperModel("large-v2", device="cuda")  # try GPU
        except RuntimeError:
            print("CUDA not available, falling back to CPU for transcription.")
            whisper_model = WhisperModel("large-v2", device="cpu")  # fallback to CPU
        except ImportError:
            print("Faster-Whisper library not available. Please install with `pip install faster-whisper`.")
    return whisper_model


def get_vosk_model():
    global vosk_model
    if vosk_model is None:
        print("Loading Vosk model...")
        try:
            from vosk import Model as VoskModel
            vosk_model = VoskModel(VOSK_MODEL_PATH)
        except ImportError:
            print("Vosk library not available. Please install with `pip install vosk`.")
    return vosk_model


def transcribe_whisper(video_file: str) -> List[Dict]:
    """
    Extract audio from video and transcribe using Whisper/Faster-Whisper.
    Returns list of segments: [{'start': float, 'end': float, 'text': str}]
    """
    from moviepy.video.io.VideoFileClip import VideoFileClip
    import tempfile

    whisper_model = get_whisper_model()
    if whisper_model is None:
        raise RuntimeError("Whisper model not loaded.")

    # Extract audio to temp WAV
    with VideoFileClip(video_file) as clip:
        tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_audio.close()  # <-- important, release handle
        clip.audio.write_audiofile(tmp_audio.name, fps=16000, nbytes=2, codec='pcm_s16le')

    # Transcribe
    segments = []
    segments_gen, _ = whisper_model.transcribe(tmp_audio.name, beam_size=5)
    for segment in segments_gen:
        text = segment.text.strip()
        if text:
            segments.append({'start': segment.start, 'end': segment.end, 'text': text})

    os.unlink(tmp_audio.name)
    return segments


def transcribe_vosk(audio_file: str) -> List[Dict]:
    """
    Transcribe WAV audio using Vosk (CPU).
    """
    vosk_model = get_vosk_model()
    if vosk_model is None:
        raise RuntimeError("Vosk model not loaded.")

    import wave
    from vosk import KaldiRecognizer
    wf = wave.open(audio_file, "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)
    segments = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            if 'result' in res:
                words = res['result']
                if words:
                    start = words[0]['start']
                    end = words[-1]['end']
                    text = ' '.join([w['word'] for w in words])
                    segments.append({'start': start, 'end': end, 'text': text})

    # Final partial result
    res = json.loads(rec.FinalResult())
    if 'result' in res:
        words = res['result']
        if words:
            start = words[0]['start']
            end = words[-1]['end']
            text = ' '.join([w['word'] for w in words])
            segments.append({'start': start, 'end': end, 'text': text})

    wf.close()
    return segments


def transcribe_video(video_file: str, backend: str = "whisper") -> List[Dict]:
    """
    Main entry point. Chooses backend: 'whisper' (default) or 'vosk'.
    Return list of segments as:
    [
        {'start': 0.0, 'end': 5.3, 'text': "Hello everyone"},
        {'start': 5.3, 'end': 10.7, 'text': "Welcome to the demo"}
    ]
    """
    from moviepy.video.io.VideoFileClip import VideoFileClip
    import tempfile

    if backend == "whisper":
        return transcribe_whisper(video_file)
    elif backend == "vosk":
        # extract audio first
        with VideoFileClip(video_file) as clip:
            tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            clip.audio.write_audiofile(tmp_audio.name, fps=16000, nbytes=2, codec='pcm_s16le')
        segments = transcribe_vosk(tmp_audio.name)
        os.unlink(tmp_audio.name)
        return segments
    else:
        raise ValueError("Unknown backend, must be 'whisper' or 'vosk'.")