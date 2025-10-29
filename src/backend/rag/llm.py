from typing import List, Dict, Any
import os
from ..config import settings

# Simple LLM multiplexor: mock (default), ollama (local), or OpenAI/Anthropic via API


class LLM:
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.ollama_model
        self._client: Any = None

        if self.provider == "mock":
            self._client = object()
        elif self.provider == "openai":
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            from anthropic import Anthropic  # type: ignore
            self._client = Anthropic(api_key=settings.anthropic_api_key)
        elif self.provider == "ollama":
            import ollama  # type: ignore
            self._client = ollama

    def generate(self, prompt: str) -> str:
        if self.provider == "mock":
            # Extract facts from the prompt and generate a better mock answer
            lines = prompt.split("\n")
            fact_lines = [l for l in lines if l.strip().startswith("[")]
            
            if fact_lines:
                # Generate a mock answer that summarizes the facts
                answer = (
                    f"Based on the {len(fact_lines)} sources found, here's what I learned: "
                    f"{fact_lines[0].split('|')[0] if '|' in fact_lines[0] else 'Information available from trusted sources'}. "
                    f"The evidence suggests this is well-documented across multiple reliable websites [1][2][3]. "
                    f"For more detailed information, please refer to the cited sources below."
                )
            else:
                answer = "I found relevant information from web sources. Please check the citations below for details [1][2][3]."
            
            print(f"[MOCK LLM] Generated answer ({len(answer)} chars): {answer[:100]}...")
            return answer
        elif self.provider == "ollama":
            res = self._client.generate(model=self.model, prompt=prompt)
            return res["response"]
        elif self.provider == "openai":
            chat = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return chat.choices[0].message.content
        elif self.provider == "anthropic":
            msg = self._client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return msg.content[0].text
        else:
            raise ValueError("Unsupported LLM provider")
    
    def generate_stream(self, prompt: str):
        """Stream generation token by token."""
        if self.provider == "mock":
            # For mock, just yield the whole answer in one chunk
            answer = self.generate(prompt)
            yield answer
        elif self.provider == "ollama":
            stream = self._client.generate(model=self.model, prompt=prompt, stream=True)
            for chunk in stream:
                if chunk.get("response"):
                    yield chunk["response"]
        elif self.provider == "openai":
            stream = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        elif self.provider == "anthropic":
            with self._client.messages.stream(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            ) as stream:
                for text in stream.text_stream:
                    yield text
        else:
            raise ValueError("Unsupported LLM provider")
