from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx


class LLMQueryError(RuntimeError):
    pass


@dataclass
class OllamaAdapter:
    base_url: str
    model: str
    timeout: float
    default_max_concurrency: int

    def __post_init__(self) -> None:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    def query(self, prompt: str) -> str:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMQueryError(f"Ollama query failed: {exc}") from exc

        answer = data.get("response")
        if not isinstance(answer, str):
            raise LLMQueryError("Ollama response has no text field 'response'.")
        return answer

    async def query_async(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMQueryError(f"Ollama query failed: {exc}") from exc

        answer = data.get("response")
        if not isinstance(answer, str):
            raise LLMQueryError("Ollama response has no text field 'response'.")
        return answer

    async def query_many_async(
        self,
        prompts: list[str],
        max_concurrency: int | None = None,
    ) -> list[str]:
        limit = max_concurrency or self.default_max_concurrency
        semaphore = asyncio.Semaphore(limit)

        async def _one(prompt: str) -> str:
            async with semaphore:
                return await self.query_async(prompt)

        tasks = [_one(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    def query_many(
        self,
        prompts: list[str],
        max_concurrency: int | None = None,
    ) -> list[str]:
        return asyncio.run(self.query_many_async(prompts, max_concurrency=max_concurrency))
