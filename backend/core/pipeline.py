from .summarizer import Summarizer
from .visualizer import Visualizer
from .narrator import Narrator
from .composer import Composer
from .publisher import Publisher
from .shorts import get_config, validate_shorts_config
from .utils import DebugUtils
import logging
import time

class Pipeline:
    def __init__(self):
        # 양산형 쇼츠 설정 검증
        validate_shorts_config()
        self.config = get_config()
        
        self.summarizer = Summarizer()
        self.visualizer = Visualizer()
        self.narrator = Narrator()
        self.composer = Composer() 
        self.publisher = Publisher()
        
        logging.info("Pipeline initialized for mass-production shorts (9:16, 60s max)")
    
    def process_paper(self, arxiv_id, paper_data):
        start_time = time.time()
        
        if not arxiv_id or not paper_data:
            raise ValueError("ERROR: arxiv_id and paper_data required")
            
        if not paper_data.get('title') or not paper_data.get('abstract'):
            raise ValueError(f"ERROR: Invalid paper data for {arxiv_id} - missing title or abstract")
            
        try:
            logging.info(f"ERROR 레벨: Starting SHORTS pipeline for {arxiv_id}: {paper_data.get('title', 'Unknown')}")
            
            # Step 1/5: 양산형 스크립트 생성 (hook + 60초 제한)
            logging.info("Step 1/5: Generating mass-production shorts script...")
            try:
                script = self.summarizer.generate_script(paper_data)
                
                if not script or not script.get('scenes'):
                    raise ValueError(f"ERROR: No script generated for {arxiv_id}")
            except Exception as e:
                DebugUtils.diagnose_pipeline_error('script_generation', str(e))
                raise
                
            # 60초 검증
            total_duration = sum(scene.get('duration', 0) for scene in script.get('scenes', []))
            if total_duration > 60:
                raise ValueError(f"ERROR: Script duration {total_duration}s exceeds 60s limit")
                
            logging.info(f"Script: {len(script.get('scenes', []))} scenes, {total_duration}s total")
            
            # Step 2/5: 9:16 세로형 시각 자료 생성
            logging.info("Step 2/5: Creating 9:16 vertical visuals...")
            try:
                visuals = self.visualizer.create_visuals(paper_data, script)
                
                if not visuals or len(visuals) != len(script.get('scenes', [])):
                    raise ValueError(f"ERROR: Visual count mismatch for {arxiv_id}")
            except Exception as e:
                DebugUtils.diagnose_pipeline_error('visual_generation', str(e))
                raise
                
            logging.info(f"Generated {len(visuals)} 9:16 visual files")
            
            # Step 3/5: 쇼츠 최적화 나레이션 생성
            logging.info("Step 3/5: Generating shorts-optimized narration...")
            try:
                narration = self.narrator.generate_narration(script)
                
                if not narration or len(narration) != len(script.get('scenes', [])):
                    raise ValueError(f"ERROR: Narration count mismatch for {arxiv_id}")
            except Exception as e:
                DebugUtils.diagnose_pipeline_error('narration_generation', str(e))
                raise
                
            logging.info(f"Generated narration: {len(narration)} audio segments")
            
            # Step 4/5: 9:16 비디오 합성 (1080x1920)
            logging.info("Step 4/5: Composing 9:16 shorts video...")
            try:
                video_paths = self.composer.compose_video(visuals, narration, script)
                
                if not video_paths:
                    raise ValueError(f"ERROR: Video composition failed for {arxiv_id}")
            except Exception as e:
                DebugUtils.diagnose_pipeline_error('video_composition', str(e))
                raise
                
            logging.info(f"9:16 shorts video complete: {video_paths}")
            
            # Step 5/5: 플랫폼 배포
            logging.info("Step 5/5: Publishing to platforms...")
            results = self.publisher.distribute(video_paths)
            
            # 처리 시간 측정
            processing_time = time.time() - start_time
            logging.info(f"SHORTS PIPELINE COMPLETE: {arxiv_id} ({processing_time:.2f}s)")
            
            return {
                'video_paths': video_paths,
                'script': script,
                'visuals': visuals,
                'narration': narration,
                'publish_results': results,
                'processing_time': processing_time,
                'total_duration': total_duration
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"ERROR: Shorts pipeline failed for {arxiv_id} after {processing_time:.2f}s: {e}"
            
            # 에러 진단 실행
            diagnosis = DebugUtils.diagnose_pipeline_error('unknown', str(e))
            logging.error(f"Diagnosis: {diagnosis}")
            
            raise Exception(error_msg)
            
    def batch_process_papers(self, paper_list):
        """여러 논문 동시 처리 (양산형)"""
        if not paper_list:
            raise ValueError("ERROR: No papers provided for batch processing")
            
        if len(paper_list) > self.config['BATCH_SIZE']:
            raise ValueError(f"ERROR: Batch size {len(paper_list)} exceeds limit {self.config['BATCH_SIZE']}")
            
        logging.info(f"Starting batch processing: {len(paper_list)} papers")
        
        results = []
        errors = []
        
        for i, (arxiv_id, paper_data) in enumerate(paper_list):
            try:
                logging.info(f"Processing {i+1}/{len(paper_list)}: {arxiv_id}")
                result = self.process_paper(arxiv_id, paper_data)
                results.append({'arxiv_id': arxiv_id, 'success': True, 'result': result})
                
            except Exception as e:
                error_info = {'arxiv_id': arxiv_id, 'success': False, 'error': str(e)}
                errors.append(error_info)
                logging.error(f"Batch item {i+1} failed: {e}")
                
                # strict_mode에서는 하나라도 실패하면 전체 중단
                if self.config['STRICT_MODE']:
                    raise Exception(f"ERROR: Batch processing stopped due to failure: {e}")
        
        success_count = len(results)
        total_count = len(paper_list)
        
        logging.info(f"Batch processing complete: {success_count}/{total_count} successful")
        
        if errors and not self.config['STRICT_MODE']:
            logging.warning(f"Batch had {len(errors)} errors: {[e['arxiv_id'] for e in errors]}")
        
        return {
            'successful': results,
            'failed': errors,
            'success_rate': success_count / total_count,
            'total_processed': total_count
        }
