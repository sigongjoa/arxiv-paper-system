import logging

class YouTubeMetadata:
    def __init__(self):
        logging.info("YouTubeMetadata initialized")
    
    def create_metadata(self, title=None, description=None, tags=None):
        metadata = {
            'snippet': {
                'title': title or 'ArXiv Research Summary',
                'description': description or 'Research summary generated from ArXiv paper',
                'tags': tags or ['research', 'science', 'arxiv', 'shorts'],
                'categoryId': '27'  # Education category
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        logging.info(f"Metadata created: {metadata['snippet']['title']}")
        return metadata
    
    def parse_tags(self, tag_string):
        if not tag_string:
            return []
        
        tags = [tag.strip('#').strip() for tag in tag_string.split()]
        tags = [tag for tag in tags if tag]
        logging.info(f"Tags parsed: {tags}")
        return tags
