import os
import logging

class DebugUtils:
    @staticmethod
    def check_dependencies():
        """필수 의존성 체크"""
        deps = {}
        
        try:
            import edge_tts
            deps['edge_tts'] = 'OK'
        except ImportError as e:
            deps['edge_tts'] = f'ERROR: {e}'
            
        try:
            import moviepy.editor
            deps['moviepy'] = 'OK'
        except ImportError as e:
            deps['moviepy'] = f'ERROR: {e}'
            
        return deps
    
    @staticmethod
    def check_output_dirs():
        """출력 디렉토리 상태 체크"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        dirs = ['output/audio', 'output/videos', 'output/visuals']
        
        status = {}
        for dir_path in dirs:
            full_path = os.path.join(project_root, dir_path)
            if os.path.exists(full_path):
                files = os.listdir(full_path)
                status[dir_path] = f'OK ({len(files)} files)'
            else:
                status[dir_path] = 'MISSING'
                
        return status
    
    @staticmethod
    def diagnose_pipeline_error(error_stage, error_msg):
        """파이프라인 에러 진단"""
        logging.error(f"ERROR 레벨: Pipeline failed at {error_stage}: {error_msg}")
        
        # 의존성 체크
        deps = DebugUtils.check_dependencies()
        for dep, status in deps.items():
            if 'ERROR' in status:
                logging.error(f"Dependency issue: {dep} - {status}")
        
        # 디렉토리 체크
        dirs = DebugUtils.check_output_dirs()
        for dir_path, status in dirs.items():
            if 'MISSING' in status:
                logging.error(f"Missing directory: {dir_path}")
                
        return {
            'dependencies': deps,
            'directories': dirs,
            'stage': error_stage,
            'error': error_msg
        }
