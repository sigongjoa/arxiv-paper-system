"""
Pillow 10+ 호환성을 위한 패치
MoviePy가 최신 Pillow와 호환되지 않을 때 사용
"""
from PIL import Image
import logging

# Pillow 10+ 호환성 패치
if not hasattr(Image, 'ANTIALIAS'):
    try:
        Image.ANTIALIAS = Image.Resampling.LANCZOS
        logging.info("Applied Pillow compatibility patch: ANTIALIAS -> Resampling.LANCZOS")
    except AttributeError:
        # 더 오래된 Pillow 버전의 경우
        Image.ANTIALIAS = Image.LANCZOS
        logging.info("Applied Pillow compatibility patch: ANTIALIAS -> LANCZOS")

# 추가 호환성 패치들
if not hasattr(Image, 'BICUBIC'):
    try:
        Image.BICUBIC = Image.Resampling.BICUBIC
    except AttributeError:
        pass

if not hasattr(Image, 'BILINEAR'):
    try:
        Image.BILINEAR = Image.Resampling.BILINEAR  
    except AttributeError:
        pass

if not hasattr(Image, 'NEAREST'):
    try:
        Image.NEAREST = Image.Resampling.NEAREST
    except AttributeError:
        pass
