from . import db


def index_transcript(video_id: int, transcript: str):
    """Index the segments for a given video ID."""
    for seg in transcript:
        db.insert_transcript_segment(video_id, seg['start'], seg['end'], seg['text'])