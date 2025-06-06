import logging
import json
import time
from typing import Dict, List, Any
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class DebugLogger:
    """Debug logging utility for enhanced system"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.start_time = time.time()
        
    def log_performance(self, operation: str, duration: float, details: Dict = None):
        """Log performance metrics"""
        logger.info(f"[{self.component_name}] {operation} completed in {duration:.3f}s")
        if details:
            logger.debug(f"[{self.component_name}] Details: {json.dumps(details, ensure_ascii=False)}")
    
    def log_error(self, operation: str, error: Exception, context: Dict = None):
        """Log errors with full stack trace"""
        logger.error(f"[{self.component_name}] {operation} failed: {str(error)}")
        logger.error(f"[{self.component_name}] Stack trace: {traceback.format_exc()}")
        if context:
            logger.error(f"[{self.component_name}] Context: {json.dumps(context, ensure_ascii=False)}")
    
    def log_analysis_result(self, arxiv_id: str, analysis_type: str, result: Dict):
        """Log analysis results for debugging"""
        logger.info(f"[{self.component_name}] Analysis completed - ID: {arxiv_id}, Type: {analysis_type}")
        
        if "error" in result:
            logger.error(f"[{self.component_name}] Analysis error: {result['error']}")
        else:
            # Log key metrics
            if analysis_type == "comprehensive" and "quality_scores" in result:
                scores = result["quality_scores"]
                logger.info(f"[{self.component_name}] Quality scores: {scores}")
            
            if "timestamp" in result:
                logger.debug(f"[{self.component_name}] Analysis timestamp: {result['timestamp']}")

class UnitTestFramework:
    """Simple unit testing framework for enhanced components"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
    
    async def test_lm_studio_client(self, lm_client):
        """Test LM Studio client functionality"""
        self.tests_run += 1
        test_name = "LM Studio Client Test"
        
        try:
            # Test health check
            health = await lm_client.check_health()
            assert "status" in health, "Health check should return status"
            
            # Test simple generation
            test_prompt = "Test prompt for unit testing"
            response = await lm_client.generate_response(test_prompt, "paper_summary")
            assert isinstance(response, str), "Response should be string"
            assert len(response) > 0, "Response should not be empty"
            
            self.tests_passed += 1
            self.test_results.append({"test": test_name, "status": "PASSED", "details": "All checks passed"})
            logger.info(f"✅ {test_name} PASSED")
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            logger.error(f"❌ {test_name} FAILED: {str(e)}")
    
    async def test_paper_analysis_agent(self, analysis_agent, sample_paper):
        """Test paper analysis agent"""
        self.tests_run += 1
        test_name = "Paper Analysis Agent Test"
        
        try:
            # Test comprehensive analysis
            result = await analysis_agent.analyze_paper_comprehensive(sample_paper)
            assert isinstance(result, dict), "Analysis result should be dict"
            assert "error" not in result or result.get("error") is None, f"Analysis should not have errors: {result.get('error')}"
            
            self.tests_passed += 1
            self.test_results.append({"test": test_name, "status": "PASSED", "details": "Analysis completed successfully"})
            logger.info(f"✅ {test_name} PASSED")
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            logger.error(f"❌ {test_name} FAILED: {str(e)}")
    
    async def test_citation_intelligence(self, citation_agent, sample_citing_paper, sample_cited_papers):
        """Test citation intelligence agent"""
        self.tests_run += 1
        test_name = "Citation Intelligence Test"
        
        try:
            # Test citation classification
            result = await citation_agent.classify_citations(sample_citing_paper, sample_cited_papers)
            assert isinstance(result, dict), "Classification result should be dict"
            assert "classifications" in result, "Result should contain classifications"
            
            self.tests_passed += 1
            self.test_results.append({"test": test_name, "status": "PASSED", "details": "Citation classification successful"})
            logger.info(f"✅ {test_name} PASSED")
            
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            logger.error(f"❌ {test_name} FAILED: {str(e)}")
    
    def get_test_summary(self) -> Dict:
        """Get test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_run - self.tests_passed,
            "success_rate": f"{success_rate:.1f}%",
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

class PerformanceMonitor:
    """Monitor system performance for optimization"""
    
    def __init__(self):
        self.metrics = {}
        self.operation_times = {}
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.operation_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str, details: Dict = None):
        """End timing an operation and record metrics"""
        if operation_name in self.operation_times:
            duration = time.time() - self.operation_times[operation_name]
            
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            
            metric_entry = {
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
            
            self.metrics[operation_name].append(metric_entry)
            
            # Keep only last 100 entries per operation
            if len(self.metrics[operation_name]) > 100:
                self.metrics[operation_name] = self.metrics[operation_name][-100:]
            
            logger.debug(f"Performance: {operation_name} took {duration:.3f}s")
            
            del self.operation_times[operation_name]
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        summary = {}
        
        for operation, entries in self.metrics.items():
            durations = [entry["duration"] for entry in entries]
            
            if durations:
                summary[operation] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "last_duration": durations[-1] if durations else 0,
                    "last_timestamp": entries[-1]["timestamp"] if entries else None
                }
        
        return {
            "performance_metrics": summary,
            "monitoring_since": datetime.now().isoformat(),
            "total_operations": sum(len(entries) for entries in self.metrics.values())
        }

class SystemValidator:
    """Validate system configuration and dependencies"""
    
    @staticmethod
    def validate_lm_studio_config(config: Dict) -> Dict:
        """Validate LM Studio configuration"""
        validation_result = {"valid": True, "issues": []}
        
        required_fields = ["models", "optimization_config"]
        for field in required_fields:
            if field not in config:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing required field: {field}")
        
        # Validate model configurations
        if "models" in config:
            for use_case, model_config in config["models"].items():
                required_model_fields = ["name", "context_length", "temperature", "max_tokens"]
                for field in required_model_fields:
                    if field not in model_config:
                        validation_result["valid"] = False
                        validation_result["issues"].append(f"Model {use_case} missing field: {field}")
        
        return validation_result
    
    @staticmethod
    def validate_paper_data(paper_data: Dict) -> Dict:
        """Validate paper data structure"""
        validation_result = {"valid": True, "issues": []}
        
        required_fields = ["title", "abstract", "arxiv_id"]
        for field in required_fields:
            if field not in paper_data or not paper_data[field]:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing or empty field: {field}")
        
        # Validate data types
        if "categories" in paper_data and not isinstance(paper_data["categories"], list):
            validation_result["valid"] = False
            validation_result["issues"].append("Categories should be a list")
        
        if "authors" in paper_data and not isinstance(paper_data["authors"], list):
            validation_result["valid"] = False
            validation_result["issues"].append("Authors should be a list")
        
        return validation_result

# Global debug utilities
debug_logger = DebugLogger("GLOBAL")
performance_monitor = PerformanceMonitor()

def log_function_call(func):
    """Decorator to log function calls for debugging"""
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        debug_logger.log_performance(f"CALL_{func_name}", 0, {"args_count": len(args), "kwargs": list(kwargs.keys())})
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            debug_logger.log_performance(f"COMPLETE_{func_name}", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            debug_logger.log_error(f"ERROR_{func_name}", e, {"duration": duration})
            raise
    return wrapper

async def run_system_diagnostics():
    """Run comprehensive system diagnostics"""
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "system_status": "checking",
        "components": {}
    }
    
    try:
        # Test LM Studio connection
        from ..core.lm_studio import LMStudioClient
        lm_client = LMStudioClient()
        health = await lm_client.check_health()
        diagnostics["components"]["lm_studio"] = {
            "status": health.get("status", "unknown"),
            "details": health
        }
        
        # Test database connection
        from ..core.paper_database import PaperDatabase
        db = PaperDatabase()
        paper_count = db.get_total_count()
        diagnostics["components"]["database"] = {
            "status": "healthy" if paper_count >= 0 else "error",
            "paper_count": paper_count
        }
        
        # Check Notion integration
        try:
            from ..automation.enhanced_notion_saver import EnhancedNotionSaver
            notion_saver = EnhancedNotionSaver()
            diagnostics["components"]["notion"] = {"status": "available"}
        except Exception as e:
            diagnostics["components"]["notion"] = {"status": "error", "error": str(e)}
        
        # Overall system status
        component_statuses = [comp.get("status") for comp in diagnostics["components"].values()]
        if all(status == "healthy" or status == "available" for status in component_statuses):
            diagnostics["system_status"] = "healthy"
        elif any(status == "error" for status in component_statuses):
            diagnostics["system_status"] = "degraded"
        else:
            diagnostics["system_status"] = "unknown"
        
        logger.info(f"System diagnostics completed: {diagnostics['system_status']}")
        
    except Exception as e:
        diagnostics["system_status"] = "error"
        diagnostics["error"] = str(e)
        logger.error(f"System diagnostics failed: {e}")
    
    return diagnostics
