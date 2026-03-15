import argparse
import os
import subprocess
from .core import db, indexer, transcribe
from .core.search import search_videos_by_name, search_segment_by_transcript

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".m4v"
}

def add(args):
    """
    Given video file path or a folder of video files, add all videos to the system.
    Steps:
    1. Save video info to database.
    2. Transcribe audio to text.
    3. Index transcript for search.
    """
    path = args.file_or_folder
    model_name = args.use_vosk and "Vosk" or "Whisper"
    print("Adding video(s) to DB:", args.file_or_folder)

    # --- Determine if path is file or folder ---
    files_to_add = []
    if os.path.isfile(path):
        files_to_add.append(path)
    elif os.path.isdir(path):
        # Walk the folder recursively
        for root, _, files in os.walk(path):
            for f in files:
                if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
                    files_to_add.append(os.path.join(root, f))
    else:
        print(f"Path not found or invalid: {path}")
        return

    # --- Add each video ---
    for video_file in files_to_add:
        # --- Check if video already exists in DB ---
        existing_video_id = db.get_video_by_file_path(video_file)
        if existing_video_id:
            print(f"Video '{video_file}' already exists in DB with ID: {existing_video_id}")
            response = input("Press y to delete and re-add; anything else to skip: ")
            if response == "y":
                db.delete_video(existing_video_id)
                print(f"Deleted video with ID: {existing_video_id}")
            else:
                print(f"Skipping adding video: {video_file}")
                continue

        # --- Step 1: Insert video metadata into DB ---
        video_id = db.insert_video(video_file)  # returns unique video_id
        print(f"Video added with ID: {video_id}")

        # --- Step 2: Transcribe video ---
        transcript = transcribe.transcribe_video(video_file, backend=model_name)
        print(f"Transcription done, {len(transcript)} segments found.")

        # --- Step 3: Index transcript in database ---
        indexer.index_transcript(video_id, transcript)
        print("Transcript indexed and ready for search.")


def search_video(args):
    print("Searching:", args.query)
    for r in search_videos_by_name(args.query):
        print(f"{r['id']}  {r['file']}")


def search_segment(args):
    for r in search_segment_by_transcript(args.query):
        print(f"{r['id']}  {r['video_id']}  {r['start']}  {r['text']}")

def open_segment(args):
    print("Opening segment:", args.segment_id)
    segment_id = args.segment_id
    segment = db.get_segment_by_id(segment_id)
    if not segment:
        print(f"Segment {segment_id} not found")
        return

    video_path = db.get_video_path(segment['video_id'])
    start_time = segment['start']

    print(f"Opening {video_path} at {start_time} seconds")

    # Example using mpv player; you can replace with VLC or other
    subprocess.run(["mpv", f"--start={start_time}", video_path])
    

def list_videos(args):
    print("Listing videos")
    page_size = getattr(args, "page_size", 50)
    for v in db.iterate_pages(db.get_all_videos, page_size=page_size):
        print(f"{v['id']}  {v['file']}")

def list_segments_by_video_id(args):
    video_id = args.video_id
    print(f"Listing transcripts for video ID {video_id}")
    page_size = getattr(args, "page_size", 50)
    for s in db.iterate_pages(db.get_segments_by_video_id, page_size=page_size, video_id=video_id):
        print(f"{s['start']}  {s['text']}")

def remove_video(args):
    video_id = args.video_id
    print(f"Removing video ID {video_id}")
    db.delete_video(video_id)
    print("Video removed from database.")


def build_parser(include_interactive=True):
    parser = argparse.ArgumentParser(prog="vidsearch")
    sub = parser.add_subparsers(dest="command")

    add_parser = sub.add_parser("add")
    add_parser.add_argument("file_or_folder")
    add_parser.add_argument("--use-vosk", action="store_true", help="Use Vosk instead of Whisper")
    add_parser.set_defaults(func=add)

    search_video_parser = sub.add_parser("search_video")
    search_video_parser.add_argument("query")
    search_video_parser.set_defaults(func=search_video)

    search_segment_parser = sub.add_parser("search_segment")
    search_segment_parser.add_argument("query")
    search_segment_parser.set_defaults(func=search_segment)

    open_segment_parser = sub.add_parser("open_segment")
    open_segment_parser.add_argument("--segment_id", type=int)
    open_segment_parser.set_defaults(func=open_segment)

    list_videos_parser = sub.add_parser("list_videos")
    list_videos_parser.set_defaults(func=list_videos)

    list_segments_parser = sub.add_parser("list_segments")
    list_segments_parser.add_argument("--video-id", type=int)
    list_segments_parser.set_defaults(func=list_segments_by_video_id)

    remove_parser = sub.add_parser("remove")
    remove_parser.add_argument("--video-id", type=int)
    remove_parser.set_defaults(func=remove_video)

    if include_interactive:
        interactive_parser = sub.add_parser("interactive")
        interactive_parser.set_defaults(func=interactive)

    return parser

def interactive(args):
    print("Entering interactive mode. Type 'exit' to quit.")

    parser = build_parser(include_interactive=False)

    while True:
        try:
            cmd = input("vidsearch> ").strip()

            if cmd == "exit":
                break
            if not cmd:
                continue

            args = parser.parse_args(cmd.split())

            if hasattr(args, "func"):
                args.func(args)
            else:
                print("Invalid command")

        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except SystemExit:
            print("Invalid command or arguments.")

def main():
    db.init_db()

    parser = build_parser(include_interactive=True)
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()