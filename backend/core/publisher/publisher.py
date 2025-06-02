import logging

class Publisher:
    def __init__(self):
        pass
        
    def distribute(self, video_paths):
        try:
            results = []
            
            for video_path in video_paths:
                # 로컬 저장만 구현 (SNS 업로드는 별도 구현 필요)
                result = {
                    'platform': 'local',
                    'video_path': video_path,
                    'status': 'saved',
                    'url': f"file://{video_path}"
                }
                results.append(result)
                
            logging.info(f"Videos saved locally: {len(results)} files")
            return results
            
        except Exception as e:
            logging.error(f"Publishing error: {e}")
            raise
