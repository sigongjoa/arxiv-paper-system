"""Paper Analysis Agent for arXiv Research System"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import time
from .lm_studio_client import LMStudioClient

logger = logging.getLogger(__name__)

@dataclass
class PaperAnalysisResult:
    """논문 분석 결과"""
    paper_id: str
    title: str
    summary: str
    key_insights: List[str]
    methodology: str
    main_findings: List[str]
    limitations: List[str]
    future_work: List[str]
    technical_keywords: List[str]
    confidence_score: float
    analysis_timestamp: str

class PaperAnalysisAgent:
    """논문 분석 AI 에이전트"""
    
    def __init__(self, llm_client: LMStudioClient):
        self.llm_client = llm_client
        self.system_prompt = """You are an expert AI research assistant specializing in academic paper analysis.
Your task is to analyze scientific papers and extract structured insights.
Always respond in Korean and provide detailed, accurate analysis."""

    async def analyze_paper(self, paper_content: str, paper_metadata: Dict[str, Any]) -> PaperAnalysisResult:
        """논문 분석 수행"""
        try:
            start_time = time.time()
            logger.info(f"논문 분석 시작: {paper_metadata.get('title', 'Unknown')}")
            
            # 섹션별 분석
            sections = self._extract_sections(paper_content)
            
            # 구조화된 분석 수행
            analysis_tasks = [
                self._generate_summary(sections, paper_metadata),
                self._extract_methodology(sections),
                self._identify_key_findings(sections),
                self._extract_limitations(sections),
                self._suggest_future_work(sections),
                self._extract_keywords(paper_content, paper_metadata)
            ]
            
            results = []
            for task in analysis_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    logger.error(f"분석 작업 실패: {e}", exc_info=True)
                    results.append(None)
            
            # 결과 통합
            summary, methodology, findings, limitations, future_work, keywords = results
            
            # 인사이트 추출
            insights = await self._extract_insights(summary, findings)
            
            # 신뢰도 점수 계산
            confidence = self._calculate_confidence_score(results)
            
            analysis_result = PaperAnalysisResult(
                paper_id=paper_metadata.get('id', ''),
                title=paper_metadata.get('title', ''),
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
            logger.error(f"논문 분석 실패: {e}", exc_info=True)
            raise

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """논문 섹션 추출"""
        sections = {
            'abstract': '',
            'introduction': '',
            'methodology': '',
            'results': '',
            'conclusion': '',
            'full_text': content
        }
        
        try:
            # 간단한 섹션 추출 로직
            content_lower = content.lower()
            
            # Abstract 추출
            abstract_patterns = [r'abstract[:\s]+(.*?)(?=\n\s*\n|\nintroduction|\n1\.)', 
                               r'요약[:\s]+(.*?)(?=\n\s*\n|서론|\n1\.)']
            for pattern in abstract_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    sections['abstract'] = match.group(1).strip()
                    break
            
            # Introduction 추출
            intro_patterns = [r'introduction[:\s]+(.*?)(?=\n\s*\n|methodology|method|\n2\.)',
                             r'서론[:\s]+(.*?)(?=\n\s*\n|방법론|방법|\n2\.)']
            for pattern in intro_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    sections['introduction'] = match.group(1).strip()
                    break
            
            logger.info(f"섹션 추출 완료 - Abstract: {bool(sections['abstract'])}, Intro: {bool(sections['introduction'])}")
            
        except Exception as e:
            logger.error(f"섹션 추출 실패: {e}", exc_info=True)
        
        return sections

    async def _generate_summary(self, sections: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """논문 요약 생성"""
        try:
            prompt = f"""다음 논문을 한국어로 요약해주세요:

제목: {metadata.get('title', 'Unknown')}
저자: {', '.join(metadata.get('authors', []))}

초록: {sections.get('abstract', '없음')}
서론: {sections.get('introduction', '없음')[:1000]}

요약 요구사항:
1. 연구 목적과 동기
2. 주요 방법론
3. 핵심 결과
4. 연구의 의의
5. 200-300단어로 작성

요약:"""
            
            return await self.llm_client.generate_response(prompt, self.system_prompt)
            
        except Exception as e:
            logger.error(f"요약 생성 실패: {e}", exc_info=True)
            return None

    async def _extract_methodology(self, sections: Dict[str, str]) -> str:
        """방법론 추출"""
        try:
            content = sections.get('methodology', '') or sections.get('full_text', '')[:2000]
            
            prompt = f"""다음 논문 내용에서 방법론을 한국어로 추출하고 정리해주세요:

{content}

방법론 추출 요구사항:
1. 사용된 주요 기법과 알고리즘
2. 실험 설계 및 데이터셋
3. 평가 방법 및 지표
4. 구체적이고 명확하게 기술

방법론:"""
            
            return await self.llm_client.generate_response(prompt, self.system_prompt)
            
        except Exception as e:
            logger.error(f"방법론 추출 실패: {e}", exc_info=True)
            return None

    async def _identify_key_findings(self, sections: Dict[str, str]) -> List[str]:
        """핵심 발견사항 추출"""
        try:
            content = sections.get('results', '') or sections.get('full_text', '')[:2000]
            
            prompt = f"""다음 논문 내용에서 핵심 연구 결과를 한국어로 추출해주세요:

{content}

