"""Multi-Platform Paper Analysis Agent"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import time
from .lm_studio_client import LMStudioClient

logger = logging.getLogger(__name__)

@dataclass
class PlatformAnalysisResult:
    """플랫폼별 논문 분석 결과"""
    paper_id: str
    title: str
    platform: str
    summary: str
    key_insights: List[str]
    methodology: str
    main_findings: List[str]
    limitations: List[str]
    future_work: List[str]
    technical_keywords: List[str]
    confidence_score: float
    analysis_timestamp: str

class MultiPlatformAnalysisAgent:
    """다중 플랫폼 논문 분석 AI 에이전트"""
    
    def __init__(self, llm_client: LMStudioClient):
        self.llm_client = llm_client
        self.platform_configs = {
            'ArXiv': {
                'focus': 'computer science, AI, machine learning',
                'content_type': 'preprint',
                'analysis_depth': 'technical'
            },
            'BioRxiv': {
                'focus': 'biology, life sciences, medical research',
                'content_type': 'preprint',
                'analysis_depth': 'biological'
            },
            'PMC': {
                'focus': 'peer-reviewed medical and life sciences',
                'content_type': 'published',
                'analysis_depth': 'clinical'
            },
            'PLOS': {
                'focus': 'open access scientific research',
                'content_type': 'published',
                'analysis_depth': 'comprehensive'
            },
            'DOAJ': {
                'focus': 'open access academic journals',
                'content_type': 'published',
                'analysis_depth': 'academic'
            },
            'CORE': {
                'focus': 'open access research papers',
                'content_type': 'published',
                'analysis_depth': 'general'
            }
        }

    async def analyze_paper(self, paper_content: str, paper_metadata: Dict[str, Any]) -> PlatformAnalysisResult:
        """플랫폼별 논문 분석 수행"""
        try:
            start_time = time.time()
            platform = paper_metadata.get('platform', 'Unknown')
            
            logger.info(f"논문 분석 시작: {paper_metadata.get('title', 'Unknown')} ({platform})")
            
            # 플랫폼별 설정 가져오기
            platform_config = self.platform_configs.get(platform, self.platform_configs['CORE'])
            
            # 플랫폼별 시스템 프롬프트 생성
            system_prompt = self._generate_platform_system_prompt(platform, platform_config)
            
            # 섹션별 분석
            sections = self._extract_sections(paper_content, platform)
            
            # 구조화된 분석 수행
            analysis_tasks = [
                self._generate_platform_summary(sections, paper_metadata, platform_config),
                self._extract_platform_methodology(sections, platform_config),
                self._identify_platform_findings(sections, platform_config),
                self._extract_platform_limitations(sections, platform_config),
                self._suggest_platform_future_work(sections, platform_config),
                self._extract_platform_keywords(paper_content, paper_metadata, platform_config)
            ]
            
            results = []
            for task in analysis_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    logger.error(f"분석 작업 실패: {e}")
                    results.append(None)
            
            # 결과 통합
            summary, methodology, findings, limitations, future_work, keywords = results
            
            # 플랫폼별 인사이트 추출
            insights = await self._extract_platform_insights(summary, findings, platform_config)
            
            # 신뢰도 점수 계산
            confidence = self._calculate_confidence_score(results, platform)
            
            analysis_result = PlatformAnalysisResult(
                paper_id=paper_metadata.get('id', ''),
                title=paper_metadata.get('title', ''),
                platform=platform,
                summary=summary or "분석 실패",
                key_insights=insights or [],
                methodology=methodology or "방법론 추출 실패",
                main_findings=findings or [],
                limitations=limitations or [],
                future_work=future_work or [],
                technical_keywords=keywords or [],
                confidence_score=confidence,
                analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            execution_time = time.time() - start_time
            logger.info(f"논문 분석 완료 - 시간: {execution_time:.2f}s, 신뢰도: {confidence:.2f}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"논문 분석 실패: {e}")
            raise

    def _generate_platform_system_prompt(self, platform: str, config: Dict[str, str]) -> str:
        """플랫폼별 시스템 프롬프트 생성"""
        return f"""You are an expert AI research assistant specializing in {config['focus']} research analysis.
