#!/usr/bin/env python3
import logging
import os
import sys

logging.basicConfig(level=logging.ERROR)

def test_fonts():
    """폰트 로딩 테스트"""
    from PIL import Image, ImageDraw, ImageFont
    
    logging.error("Starting font test...")
    
    # 테스트용 이미지 생성
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    test_text = "한글 폰트 테스트 123"
    
    # 방법 1: Windows 기본 한글 폰트
    font_path = 'C:/Windows/Fonts/malgun.ttf'
    font = ImageFont.truetype(font_path, 30)
    draw.text((20, 20), test_text, fill='black', font=font)
    logging.error(f"✓ Windows font loaded: {font_path}")
    
    # 저장
    output_path = os.path.join(os.path.dirname(__file__), 'output', 'font_test.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    
    logging.error(f"Test image saved: {output_path}")
    return output_path

def test_research_template():
    """연구 템플릿 테스트"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from templates.research_template import ResearchVideoTemplate
    
    template = ResearchVideoTemplate()
    
    test_img = template.CreateTemplate(
        "한글 제목 테스트", 
        "연구자", 
        "2024.06.04", 
        "#테스트"
    )
    
    output_path = os.path.join(os.path.dirname(__file__), 'output', 'template_test.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    test_img.save(output_path)
    
    logging.error(f"Template test saved: {output_path}")
    return output_path

if __name__ == "__main__":
    logging.error("=== Font Test Started ===")
    
    # 기본 폰트 테스트
    font_result = test_fonts()
    
    # 템플릿 테스트
    template_result = test_research_template()
    
    logging.error("=== Font Test Completed ===")
    logging.error(f"Results: {font_result}, {template_result}")
