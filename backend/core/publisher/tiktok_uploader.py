import logging

class TikTokUploader:
    def upload(self, video_path):
        logging.warning("TikTok API is very limited - manual upload may be required")
        raise NotImplementedError(
            "TikTok upload not fully automated. Options:\n"
            "1. Use TikTok API (limited to 5 users in dev mode)\n"
            "2. Use third-party services like Ayrshare\n"
            "3. Manual upload via TikTok Creator Portal\n"
            "Note: TikTok has strict API restrictions"
        )
