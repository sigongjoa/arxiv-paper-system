import logging

class CaptionGenerator:
    def generate(self, script):
        logging.info(f"ERROR 레벨: Generating captions for script with {len(script.get('scenes', []))} scenes")
        
        if not script or not script.get('scenes'):
            raise ValueError("ERROR: Script with scenes required for caption generation")
        
        captions = []
        time_offset = 0
        
        # Hook (첫 3초)
        if script.get('hook'):
            captions.append({
                'text': script['hook'],
                'start': time_offset,
                'duration': 3
            })
            time_offset += 3
        
        # 각 씬별 자막 생성
        for i, scene in enumerate(script['scenes']):
            text = scene.get('text', '')
            duration = scene.get('duration', 5)
            
            if not text:
                raise ValueError(f"ERROR: Empty text in scene {i}")
            
            captions.append({
                'text': text,
                'start': time_offset,
                'duration': duration,
                'scene_id': i
            })
            time_offset += duration
        
        # CTA (마무리)
        if script.get('cta'):
            captions.append({
                'text': script['cta'],
                'start': time_offset,
                'duration': 2
            })
        
        # 60초 제한 검증
        if time_offset > 60:
            raise ValueError(f"ERROR: Caption total duration {time_offset}s exceeds 60s limit")
        
        logging.info(f"Generated {len(captions)} captions, total {time_offset}s")
        return captions
