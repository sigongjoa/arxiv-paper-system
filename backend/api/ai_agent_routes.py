from fastapi import APIRouter, HTTPException
from datetime import datetime
import os
import logging
import sys

# Add root directory to path
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_path)

try:
    from core.paper_database import PaperDatabase as DatabaseManager
    from core.ai_agent import AIAgent
    from core.llm_summarizer import LLMSummarizer # AI agent가 LLM Summarizer를 사용할 수 있으므로 임포트
except ImportError as e:
    logging.error(f"ERROR: AI Agent route imports failed - {e}")
    raise

router = APIRouter()

# Initialize components
db = DatabaseManager()
ai_agent = AIAgent()
llm_summarizer = LLMSummarizer()

logging.basicConfig(level=logging.ERROR)
print("DEBUG: AI Agent routes initialized with database, AI agent, and LLM summarizer components")

# ==========================================
# AI AGENT ENDPOINTS
# ==========================================

@router.post("/analyze/comprehensive")
async def comprehensive_paper_analysis(request: dict):
    """종합적인 논문 분석"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        # 논문 정보 조회
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors,
            'arxiv_id': paper.paper_id # arxiv_id 대신 paper_id 사용
        }
        
        result = await ai_agent.analyze_paper_comprehensive(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Comprehensive analysis failed for {arxiv_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract/findings")
async def extract_key_findings(request: dict):
    """핵심 발견사항 추출"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors
        }
        
        result = await ai_agent.extract_key_findings(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Key findings extraction failed for {arxiv_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assess/quality")
async def assess_paper_quality(request: dict):
    """논문 품질 평가"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors
        }
        
        result = await ai_agent.assess_paper_quality(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Quality assessment failed for {arxiv_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_paper(request: dict):
    """논문과 대화형 상호작용"""
    paper_id = request.get('paper_id')
    message = request.get('message')
    session_id = request.get('session_id', 'default')
    
    if not paper_id or not message:
        raise HTTPException(status_code=400, detail="paper_id and message required")
    
    try:
        result = await ai_agent.chat_with_paper(paper_id, message, session_id)
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Chat interaction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest/related")
async def suggest_related_papers(request: dict):
    """관련 논문 추천"""
    paper_id = request.get('paper_id')
    limit = request.get('limit', 5)
    
    if not paper_id:
        raise HTTPException(status_code=400, detail="paper_id required")
    
    try:
        result = await ai_agent.suggest_related_papers(paper_id, limit)
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Related papers suggestion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/questions")
async def generate_research_questions(request: dict):
    """연구 질문 생성"""
    arxiv_id = request.get('arxiv_id')
    
    if not arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        paper = db.get_paper_by_id(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = {
            'title': paper.title,
            'abstract': paper.abstract,
            'categories': paper.categories,
            'authors': paper.authors
        }
        
        result = await ai_agent.generate_research_questions(paper_data)
        result['arxiv_id'] = arxiv_id
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Research questions generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_papers(request: dict):
    """논문 비교 분석"""
    paper_ids = request.get('paper_ids', [])
    
    if not paper_ids or len(paper_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 paper_ids required")
    
    try:
        # db를 통해 paper_ids에 해당하는 논문 정보를 가져와 ai_agent.compare_papers에 전달
        papers_data = []
        for paper_id in paper_ids:
            paper = db.get_paper_by_id(paper_id)
            if paper:
                papers_data.append({
                    'paper_id': paper.paper_id,
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': paper.authors,
                    'categories': paper.categories
                })
        
        if len(papers_data) < 2:
            raise HTTPException(status_code=404, detail="Could not find at least 2 papers for comparison.")

        result = await ai_agent.compare_papers(papers_data) # paper_ids 대신 papers_data 전달
        result['timestamp'] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logging.error(f"ERROR: Paper comparison failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/clear/{session_id}")
async def clear_chat_history(session_id: str):
    """대화 히스토리 초기화"""
    try:
        ai_agent.clear_conversation_history(session_id)
        
        return {
            'success': True,
            'message': f'Chat history cleared for session {session_id}',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"ERROR: Failed to clear chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_ai_agent_status():
    """AI 에이전트 상태 확인"""
    try:
        # LM Studio 연결 테스트
        # LM StudioClient.check_connection()이 필요할 수 있으나, 현재 AIAgent 내부에서 처리한다고 가정.
        # 또는 간단한 LLM 요약 테스트로 대체
        test_paper = {
            'title': 'Test Paper for AI Agent Status Check',
            'abstract': 'This is a test abstract to verify AI agent functionality.',
            'categories': ['cs.AI'],
            'authors': ['Test Author']
        }
        
        # 간단한 분석 테스트 (LLMSummarizer를 통해)
        test_result = llm_summarizer.summarize_paper(test_paper) # ai_agent 대신 llm_summarizer 사용
        
        # LLM Summarizer가 제대로 작동했다면 'background' 키가 있을 것으로 가정
        ai_agent_online = 'background' in test_result and 'problem_definition' in test_result['background']

        status = {
            'ai_agent_status': 'Online' if ai_agent_online else 'Offline',
            'lm_studio_connection': 'Connected' if ai_agent_online else 'Disconnected',
            'available_functions': [
                'comprehensive_analysis',
                'key_findings_extraction',
                'quality_assessment',
                'chat_interaction',
                'related_papers_suggestion',
                'research_questions_generation',
                'paper_comparison'
            ],
            'conversation_sessions': len(ai_agent.conversation_history) if hasattr(ai_agent, 'conversation_history') else 0, # conversation_history 속성 체크
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        logging.error(f"ERROR: AI agent status check failed: {str(e)}", exc_info=True)
        return {
            'ai_agent_status': 'Offline',
            'lm_studio_connection': 'Disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 