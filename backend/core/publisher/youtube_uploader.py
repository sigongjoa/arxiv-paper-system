import os
import logging
from .youtube_auth import YouTubeAuth
from .youtube_metadata import YouTubeMetadata

class YouTubeUploader:
    def __init__(self):
        self.auth = YouTubeAuth()
        self.metadata = YouTubeMetadata()
        logging.info("YouTubeUploader initialized")
    
    def upload(self, video_path, title=None, description=None, tags=None):
        if not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        service = self.auth.get_authenticated_service()
        metadata = self.metadata.create_metadata(title, description, tags)
        
        logging.info(f"Starting upload: {video_path}")
        return self._upload_video(service, video_path, metadata)
    
    def _upload_video(self, service, video_path, metadata):
        from googleapiclient.http import MediaFileUpload
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = service.videos().insert(
            part=','.join(metadata.keys()),
            body=metadata,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Upload progress: {int(status.progress() * 100)}%")
        
        if 'id' in response:
            video_id = response['id']
            logging.info(f"Upload successful. Video ID: {video_id}")
            return {'status': 'success', 'video_id': video_id, 'url': f'https://youtube.com/watch?v={video_id}'}
        else:
            logging.error(f"Upload failed: {response}")
            raise Exception(f"Upload failed: {response}")
