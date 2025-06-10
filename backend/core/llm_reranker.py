import os
import logging
import requests
from typing import List, Dict, Any, Optional
import json
import re

logger = logging.getLogger(__name__)

class LLMReranker:
    def __init__(self, lm_studio_base_url: str = "http://127.0.0.1:1234/v1", model_name: str = "open-solar-ko-10.7b"):
        self.base_url = lm_studio_base_url
        self.model_name = model_name
        logger.info(f"LLMReranker initialized for LM Studio at {self.base_url} with model: {self.model_name}")

    def _format_papers_for_prompt(self, papers: List[Dict[str, Any]]) -> str:
        formatted_papers = []
        for i, paper in enumerate(papers):
            # 초록은 700자 내로 요약 후 넣기
            abstract_summary = paper.get("abstract", "")
            if len(abstract_summary) > 700:
                abstract_summary = abstract_summary[:700] + "..."
            
            formatted_papers.append(
                f"### Paper {i+1}\n"
                f"Title: {paper.get("title", "N/A")}\n"
                f"Authors: {', '.join(paper.get("authors", []))}\n"
                f"Abstract: {abstract_summary}\n"
                f"Categories: {', '.join(paper.get("categories", []))}\n"
                f"PDF URL: {paper.get("pdf_url", "N/A")}\n"
            )

        return "\n\n".join(formatted_papers)

    def rerank_and_explain(self, user_interests: List[str], papers: List[Dict[str, Any]], top_k: int = 50) -> List[Dict[str, Any]]:
        if not papers:
            return []
        
        # 사용자 관심사를 문자열로 변환
        topics_str = ", ".join(user_interests) if user_interests else "general research papers"
        
        # 리스트형 프롬프트 구성
        formatted_papers_str = self._format_papers_for_prompt(papers)

        # 프롬프트에서 JSON 형식에 대한 지시를 더 명확하게 합니다.
        prompt_template = f"""Rank the following papers from 0 to 10 based on their relevance to the user's interests: {topics_str}.
For each paper, provide a score and a concise one-sentence explanation of why it is relevant.
Your output MUST be a JSON array of objects.
Each object in the array MUST be a valid JSON object containing \"paper_id\" (string), \"score\" (float from 0-10), and \"explanation\" (string, one sentence).
All keys and string values in the JSON output MUST be enclosed in double quotes.
DO NOT include any introductory or conversational text, or any other formatting outside the JSON array.
Ensure the output can be directly parsed by json.loads().

Papers to rank:
{formatted_papers_str}

Example Output:
[
  {{\"paper_id\": \"1234.5678\", \"score\": 9.5, \"explanation\": \"This paper is highly relevant due to its focus on novel deep learning architectures for natural language processing.\"}},
  {{\"paper_id\": \"9876.5432\", \"score\": 7.0, \"explanation\": \"This paper presents a new approach to data privacy, which aligns with the user's interest in data security.\"}}
]
"""

        messages = [
            {"role": "system", "content": "You are a precise JSON output generator for academic paper ranking. Only output the requested JSON."},
            {"role": "user", "content": prompt_template}
        ]

        try:
            logger.info(f"Sending {len(papers)} papers to LM Studio for re-ranking and explanation.")
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "messages": messages,
                "model": self.model_name,
            }

            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            
            # Log raw response BEFORE checking for status to see content on error
            if not response.ok:
                logger.error(f"LM Studio API Error (Status {response.status_code}): {response.text}")

            response.raise_for_status() # Raise an exception for HTTP errors
            
            response_data = response.json()
            response_content = response_data['choices'][0]['message']['content']
            
            logger.info(f"Raw LM Studio Response: {response_content}") # Log raw response for debugging

            # Attempt to extract JSON from the text, handling potential variations
            # Remove any special characters like \x0A and then extract the JSON array
            cleaned_response_content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', response_content) # Remove control characters
            
            # Find the first and last bracket to extract the JSON array
            match = re.search(r'\[.*\]', cleaned_response_content, re.DOTALL)
            if match:
                json_string = match.group(0).strip()
            else:
                raise json.JSONDecodeError("No JSON array found in response", cleaned_response_content, 0)
            
            reranked_data = json.loads(json_string)
            
            # Combine original paper data with LLM's scores and explanations
            paper_id_map = {p['paper_id']: p for p in papers}
            final_results = []
            for item in reranked_data:
                paper_id = item.get('paper_id')
                if paper_id and paper_id in paper_id_map:
                    original_paper = paper_id_map[paper_id]
                    original_paper['llm_score'] = item.get('score')
                    original_paper['llm_explanation'] = item.get('explanation')
                    final_results.append(original_paper)
            
            # Sort by LLM score in descending order
            final_results.sort(key=lambda x: x.get('llm_score', 0), reverse=True)

            return final_results[:top_k] # Return top_k after re-ranking

        except requests.exceptions.RequestException as req_e:
            logger.error(f"HTTP request error during LLM re-ranking: {req_e}")
            if hasattr(req_e, 'response') and req_e.response is not None:
                logger.error(f"LM Studio API Error Response Content: {req_e.response.text}")
            return []
        except json.JSONDecodeError as json_e:
            logger.error(f"JSON decode error from LLM response: {json_e} - Response: {response_content}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return []

    # Original rerank_and_explain (renamed for now, will be restored)
    def _original_rerank_and_explain(self, user_interests: List[str], papers: List[Dict[str, Any]], top_k: int = 50) -> List[Dict[str, Any]]:
        # This method is temporarily stored here and will be restored later.
        # Its content is the original rerank_and_explain logic.
        return [] # Placeholder 