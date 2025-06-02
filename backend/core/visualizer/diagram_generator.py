from PIL import Image, ImageDraw
import os
import logging

class DiagramGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        
    def generate(self, text):
        logging.info("Generating diagram")
        
        # 간단한 플로우차트 생성
        img = Image.new('RGB', (1080, 1920), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # 박스들 그리기
        boxes = [
            (340, 400, 740, 600),
            (340, 800, 740, 1000),
            (340, 1200, 740, 1400)
        ]
        
        for box in boxes:
            draw.rectangle(box, outline='cyan', width=3)
        
        # 화살표 그리기
        draw.line((540, 600, 540, 800), fill='cyan', width=3)
        draw.line((540, 1000, 540, 1200), fill='cyan', width=3)
        
        # 저장
        filename = f"diagram_{hash(text)}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        
        return filepath
