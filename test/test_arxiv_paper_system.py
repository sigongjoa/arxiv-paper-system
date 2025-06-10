import requests
import json
import time

FASTAPI_API_BASE = "http://localhost:8000/recommendations"

def initialize_recommendation_system():
    """
    arxiv-paper-system FastAPI 백엔드의 추천 시스템을 초기화합니다.
    """
    url = f"{FASTAPI_API_BASE}/initialize"
    print(f"Initializing recommendation system: {url}")

    headers = {"Content-Type": "application/json"}
    payload = {} # 초기화에 필요한 특정 payload가 없다면 빈 dict

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300) # 초기화에 시간이 걸릴 수 있으므로 타임아웃 증가
        response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
        result = response.json()
        print(f"FastAPI initialization response: {json.dumps(result, indent=2)}")
        if result.get("message") == "Recommendation system initialized successfully.":
            print("Recommendation system initialized successfully.")
            return True
        else:
            print(f"Recommendation system initialization failed: {result.get('error', result)}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error initializing recommendation system: {e}")
        if isinstance(e, requests.exceptions.ConnectionError):
            print("Please ensure the FastAPI recommendation system server is running at http://localhost:8000.")
            print("You might need to start the server (e.g., `uvicorn main:app --reload` in your backend directory).")
        if hasattr(e, 'response') and e.response is not None:
            print(f"FastAPI error response: {e.response.text}")
        return False

def get_recommendations(paper_id: str, limit: int = 5):
    """
    arxiv-paper-system FastAPI 백엔드에서 RAG 기반 추천을 요청합니다.
    """
    url = f"{FASTAPI_API_BASE}/get"
    print(f"Requesting recommendations from FastAPI: {url}")

    payload = {
        "paper_id": paper_id,
        "limit": limit
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
        result = response.json()
        print(f"FastAPI recommendations response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error requesting recommendations from FastAPI: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"FastAPI error response: {e.response.text}")
        return None

def main():
    print("Starting arxiv-paper-system API test...")
    
    # 1. 추천 시스템 초기화
    print("\n--- Initializing Recommendation System ---")
    if not initialize_recommendation_system():
        print("Recommendation system initialization failed. Exiting.")
        return
    print("Waiting for initialization to complete...")
    time.sleep(10) # 초기화가 완료될 시간을 충분히 기다림
    
    # 2. RAG 기반 추천 API 테스트
    print("\n--- Testing Recommendations API ---")
    # 더미 paper_id 사용 (실제 DB에 존재하는 ID로 가정)
    # 실제 테스트 시에는 populate_db.py 등으로 생성된 유효한 ID를 사용해야 합니다.
    dummy_paper_id = "2001.00001" # 예시 ID, 실제 DB에 존재해야 함

    recommendations = get_recommendations(dummy_paper_id)
    if recommendations:
        print("\nRecommendations API test completed successfully!")
    else:
        print("\nRecommendations API test failed.")

if __name__ == "__main__":
    main() 