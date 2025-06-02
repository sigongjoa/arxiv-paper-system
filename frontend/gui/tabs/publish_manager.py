import os
import logging
import threading
from backend.core.publisher import YouTubeUploader
from backend.core.publisher.youtube_metadata import YouTubeMetadata

class PublishManager:
    def __init__(self):
        self.youtube_uploader = YouTubeUploader()
        self.metadata_helper = YouTubeMetadata()
        logging.info("PublishManager initialized")
    
    def publish_to_platforms(self, video_path, platforms, title, description, hashtags, callback=None):
        def upload_thread():
            results = {}
            
            for platform in platforms:
                try:
                    if platform == 'youtube':
                        result = self._upload_to_youtube(video_path, title, description, hashtags)
                        results[platform] = result
                        logging.info(f"YouTube upload completed: {result}")
                    else:
                        results[platform] = {'status': 'error', 'message': f'{platform} not implemented'}
                        logging.error(f"{platform} upload not implemented")
                        
                except Exception as e:
                    results[platform] = {'status': 'error', 'message': str(e)}
                    logging.error(f"{platform} upload failed: {e}")
            
            if callback:
                callback(results)
        
        thread = threading.Thread(target=upload_thread)
        thread.daemon = True
        thread.start()
        logging.info(f"Upload thread started for platforms: {platforms}")
    
    def _upload_to_youtube(self, video_path, title, description, hashtags):
        tags = self.metadata_helper.parse_tags(hashtags)
        return self.youtube_uploader.upload(video_path, title, description, tags)
