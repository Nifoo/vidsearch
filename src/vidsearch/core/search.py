from . import db


def search_videos_by_name(keyword, page_size=50):
    yield from db.iterate_pages(db.search_videos_by_name, page_size=page_size, query=keyword)
        

def search_segment_by_transcript(keyword, page_size=50):
    yield from db.iterate_pages(db.search_segment_by_transcript, page_size=page_size, query=keyword)
