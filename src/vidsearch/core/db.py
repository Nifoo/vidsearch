import os
import sqlite3

# Default DB path: {HOME}/.vidsearch/vidsearch.db
# HOME = os.path.expanduser("~")
HOME = "."
DEFAULT_DB_DIR = os.path.join(HOME, ".vidsearch")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "vidsearch.db")

# Ensure directory exists
os.makedirs(DEFAULT_DB_DIR, exist_ok=True)

def get_db_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create the videos table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file TEXT UNIQUE
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_file ON videos(file);
    """)

    # Create the segments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY,
            video_id INTEGER,
            start REAL,
            end REAL,
            text TEXT,
            text_pinyin TEXT
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_video_id ON segments(video_id);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_text ON segments(text);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_pinyin ON segments(text_pinyin);
    """)

    conn.commit()
    conn.close()

def insert_video(video_file):
    conn = get_db_connection()
    cur = conn.cursor()
    video_file = os.path.abspath(video_file)
    try:
        cur.execute(
            "INSERT INTO videos (file) VALUES (?)",
            (video_file,)
        )
        conn.commit()
        video_id = cur.lastrowid
        print(f"Inserted video '{video_file}' with ID {video_id}")
        return video_id
    except sqlite3.IntegrityError:
        # duplicate video file
        print(f"Video '{video_file}' already exists in DB.")
        return None
    except Exception as e:
        conn.rollback()
        print(f"Failed to insert '{video_file}': {e}")
        return None
    finally:
        conn.close()  # always close the connection

def insert_transcript_segment(video_id, start, end, text):
    conn = get_db_connection()
    # Insert into segments
    conn.execute(
        "INSERT INTO segments (video_id, start, end, text, text_pinyin) VALUES (?, ?, ?, ?, ?)",
        (video_id, start, end, text, "")
    )
    conn.commit()
    conn.close()


def search_videos_by_name(query: str, limit=None, offset=0):
    conn = get_db_connection()
    cur = conn.cursor()
    if limit is not None:
        cur.execute(
            "SELECT * FROM videos WHERE file LIKE ? LIMIT ? OFFSET ?",
            (f"%{query}%", limit, offset)
        )
    else:
        cur.execute(
            "SELECT * FROM videos WHERE file LIKE ?",
            (f"%{query}%",)
        )
    results = cur.fetchall()
    conn.close()
    return results

def search_segment_by_transcript(query: str, limit=None, offset=0):
    conn = get_db_connection()
    cur = conn.cursor()
    if limit is not None:
        cur.execute(
            "SELECT * FROM segments WHERE text LIKE ? LIMIT ? OFFSET ?",
            (f"%{query}%", limit, offset)
        )
    else:
        cur.execute(
            "SELECT * FROM segments WHERE text LIKE ?",
            (f"%{query}%",)
        )
    results = cur.fetchall()
    conn.close()
    return results

def get_segment_by_id(segment_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM segments WHERE id = ?",
        (segment_id,)
    )
    result = cur.fetchone()
    conn.close()
    return result

def get_video_path(video_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT file FROM videos WHERE id = ?",
        (video_id,)
    )
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_videos(limit=None, offset=0):
    conn = get_db_connection()
    cur = conn.cursor()
    if limit is not None:
        cur.execute("SELECT * FROM videos LIMIT ? OFFSET ?", (limit, offset))
    else:
        cur.execute("SELECT * FROM videos")
    results = cur.fetchall()
    conn.close()
    return results

def get_video_by_file_path(video_file):
    conn = get_db_connection()
    cur = conn.cursor()
    video_file = os.path.abspath(video_file)
    cur.execute("SELECT id FROM videos WHERE file = ?", (video_file,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_segments_by_video_id(video_id: int, limit=None, offset=0):
    conn = get_db_connection()
    cur = conn.cursor()
    if limit is not None:
        cur.execute(
            "SELECT * FROM segments WHERE video_id = ? ORDER BY start LIMIT ? OFFSET ?",
            (video_id, limit, offset)
        )
    else:
        cur.execute(
            "SELECT * FROM segments WHERE video_id = ? ORDER BY start",
            (video_id,)
        )
    results = cur.fetchall()
    conn.close()
    return results

def iterate_pages(fetch_fn, page_size=50, *args, **kwargs):
    offset = 0
    while True:
        rows = fetch_fn(*args, limit=page_size, offset=offset, **kwargs)
        for r in rows:
            yield r
        if len(rows) < page_size:
            break
        wait_for_enter()
        offset += page_size

def wait_for_enter():
    try:
        input("Press Enter to see next page... (Ctrl+C to exit)")
        return True
    except KeyboardInterrupt:
        print("\nExiting list early.")
        return False
    
def delete_video(video_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # First delete segments associated with the video
        cur.execute("DELETE FROM segments WHERE video_id = ?", (video_id,))
        if cur.rowcount == 0:
            print(f"No records found for video_id {video_id} in segments table. Skipping for video_id {video_id}")
        # Then delete the video record itself
        cur.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        if cur.rowcount == 0:
            print(f"No records found for video_id {video_id} in videos table. Skipping for video_id {video_id}")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Failed to delete video_id {video_id}: {e}")
        conn.rollback()
    finally:
        conn.close()
