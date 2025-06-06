# Enhanced LM Studio API Routes
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

# Safe imports with error handling
try:
    from ..core.lm_studio import LMStudioClient, PaperAnalysisAgent
    from ..citation.citation_intelligence_agent import CitationIntelligenceAgent
    from ..core.paper_database import PaperDatabase
    
    # Initialize enhanced components
    lm_client = LMStudioClient()
    paper_analysis_agent = PaperAnalysisAgent(lm_client)
    citation_intelligence = CitationIntelligenceAgent(lm_client)
    db = PaperDatabase()
    
    enhanced_features_available = True
    logger.info("Enhanced features initialized successfully")
    
except ImportError as e:
    logger.warning(f"Enhanced features not available: {e}")
    enhanced_features_available = False
    
    # Create dummy components to prevent errors
    class DummyComponent:
        async def __call__(self, *args, **kwargs):
            raise HTTPException(status_code=503, detail="Enhanced features not available")
    
    lm_client = DummyComponent()
    paper_analysis_agent = DummyComponent()
    citation_intelligence = DummyComponent()
    db = None

@router.get("/status")
async def enhanced_status():
    """Get enhanced features status"""
    return {
        "enhanced_features_available": enhanced_features_available,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

if enhanced_features_available:
    
    @router.post("/ai/enhanced/comprehensive")
    async def enhanced_comprehensive_analysis(request: dict):
        """Enhanced comprehensive paper analysis"""
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
                'authors': paper.authors,
                'arxiv_id': paper.arxiv_id
            }
            
            logger.info(f"Starting enhanced comprehensive analysis for {arxiv_id}")
            
            # Parallel analysis for better performance
            analysis_tasks = [
                paper_analysis_agent.analyze_paper_comprehensive(paper_data),
                paper_analysis_agent.extract_methodology_details(paper_data),
                paper_analysis_agent.assess_reproducibility(paper_data)
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            comprehensive_result = {
                "comprehensive_analysis": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
                "methodology_details": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
                "reproducibility_assessment": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
                "arxiv_id": arxiv_id,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Enhanced comprehensive analysis completed for {arxiv_id}")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Enhanced comprehensive analysis failed for {arxiv_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/ai/enhanced/research-gaps")
    async def identify_research_gaps(request: dict):
        """Identify research gaps and opportunities"""
        arxiv_id = request.get('arxiv_id')
        include_related = request.get('include_related', True)
        
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
                'authors': paper.authors,
                'arxiv_id': paper.arxiv_id
            }
            
            related_papers = None
            if include_related:
                # Get related papers from same categories
                related_papers_db = db.get_papers_by_categories(
                    paper.categories, limit=5, exclude_id=arxiv_id
                )
                related_papers = [{
                    'title': rp.title,
                    'abstract': rp.abstract,
                    'arxiv_id': rp.arxiv_id
                } for rp in related_papers_db]
            
            gaps_analysis = await paper_analysis_agent.identify_research_gaps(
                paper_data, related_papers
            )
            
            return gaps_analysis
            
        except Exception as e:
            logger.error(f"Research gaps identification failed for {arxiv_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/citation/enhanced/classify")
    async def classify_citation_relationships(request: dict):
        """Classify citation relationships with smart analysis"""
        citing_paper_id = request.get('citing_paper_id')
        cited_paper_ids = request.get('cited_paper_ids', [])
        
        if not citing_paper_id or not cited_paper_ids:
            raise HTTPException(status_code=400, detail="citing_paper_id and cited_paper_ids required")
        
        try:
            # Get citing paper
            citing_paper = db.get_paper_by_id(citing_paper_id)
            if not citing_paper:
                raise HTTPException(status_code=404, detail="Citing paper not found")
            
            citing_paper_data = {
                'title': citing_paper.title,
                'abstract': citing_paper.abstract,
                'arxiv_id': citing_paper.arxiv_id
            }
            
            # Get cited papers
            cited_papers_data = []
            for cited_id in cited_paper_ids:
                cited_paper = db.get_paper_by_id(cited_id)
                if cited_paper:
                    cited_papers_data.append({
                        'title': cited_paper.title,
                        'abstract': cited_paper.abstract,
                        'arxiv_id': cited_paper.arxiv_id
                    })
            
            if not cited_papers_data:
                raise HTTPException(status_code=404, detail="No valid cited papers found")
            
            classification_result = await citation_intelligence.classify_citations(
                citing_paper_data, cited_papers_data
            )
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Citation classification failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/ai/enhanced/models/status")
    async def get_enhanced_models_status():
        """Get status of enhanced LM Studio models"""
        try:
            health_status = await lm_client.check_health()
            performance_data = await lm_client.get_model_performance()
            
            return {
                "health": health_status,
                "performance": performance_data,
                "model_configs": lm_client.models,
                "optimization_config": lm_client.optimization_config,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced models status check failed: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @router.post("/system/enhanced/optimize")
    async def optimize_system_performance():
        """Optimize system performance based on usage patterns"""
        try:
            # Collect system metrics
            health_status = await lm_client.check_health()
            performance_data = await lm_client.get_model_performance()
            
            # Basic optimization recommendations
            recommendations = {
                "model_optimization": [],
                "resource_optimization": [],
                "performance_metrics": performance_data
            }
            
            # Check model performance and suggest optimizations
            for use_case, perf in performance_data.items():
                if perf.get("status") == "available":
                    response_time = perf.get("response_time", 0)
                    if response_time > 10:  # seconds
                        recommendations["model_optimization"].append({
                            "use_case": use_case,
                            "issue": "High response time",
                            "suggestion": "Consider using a smaller model or GPU acceleration"
                        })
            
            # Check system health
            if health_status.get("status") != "healthy":
                recommendations["resource_optimization"].append({
                    "issue": "LM Studio connection issues",
                    "suggestion": "Check LM Studio server status and restart if necessary"
                })
            
            return {
                "optimization_recommendations": recommendations,
                "system_health": health_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System optimization failed: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

else:
    # Fallback endpoints when enhanced features are not available
    @router.post("/ai/enhanced/comprehensive")
    async def enhanced_comprehensive_analysis_fallback(request: dict):
        raise HTTPException(
            status_code=503, 
            detail="Enhanced AI features not available. Please install required dependencies."
        )
    
    @router.get("/ai/enhanced/models/status")
    async def get_enhanced_models_status_fallback():
        return {
            "error": "Enhanced features not available",
            "available": False,
            "timestamp": datetime.now().isoformat()
        }
