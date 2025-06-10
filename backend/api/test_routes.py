"""기본 테스트"""
from fastapi import APIRouter
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.api.routes import router # main router from routes.py

test_router = APIRouter(prefix="/test")

client = TestClient(router)

@test_router.get("/simple")
async def simple_test():
    return {"status": "ok", "message": "basic test works"}

@test_router.post("/crawl-test")  
async def crawl_test(request: dict):
    return {"received": request, "status": "received"}

@test_router.post("/papers/analyze")
async def analyze_paper_test_route(request: dict):
    # This is a proxy route to test the /papers/analyze endpoint in the main router
    # We will call the actual analyze_paper function here, potentially with mocks
    pass

def test_simple_test():
    response = client.get("/simple")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "basic test works"}

def test_crawl_test():
    response = client.post("/crawl-test", json={"test_key": "test_value"})
    assert response.status_code == 200
    assert response.json() == {"received": {"test_key": "test_value"}, "status": "received"}

@patch('backend.api.routes.PaperDatabase')
@patch('backend.api.routes.LLMSummarizer')
def test_analyze_paper(mock_llm_summarizer, mock_paper_database):
    # Mocking PaperDatabase
    mock_db_instance = mock_paper_database.return_value
    mock_paper = MagicMock()
    mock_paper.title = "Test Paper Title"
    mock_paper.abstract = "Test Paper Abstract"
    mock_paper.categories = ["cs.AI"]
    mock_paper.paper_id = "2401.00001"
    mock_db_instance.get_paper_by_id.return_value = mock_paper

    # Mocking LLMSummarizer
    mock_llm_summarizer_instance = mock_llm_summarizer.return_value
    mock_llm_summarizer_instance.summarize_paper.return_value = "This is a summarized analysis."

    # Test case 1: Valid arxiv_id
    response = client.post("/papers/analyze", json={"arxiv_id": "2401.00001"})
    assert response.status_code == 200
    assert "analysis" in response.json()
    assert response.json()["arxiv_id"] == "2401.00001"
    assert response.json()["analysis"] == "This is a summarized analysis."
    mock_db_instance.get_paper_by_id.assert_called_once_with("2401.00001")
    mock_llm_summarizer_instance.summarize_paper.assert_called_once()

    # Reset mocks for the next test case
    mock_paper_database.reset_mock()
    mock_llm_summarizer.reset_mock()

    # Test case 2: Missing arxiv_id
    response = client.post("/papers/analyze", json={})
    assert response.status_code == 400
    assert response.json() == {"detail": "arxiv_id required"}

    # Reset mocks for the next test case
    mock_paper_database.reset_mock()
    mock_llm_summarizer.reset_mock()

    # Test case 3: Paper not found
    mock_db_instance = mock_paper_database.return_value
    mock_db_instance.get_paper_by_id.return_value = None
    response = client.post("/papers/analyze", json={"arxiv_id": "9999.99999"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found"}
    mock_db_instance.get_paper_by_id.assert_called_once_with("9999.99999")
    mock_llm_summarizer_instance.summarize_paper.assert_not_called()
