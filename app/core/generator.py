"""Answer generation with offline and LLM modes."""

from typing import List, Dict, Any, Optional
import openai
import httpx
from anthropic import Anthropic

from app.core.citations import CitationExtractor
from app.utils.tokens import count_tokens, truncate_to_tokens
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AnswerGenerator:
    """Generate answers from retrieved context."""
    
    def __init__(
        self,
        offline_mode: bool = True,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        max_context_tokens: int = 2000,
    ):
        self.offline_mode = offline_mode
        self.provider = provider
        self.api_key = api_key
        self.max_context_tokens = max_context_tokens
        self.citation_extractor = CitationExtractor()
        
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        self.mistral_client = None
        
        if not offline_mode and api_key:
            if provider == "openai":
                openai.api_key = api_key
                self.openai_client = openai
            elif provider == "anthropic":
                self.anthropic_client = Anthropic(api_key=api_key)
            elif provider == "mistral":
                # Mistral uses HTTP client
                self.mistral_client = httpx.AsyncClient(
                    base_url="https://api.mistral.ai/v1",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
    
    async def initialize(self):
        """Initialize generator."""
        logger.info(f"Answer generator initialized (mode: {'offline' if self.offline_mode else self.provider})")
    
    async def generate(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate answer from query and contexts."""
        if not contexts:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "citations": [],
                "mode": mode or ("offline" if self.offline_mode else self.provider),
                "confidence": 0.0,
            }
        
        # Prepare context
        context_text = self._prepare_context(contexts)
        
        # Generate answer
        if self.offline_mode or mode == "offline":
            answer = await self._generate_offline(query, context_text, contexts)
        else:
            answer = await self._generate_with_llm(query, context_text)
        
        # Extract citations
        citations = self.citation_extractor.extract(answer, contexts)
        
        return {
            "answer": answer,
            "citations": citations,
            "contexts": contexts,
            "mode": mode or ("offline" if self.offline_mode else self.provider),
            "confidence": self._calculate_confidence(contexts),
        }
    
    def _prepare_context(self, contexts: List[Dict[str, Any]]) -> str:
        """Prepare context text from retrieved chunks."""
        context_parts = []
        total_tokens = 0
        
        for i, ctx in enumerate(contexts, 1):
            # Format context with source info
            context_part = f"[{i}] From '{ctx['filename']}':\n{ctx['text']}\n"
            
            # Check token limit
            part_tokens = count_tokens(context_part)
            if total_tokens + part_tokens > self.max_context_tokens:
                break
            
            context_parts.append(context_part)
            total_tokens += part_tokens
        
        return "\n".join(context_parts)
    
    async def _generate_offline(
        self,
        query: str,
        context: str,
        contexts: List[Dict[str, Any]]
    ) -> str:
        """Generate answer in offline mode using extractive summarization."""
        # Simple extractive approach: find most relevant sentences
        sentences = []
        
        for ctx in contexts[:3]:  # Use top 3 contexts
            text = ctx["text"]
            # Split into sentences
            text_sentences = text.split(". ")
            
            # Score sentences based on query terms
            query_terms = set(query.lower().split())
            scored_sentences = []
            
            for sent in text_sentences:
                sent_terms = set(sent.lower().split())
                overlap = len(query_terms & sent_terms)
                if overlap > 0:
                    scored_sentences.append((sent, overlap))
            
            # Add top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            sentences.extend([s[0] for s in scored_sentences[:2]])
        
        if not sentences:
            return "Based on the available documents, I cannot provide a specific answer to your question."
        
        # Combine sentences
        answer = ". ".join(sentences[:3])
        if not answer.endswith("."):
            answer += "."
        
        return f"Based on the indexed documents: {answer}"
    
    async def _generate_with_llm(self, query: str, context: str) -> str:
        """Generate answer using LLM API."""
        prompt = self._build_prompt(query, context)
        
        try:
            if self.provider == "openai" and self.openai_client:
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic" and self.anthropic_client:
                response = await self._call_anthropic(prompt)
            elif self.provider == "mistral" and self.mistral_client:
                response = await self._call_mistral(prompt)
            else:
                return await self._generate_offline(query, context, [])
            
            return response
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I encountered an error generating the answer. Please try again."
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for LLM."""
        return f"""You are a helpful assistant answering questions based on provided context.
Answer the question using ONLY the information provided in the context below.
If the context doesn't contain relevant information, say so clearly.
Include citations in [1], [2] format when referencing specific sources.

Context:
{context}

Question: {query}

Answer:"""
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        response = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _call_mistral(self, prompt: str) -> str:
        """Call Mistral API."""
        response = await self.mistral_client.post(
            "/chat/completions",
            json={
                "model": "mistral-tiny",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3,
            }
        )
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _calculate_confidence(self, contexts: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on context relevance."""
        if not contexts:
            return 0.0
        
        # Average of top context scores
        scores = [ctx.get("score", 0.0) for ctx in contexts[:3]]
        return sum(scores) / len(scores) if scores else 0.0