You are analyzing {config['content_type']} papers from the {platform} platform.
Your analysis should be {config['analysis_depth']} in nature.
Always respond in Korean and provide detailed, accurate analysis appropriate for {platform} content."""

    def _extract_sections(self, content: str, platform: str) -> Dict[str, str]:
        """플랫폼별 섹션 추출"""
        sections = {
            'abstract': '',
            'introduction': '',
            'methodology': '',
            'results': '',
            'conclusion': '',
            'full_text': content
        }
        
        try:
            content_lower = content.lower()
            
            # 플랫폼별 섹션 패턴
            if platform in ['BioRxiv', 'PMC']:
                # 생물학/의학 논문 패턴
                abstract_patterns = [
                    r'abstract[:\s]+(.*?)(?=\n\s*\n|introduction|background|\n1\.)',
                    r'summary[:\s]+(.*?)(?=\n\s*\n|introduction|background|\n1\.)'
                ]
                intro_patterns = [
                    r'(?:introduction|background)[:\s]+(.*?)(?=\n\s*\n|methods?|materials|\n2\.)',
                    r'배경[:\s]+(.*?)(?=\n\s*\n|방법|재료|\n2\.)'
                ]
            elif platform in ['PLOS', 'DOAJ']:
                # 학술 저널 패턴
                abstract_patterns = [
                    r'abstract[:\s]+(.*?)(?=\n\s*\n|introduction|키워드|\n1\.)',
                    r'요약[:\s]+(.*?)(?=\n\s*\n|서론|키워드|\n1\.)'
                ]
                intro_patterns = [
                    r'introduction[:\s]+(.*?)(?=\n\s*\n|methodology|literature|\n2\.)',
                    r'서론[:\s]+(.*?)(?=\n\s*\n|방법론|문헌|\n2\.)'
                ]
            else:
                # 기본 패턴 (ArXiv, CORE)
                abstract_patterns = [
                    r'abstract[:\s]+(.*?)(?=\n\s*\n|introduction|\n1\.)',
                    r'요약[:\s]+(.*?)(?=\n\s*\n|서론|\n1\.)'
                ]
                intro_patterns = [
                    r'introduction[:\s]+(.*?)(?=\n\s*\n|methodology|method|\n2\.)',
                    r'서론[:\s]+(.*?)(?=\n\s*\n|방법론|방법|\n2\.)'
                ]
            
            # Abstract 추출
            for pattern in abstract_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    sections['abstract'] = match.group(1).strip()
                    break
            
            # Introduction 추출
            for pattern in intro_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    sections['introduction'] = match.group(1).strip()
                    break
            
            logger.info(f"플랫폼별 섹션 추출 완료 ({platform}) - Abstract: {bool(sections['abstract'])}, Intro: {bool(sections['introduction'])}")
            
        except Exception as e:
            logger.error(f"섹션 추출 실패: {e}")
        
        return sections

    async def _generate_platform_summary(self, sections: Dict[str, str], metadata: Dict[str, Any], config: Dict[str, str]) -> str:
        """논문 요약 생성"""
        # System prompt is now handled by _generate_platform_system_prompt
        user_prompt = f"""Instructions:
        다음 {config['focus']} 관련 논문을 한국어로 요약해주세요.
        요약은 논문의 핵심 내용만을 포함하며, 간결하고 명확하게 작성되어야 합니다.
        다른 어떠한 추가 텍스트나 포맷팅 없이 오직 요약 내용만을 반환해주세요.
        """
        user_input = sections.get('abstract', sections.get('introduction', sections.get('full_text', '')))

        try:
            response = await self.llm_client.chat_completion(
                system_prompt=self._generate_platform_system_prompt(metadata.get('platform', 'Unknown'), config),
                user_prompt=f"{user_prompt}\nPaper Content:\n{user_input}" # Combine user instruction with content
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"요약 생성 실패: {e}")
            return "분석 실패"

    async def _extract_platform_methodology(self, sections: Dict[str, str], config: Dict[str, str]) -> str:
        """플랫폼별 방법론 추출"""
        try:
            content = sections.get('methodology', '') or sections.get('full_text', '')[:2000]
            platform_focus = config['focus']
            
            prompt = f"""다음 {platform_focus} 연구의 방법론을 한국어로 추출하고 정리해주세요:

