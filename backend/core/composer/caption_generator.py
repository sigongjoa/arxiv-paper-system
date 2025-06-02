import logging

class CaptionGenerator:
    def generate(self, script):
        logging.info("Generating captions")
        
        captions = []
        time_offset = 0
        
        # Hook
        captions.append({
            'text': script['hook'],
            'start': time_offset,
            'duration': 3
        })
        time_offset += 3
        
        # Introduction
        captions.append({
            'text': script['introduction'],
            'start': time_offset,
            'duration': 3
        })
        time_offset += 3
        
        # Main points
        for point in script['main_points']:
            captions.append({
                'text': point['text'],
                'start': time_offset,
                'duration': point['duration']
            })
            time_offset += point['duration']
        
        # Conclusion
        captions.append({
            'text': script['conclusion'],
            'start': time_offset,
            'duration': 5
        })
        
        return captions
