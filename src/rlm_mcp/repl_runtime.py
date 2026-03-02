from __future__ import annotations

import asyncio
import io
import json
import traceback
import uuid
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from typing import Any

from .llm_adapter import OllamaAdapter


@dataclass
class ReplExecutionResult:
    stdout: str
    stderr: str
    error: str | None
    final: str | None
    llm_trace: list[dict[str, Any]]


class ReplRuntime:
    def __init__(
        self,
        memory_context: dict[str, str],
        llm_adapter: OllamaAdapter,
        *,
        trace_preview_chars: int = 280,
        trace_persist: bool = False,
        trace_file: Path | None = None,
        local_iter_log_enabled: bool = True,
        local_iter_log_file: Path | None = None,
        local_iter_log_preview_chars: int = 420,
        local_llm_force_english: bool = True,
    ):
        self.memory_context = memory_context
        self.llm_adapter = llm_adapter
        self.final_value: str | None = None
        self.trace_preview_chars = trace_preview_chars
        self.trace_persist = trace_persist
        self.trace_file = trace_file
        self.local_iter_log_enabled = local_iter_log_enabled
        self.local_iter_log_file = local_iter_log_file
        self.local_iter_log_preview_chars = max(80, local_iter_log_preview_chars)
        self.local_llm_force_english = local_llm_force_english
        self.execution_id: str | None = None
        self.execution_trace: list[dict[str, Any]] = []
        self.globals: dict[str, Any] = {
            "__builtins__": __builtins__,
            "memory_context": self.memory_context,
            "llm_query": self._llm_query,
            "llm_query_many": self._llm_query_many,
            "FINAL": self._final,
            "FINAL_VAR": self._final_var,
            "asyncio": asyncio,
        }

    def refresh_memory(self, memory_context: dict[str, str]) -> None:
        self.memory_context = memory_context
        self.globals["memory_context"] = self.memory_context

    def _final(self, text: Any) -> None:
        self.final_value = "" if text is None else str(text)

    def _final_var(self, var_name: str) -> None:
        if var_name not in self.globals:
            raise NameError(f"FINAL_VAR: variable '{var_name}' not found in REPL globals")
        value = self.globals[var_name]
        self.final_value = "" if value is None else str(value)

    def _clip(self, text: str) -> str:
        limit = max(64, self.trace_preview_chars)
        if len(text) <= limit:
            return text
        return f"{text[:limit]}...<truncated:{len(text) - limit}>"

    def _clip_local(self, text: str) -> str:
        limit = self.local_iter_log_preview_chars
        if len(text) <= limit:
            return text
        return f"{text[:limit]}...<truncated:{len(text) - limit}>"

    def _prepare_local_prompt(self, prompt: str) -> str:
        if not self.local_llm_force_english:
            return prompt
        directive = (
            "System instruction: Respond in English only. "
            "Do not switch language even if the input is in another language.\n\n"
        )
        return directive + prompt

    def _local_log_reset(self, call_type: str, meta: dict[str, Any] | None = None) -> None:
        if not self.local_iter_log_enabled or not self.local_iter_log_file:
            return
        self.local_iter_log_file.parent.mkdir(parents=True, exist_ok=True)
        header = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "execution_id": self.execution_id,
            "call_type": call_type,
            "event": "request_start",
        }
        if meta:
            header.update(meta)
        self.local_iter_log_file.write_text(
            json.dumps(header, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _local_log_append(self, payload: dict[str, Any]) -> None:
        if not self.local_iter_log_enabled or not self.local_iter_log_file:
            return
        payload = dict(payload)
        payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
        payload.setdefault("execution_id", self.execution_id)
        with self.local_iter_log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _append_trace(
        self,
        *,
        call_type: str,
        prompt_preview: str,
        response_preview: str = "",
        prompt_chars: int = 0,
        response_chars: int = 0,
        ok: bool = True,
        error: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        event: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "execution_id": self.execution_id,
            "call_type": call_type,
            "ok": ok,
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
            "prompt_preview": self._clip(prompt_preview),
            "response_preview": self._clip(response_preview),
        }
        if error:
            event["error"] = error
        if meta:
            event.update(meta)

        self.execution_trace.append(event)

    def _persist_trace(self) -> None:
        if not self.trace_persist or not self.trace_file or not self.execution_trace:
            return
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        with self.trace_file.open("a", encoding="utf-8") as f:
            for event in self.execution_trace:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _llm_query(self, prompt: str) -> str:
        self._local_log_reset("llm_query", meta={"prompt_chars": len(prompt)})
        self._local_log_append(
            {
                "event": "iteration",
                "iteration": 0,
                "prompt_preview": self._clip_local(prompt),
            }
        )
        try:
            wrapped_prompt = self._prepare_local_prompt(prompt)
            answer = self.llm_adapter.query(wrapped_prompt)
            self._local_log_append(
                {
                    "event": "response",
                    "iteration": 0,
                    "response_preview": self._clip_local(answer),
                    "response_chars": len(answer),
                    "ok": True,
                }
            )
            self._append_trace(
                call_type="llm_query",
                prompt_preview=prompt,
                response_preview=answer,
                prompt_chars=len(prompt),
                response_chars=len(answer),
                ok=True,
            )
            return answer
        except Exception as exc:
            self._local_log_append(
                {
                    "event": "response",
                    "iteration": 0,
                    "ok": False,
                    "error": str(exc),
                }
            )
            self._append_trace(
                call_type="llm_query",
                prompt_preview=prompt,
                response_preview="",
                prompt_chars=len(prompt),
                response_chars=0,
                ok=False,
                error=str(exc),
            )
            raise

    def _run_coro_sync(self, coro: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                result: dict[str, Any] = {}

                def _runner() -> None:
                    result["value"] = asyncio.run(coro)

                thread = Thread(target=_runner, daemon=True)
                thread.start()
                thread.join()
                return result.get("value")
        except RuntimeError:
            pass

        return asyncio.run(coro)

    def _llm_query_many(self, prompts: list[str], max_concurrency: int | None = None) -> list[str]:
        self._local_log_reset(
            "llm_query_many",
            meta={"batch_size": len(prompts), "max_concurrency": max_concurrency},
        )
        for idx, prompt in enumerate(prompts):
            self._local_log_append(
                {
                    "event": "iteration",
                    "iteration": idx,
                    "prompt_preview": self._clip_local(prompt),
                    "prompt_chars": len(prompt),
                }
            )
        try:
            wrapped_prompts = [self._prepare_local_prompt(prompt) for prompt in prompts]
            answers = self._run_coro_sync(
                self.llm_adapter.query_many_async(wrapped_prompts, max_concurrency=max_concurrency)
            )
            answers = answers or []

            for index, prompt in enumerate(prompts):
                response = answers[index] if index < len(answers) else ""
                self._local_log_append(
                    {
                        "event": "response",
                        "iteration": index,
                        "ok": index < len(answers),
                        "response_preview": self._clip_local(response),
                        "response_chars": len(response),
                    }
                )
                self._append_trace(
                    call_type="llm_query_many:item",
                    prompt_preview=prompt,
                    response_preview=response,
                    prompt_chars=len(prompt),
                    response_chars=len(response),
                    ok=index < len(answers),
                    meta={
                        "batch_index": index,
                        "batch_size": len(prompts),
                        "max_concurrency": max_concurrency,
                    },
                )

            return answers
        except Exception as exc:
            self._local_log_append(
                {
                    "event": "response",
                    "iteration": -1,
                    "ok": False,
                    "error": str(exc),
                }
            )
            self._append_trace(
                call_type="llm_query_many",
                prompt_preview=f"batch_size={len(prompts)}",
                response_preview="",
                prompt_chars=sum(len(p) for p in prompts),
                response_chars=0,
                ok=False,
                error=str(exc),
                meta={"batch_size": len(prompts), "max_concurrency": max_concurrency},
            )
            raise

    def execute(self, code: str) -> ReplExecutionResult:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        self.final_value = None
        self.execution_id = str(uuid.uuid4())
        self.execution_trace = []
        error_text: str | None = None

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, self.globals, self.globals)
        except Exception:
            error_text = traceback.format_exc()
        finally:
            self._persist_trace()

        return ReplExecutionResult(
            stdout=stdout_buffer.getvalue(),
            stderr=stderr_buffer.getvalue(),
            error=error_text,
            final=self.final_value,
            llm_trace=self.execution_trace,
        )