{content}

방법론 추출 요구사항 ({platform_focus} 관점):
1. {platform_focus} 분야의 주요 기법과 방법
2. 실험 설계 및 데이터 수집 방법
3. 분석 도구 및 평가 지표
4. {platform_focus} 분야에서의 표준 프로토콜
5. 구체적이고 명확하게 기술

방법론:"""
            
            return await self.llm_client.generate_response(prompt)
            
        except Exception as e:
            logger.error(f"방법론 추출 실패: {e}")
            return None

    async def _identify_platform_findings(self, sections: Dict[str, str], config: Dict[str, str]) -> List[str]:
        """플랫폼별 핵심 발견사항 추출"""
        try:
            content = sections.get('results', '') or sections.get('full_text', '')[:2000]
            platform_focus = config['focus']
            
            prompt = f"""다음 {platform_focus} 연구의 핵심 결과를 한국어로 추출해주세요:

{content}

추출 요구사항 ({platform_focus} 관점):
1. {platform_focus} 분야의 주요 실험 결과 3-5개
2. 정량적 성과 지표 및 통계적 유의성
3. {platform_focus}에서의 실용적 의미
4. 각 결과를 한 문장으로 요약
5. JSON 형식으로 리스트 반환: ["결과1", "결과2", "결과3"]

핵심 결과:"""
            
            response = await self.llm_client.generate_response(prompt)
            
            try:
                import re
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    findings = json.loads(json_match.group())
                    if isinstance(findings, list):
                        return findings
            except:
                pass
            
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            clean_lines = []
            for line in lines:
                if not line.startswith(('#', '-', '*', '```', 'json')):
                    if line.startswith(('•', '1.', '2.', '3.', '4.', '5.')):
                        line = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    clean_lines.append(line)
            return clean_lines[:5]
            
            return []
            
        except Exception as e:
            logger.error(f"핵심 발견사항 추출 실패: {e}")
            return []

    async def _extract_platform_limitations(self, sections: Dict[str, str], config: Dict[str, str]) -> List[str]:
        """플랫폼별 연구 한계점 추출"""
        try:
            content = sections.get('conclusion', '') or sections.get('full_text', '')[-1000:]
            platform_focus = config['focus']
            
            prompt = f"""다음 {platform_focus} 연구의 한계점을 한국어로 추출해주세요:

{content}

추출 요구사항 ({platform_focus} 관점):
1. {platform_focus} 방법론의 한계
2. 데이터나 실험의 제약사항
3. {platform_focus} 분야에서의 일반화 한계
4. 윤리적 또는 실용적 제약
5. JSON 형식으로 리스트 반환: ["한계1", "한계2", "한계3"]

한계점:"""
            
            response = await self.llm_client.generate_response(prompt)
            
            try:
                import re
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    limitations = json.loads(json_match.group())
                    if isinstance(limitations, list):
                        return limitations
            except:
                pass
            
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            clean_lines = []
            for line in lines:
                if not line.startswith(('#', '-', '*', '```', 'json')):
                    if line.startswith(('•', '1.', '2.', '3.', '4.', '5.')):
                        line = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    clean_lines.append(line)
            return clean_lines[:5]
            
            return []
            
        except Exception as e:
            logger.error(f"한계점 추출 실패: {e}")
            return []

    async def _suggest_platform_future_work(self, sections: Dict[str, str], config: Dict[str, str]) -> List[str]:
        """플랫폼별 향후 연구 방향 제안"""
        try:
            content = sections.get('conclusion', '') or sections.get('full_text', '')[-1000:]
            platform_focus = config['focus']
            
            prompt = f"""다음 {platform_focus} 연구를 바탕으로 향후 연구 방향을 한국어로 제안해주세요:

{content}

제안 요구사항 ({platform_focus} 관점):
1. {platform_focus} 분야의 확장 방향
2. 해결되지 않은 기술적 문제들
3. {platform_focus}에서의 새로운 연구 기회
4. 실용화 및 상용화 가능성
5. JSON 형식으로 리스트 반환: ["방향1", "방향2", "방향3"]