추출 요구사항:
1. 주요 실험 결과 3-5개
2. 정량적 성과 지표 포함
3. 각 결과를 한 문장으로 요약
4. JSON 형식으로 리스트 반환: ["결과1", "결과2", "결과3"]

핵심 결과:"""
            
            response = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            # JSON 파싱 시도
            try:
                findings = json.loads(response)
                if isinstance(findings, list):
                    return findings
            except:
                # JSON 파싱 실패 시 수동 분할
                lines = response.split('\n')
                return [line.strip() for line in lines if line.strip() and not line.strip().startswith(('#', '-', '*'))]
            
            return []
            
        except Exception as e:
            logger.error(f"핵심 발견사항 추출 실패: {e}", exc_info=True)
            return []

    async def _extract_limitations(self, sections: Dict[str, str]) -> List[str]:
        """연구 한계점 추출"""
        try:
            content = sections.get('conclusion', '') or sections.get('full_text', '')[-1000:]
            
            prompt = f"""다음 논문 내용에서 연구의 한계점을 한국어로 추출해주세요:

{content}

추출 요구사항:
1. 연구 방법론의 한계
2. 데이터나 실험의 제약사항
3. 일반화 가능성의 한계
4. JSON 형식으로 리스트 반환: ["한계1", "한계2", "한계3"]

한계점:"""
            
            response = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            try:
                limitations = json.loads(response)
                if isinstance(limitations, list):
                    return limitations
            except:
                lines = response.split('\n')
                return [line.strip() for line in lines if line.strip() and not line.strip().startswith(('#', '-', '*'))]
            
            return []
            
        except Exception as e:
            logger.error(f"한계점 추출 실패: {e}", exc_info=True)
            return []

    async def _suggest_future_work(self, sections: Dict[str, str]) -> List[str]:
        """향후 연구 방향 제안"""
        try:
            content = sections.get('conclusion', '') or sections.get('full_text', '')[-1000:]
            
            prompt = f"""다음 논문을 바탕으로 향후 연구 방향을 한국어로 제안해주세요:

{content}

제안 요구사항:
1. 현재 연구의 확장 방향
2. 해결되지 않은 문제들
3. 새로운 연구 기회
4. JSON 형식으로 리스트 반환: ["방향1", "방향2", "방향3"]

향후 연구:"""
            
            response = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            try:
                future_work = json.loads(response)
                if isinstance(future_work, list):
                    return future_work
            except:
                lines = response.split('\n')
                return [line.strip() for line in lines if line.strip() and not line.strip().startswith(('#', '-', '*'))]
            
            return []
            
        except Exception as e:
            logger.error(f"향후 연구 방향 제안 실패: {e}", exc_info=True)
            return []

    async def _extract_keywords(self, content: str, metadata: Dict[str, Any]) -> List[str]:
        """기술 키워드 추출"""
        try:
            prompt = f"""다음 논문에서 핵심 기술 키워드를 추출해주세요:

제목: {metadata.get('title', '')}
내용 샘플: {content[:1500]}

추출 요구사항:
1. 기술적 용어 및 방법론
2. 알고리즘 이름
3. 도메인 특화 용어
4. 영문과 한글 모두 포함
5. JSON 형식으로 리스트 반환: ["키워드1", "키워드2"]

키워드:"""
            
            response = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            try:
                keywords = json.loads(response)
                if isinstance(keywords, list):
                    return keywords[:20]  # 최대 20개로 제한
            except:
                words = re.findall(r'\b[A-Za-z가-힣]{2,}\b', response)
                return list(set(words))[:20]
            
            return []
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}", exc_info=True)
            return []

    async def _extract_insights(self, summary: str, findings: List[str]) -> List[str]:
        """핵심 인사이트 추출"""
        try:
            findings_text = '\n'.join(findings) if findings else '없음'
            
            prompt = f"""다음 논문 요약과 결과를 바탕으로 핵심 인사이트를 추출해주세요:

요약: {summary}
주요 결과: {findings_text}

인사이트 요구사항:
1. 연구의 혁신성
2. 실용적 함의
3. 학술적 기여도
4. JSON 형식으로 리스트 반환: ["인사이트1", "인사이트2"]

핵심 인사이트:"""
            
            response = await self.llm_client.generate_response(prompt, self.system_prompt)
            
            try:
                insights = json.loads(response)
                if isinstance(insights, list):
                    return insights
            except:
                lines = response.split('\n')
                return [line.strip() for line in lines if line.strip() and not line.strip().startswith(('#', '-', '*'))]
            
            return []
            
        except Exception as e:
            logger.error(f"인사이트 추출 실패: {e}", exc_info=True)
            return []

    def _calculate_confidence_score(self, results: List[Any]) -> float:
        """신뢰도 점수 계산"""
        try:
            non_null_count = sum(1 for result in results if result is not None)
            total_count = len(results)
            
            base_score = non_null_count / total_count if total_count > 0 else 0.0
            
            # 내용 품질 기반 조정
            if results[0]:  # summary 존재
                base_score += 0.1
            if results[2] and len(results[2]) >= 3:  # findings 3개 이상
                base_score += 0.1
            if results[5] and len(results[5]) >= 5:  # keywords 5개 이상
                base_score += 0.1
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"신뢰도 점수 계산 실패: {e}", exc_info=True)
            return 0.5
