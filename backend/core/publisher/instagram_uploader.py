import logging

class InstagramUploader:
    def upload(self, video_path):
        logging.error(f"InstagramUploader.upload() not implemented")
        raise NotImplementedError(
            "Instagram upload not implemented. Required:\n"
            "1. Install instagrapi: pip install instagrapi\n"
            "2. Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in .env\n"
            "3. Implement login and upload logic\n"
            "See https://github.com/adw0rd/instagrapi for documentation"
        )
