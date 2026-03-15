# VidSearch

A command-line tool for transcribing video/audio files and searching through their transcripts. Primarily uses Faster-Whisper for high-quality transcription, with Vosk as a fallback option. You can use this tool to build a searchable movie/video database where you can find any spoken phrase and jump directly to it.

## Features

- **Video Indexing**: Add individual videos or entire folders of videos to a local SQLite database
- **Automatic Transcription**: Extract audio and transcribe to text using Faster-Whisper (GPU/CPU) or Vosk
- **Full-Text Search**: Search through video filenames or transcript content with paginated results
- **Segment Playback**: Open specific transcript segments directly in a video player at the exact timestamp
- **Full Language Support**: Faster-Whisper (large-v2) supports almost all languages.

## Project Structure

```
vidsearch/
│
├── core/
│   ├── db.py          # SQLite database operations and queries
│   ├── indexer.py     # Transcript indexing and storage
│   ├── search.py      # Search utilities with pagination
│   └── transcribe.py  # Audio/video transcription (Whisper/Vosk)
│
├── models/            # Pre-trained speech recognition models (Optional, you could download yourself as needed)
├── cli.py             # Command-line interface
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Installation

1. **Clone or download the project**
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```
3. **Download models**:
   - Faster-Whisper automatically downloads the Whisper model on first use
   - (Optional) You can download Vosk models in the `models/` directory if you prefer the lightweight, fast model
4. **Install**:
   ```bash
   pip install -e .
   ```

## Usage

### Interactive Mode
```bash
vidsearch interactive
```
In this mode, you can run all the commands below in a consistent session without `vidsearch` prefix. Type `exit` to exit this mode. e.g.
```bash
vidsearch interactive
add "video.mp4" --use-vosk
search_segment "quantum computing"
exit
```

### Add Videos
Add a single video:
```bash
vidsearch add "path/to/video1.mp4" 
```

Add all videos from a folder (recursive):
```bash
vidsearch add "path/to/folder/"
```

### Search Videos
Search videos by filename:
```bash
vidsearch search_video "keyword"
```

### Search Transcripts
Search through transcript content:
```bash
vidsearch search_segment "keyword"
```

### List Videos
List all indexed videos:
```bash
vidsearch list_videos
```

### List Transcripts
List transcripts for a specific video:
```bash
vidsearch list_transcripts --video-id 1
```

### Open Segment
Open a transcript segment in video player:
```bash
vidsearch open_segment --segment_id 123
```

### Remove Video
Remove a video and its transcripts:
```bash
vidsearch remove --video-id 1
```

## Transcription Backends

- **Primary**: Faster-Whisper (`large-v2` model) - High accuracy, supports GPU acceleration
- **Fallback**: Vosk - CPU-only, faster for offline use

The system defaults to Whisper. To use Vosk, download the model (e.g., `vosk-model-small-en-us-0.15`) and place it under `models/vosk/`. Then run:
```bash
vidsearch add "path/to/video.mp4" --use-vosk
```

## Datebase
- SQLite as database stored in `~/.vidsearch/vidsearch.db`

## Requirements

- Python 3.8+
- SQLite (built-in)
- FFmpeg (for Faster-Whisper case audio extraction; MoviePy does invoke FFmpeg under the hood)
- Video player: mpv

## Dependencies

Key packages from `requirements.txt`:
- `faster-whisper`: GPU-accelerated Whisper transcription
- `moviepy`: Video/audio processing
- `vosk`: Offline speech recognition
- `pypinyin`: Chinese text processing (TODO)
- `rapidfuzz`: Fuzzy string matching for search (TODO)

## Notes

- First transcription may take time as Whisper model downloads (~3GB)
- GPU recommended for faster transcription
- Supports common video formats: MP4, MKV, AVI, MOV, etc.