향후 연구:"""
            
            response = await self.llm_client.generate_response(prompt)
            
            try:
                import re
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    future_work = json.loads(json_match.group())
                    if isinstance(future_work, list):
                        return future_work
            except:
                pass
            
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            clean_lines = []
            for line in lines:
                if not line.startswith(('#', '-', '*', '```', 'json')):
                    if line.startswith(('•', '1.', '2.', '3.', '4.', '5.')):
                        line = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    clean_lines.append(line)
            return clean_lines[:5]
            
            return []
            
        except Exception as e:
            logger.error(f"향후 연구 방향 제안 실패: {e}")
            return []

    async def _extract_platform_keywords(self, content: str, metadata: Dict[str, Any], config: Dict[str, str]) -> List[str]:
        """플랫폼별 기술 키워드 추출"""
        try:
            platform_focus = config['focus']
            
            prompt = f"""다음 {platform_focus} 관련 논문에서 핵심 기술 키워드를 추출해주세요:

제목: {metadata.get('title', '')}
내용 샘플: {content[:1500]}

추출 요구사항 ({platform_focus} 관점):
1. {platform_focus} 분야의 전문 용어
2. 사용된 알고리즘 및 기술명
3. {platform_focus} 도메인 특화 용어
4. 영문과 한글 모두 포함
5. JSON 형식으로 리스트 반환: ["키워드1", "키워드2"]

키워드:"""
            
            response = await self.llm_client.generate_response(prompt)
            
            try:
                keywords = json.loads(response)
                if isinstance(keywords, list):
                    return keywords[:20]
            except:
                words = re.findall(r'\b[A-Za-z가-힣]{2,}\b', response)
                return list(set(words))[:20]
            
            return []
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return []

    async def _extract_platform_insights(self, summary: str, findings: List[str], config: Dict[str, str]) -> List[str]:
        """플랫폼별 핵심 인사이트 추출"""
        try:
            findings_text = '\n'.join(findings) if findings else '없음'
            platform_focus = config['focus']
            
            prompt = f"""다음 {platform_focus} 연구 요약과 결과를 바탕으로 핵심 인사이트를 추출해주세요:

요약: {summary}
주요 결과: {findings_text}

인사이트 요구사항 ({platform_focus} 관점):
1. {platform_focus} 분야에서의 혁신성
2. {platform_focus} 실무에서의 활용 가능성
3. {platform_focus} 학술 발전에의 기여도
4. 사회적/경제적 파급효과
5. JSON 형식으로 리스트 반환: ["인사이트1", "인사이트2"]

핵심 인사이트:"""
            
            response = await self.llm_client.generate_response(prompt)
            
            try:
                import re
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    insights = json.loads(json_match.group())
                    if isinstance(insights, list):
                        return insights
            except:
                pass
            
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            clean_lines = []
            for line in lines:
                if not line.startswith(('#', '-', '*', '```', 'json')):
                    if line.startswith(('•', '1.', '2.', '3.', '4.', '5.')):
                        line = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    clean_lines.append(line)
            return clean_lines[:5]
            
            return []
            
        except Exception as e:
            logger.error(f"인사이트 추출 실패: {e}")
            return []

    def _calculate_confidence_score(self, results: List[Any], platform: str) -> float:
        """플랫폼별 신뢰도 점수 계산"""
        try:
            non_null_count = sum(1 for result in results if result is not None)
            total_count = len(results)
            
            base_score = non_null_count / total_count if total_count > 0 else 0.0
            
            # 플랫폼별 가중치 적용
            platform_weights = {
                'ArXiv': 0.9,      # preprint이므로 약간 낮음
                'BioRxiv': 0.85,   # preprint이므로 약간 낮음
                'PMC': 1.0,        # 검증된 논문
                'PLOS': 1.0,       # 검증된 논문
                'DOAJ': 0.95,      # 다양한 품질
                'CORE': 0.9        # 다양한 품질
            }
            
            platform_weight = platform_weights.get(platform, 0.9)
            base_score *= platform_weight
            
            # 내용 품질 기반 조정
            if results[0]:  # summary 존재
                base_score += 0.05
            if results[2] and len(results[2]) >= 3:  # findings 3개 이상
                base_score += 0.05
            if results[5] and len(results[5]) >= 5:  # keywords 5개 이상
                base_score += 0.05
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"신뢰도 점수 계산 실패: {e}")
            return 0.5
