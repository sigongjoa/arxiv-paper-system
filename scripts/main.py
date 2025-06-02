#!/usr/bin/env python3
import sys
import os

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # GUI 실행
    from frontend.gui_app import main
    main()
