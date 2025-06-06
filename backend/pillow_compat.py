"""
Pillow 10+ 호환성을 위한 패치
MoviePy가 최신 Pillow와 호환되지 않을 때 사용
"""
from PIL import Image
import logging

# Pillow 10+ 호환성 패치
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS
    logging.info("Applied Pillow compatibility patch: ANTIALIAS -> Resampling.LANCZOS")

# 추가 호환성 패치들
if not hasattr(Image, 'BICUBIC'):
    Image.BICUBIC = Image.Resampling.BICUBIC

if not hasattr(Image, 'BILINEAR'):
    Image.BILINEAR = Image.Resampling.BILINEAR  

if not hasattr(Image, 'NEAREST'):
    Image.NEAREST = Image.Resampling.NEAREST
