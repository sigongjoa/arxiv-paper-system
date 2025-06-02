#!/usr/bin/env python3
"""
arXiv to Shorts - Web Application

Usage:
    python run.py                    # Start web server (default port 5000)
    python run.py --test            # Run test pipeline  
    python run.py --port 8080       # Custom port
"""

import sys
import os
import argparse

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_test():
    """테스트 파이프라인 실행"""
    from scripts.test_real_analysis import main
    main()

def run_web(port=5000):
    """웹 서버 실행"""
    from backend.app import app
    print(f"🌐 Starting arXiv to Shorts Web Server on http://localhost:{port}")
    print("📋 Open your browser and start analyzing arXiv papers!")
    app.run(debug=True, host='0.0.0.0', port=port)

def main():
    parser = argparse.ArgumentParser(description='arXiv to Shorts - AI-powered video generator (Web Version)')
    parser.add_argument('--test', action='store_true', help='Run test pipeline')
    parser.add_argument('--port', type=int, default=5000, help='Web server port (default: 5000)')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Running test pipeline...")
        run_test()
    else:
        print("🌐 Starting web application...")
        run_web(args.port)

if __name__ == "__main__":
    main()
