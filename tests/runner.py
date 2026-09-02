"""Multi-provider automated test runner for Disambiguator Skill.

Zero mandatory dependencies (uses Python standard library urllib, json, re, pathlib).
Supports:
  - Google Gemini (native REST API or google-genai SDK)
  - OpenAI & OpenAI-compatible endpoints (Ollama, Groq, DeepSeek, vLLM, OpenRouter)
  - Anthropic Claude (Messages API)
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
import urllib.error
import urllib.request

from tests.parser import TestCase, parse_test_cases

# ---------------------------------------------------------------------------
# Robust .env loader (standard library fallback if python-dotenv not installed)
# ---------------------------------------------------------------------------
def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Standard library fallback
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), val)

_load_env()

JUDGE_SYSTEM_PROMPT = (
    "Sos un evaluador estricto. Se te da una respuesta de un modelo y un conjunto de assertions.\n"
    "Evaluá cada assertion como PASS o FAIL con una línea de razonamiento.\n"
    "Respondé solo en JSON válido, sin texto extra con este schema exacto:\n"
    "{\n"
    '  "assertions_results": { "<assertion_key>": "PASS" | "FAIL", ... },\n'
    '  "result": "PASS" | "FAIL",\n'
    '  "judge_reasoning": "una línea de razonamiento concisa evaluando el cumplimiento"\n'
    "}"
)


def read_system_prompt(repo_root: Path) -> str:
    """Read the canonical system-prompt.md from repository root."""
    path = repo_root / "system-prompt.md"
    if not path.is_file():
        raise FileNotFoundError(f"system-prompt.md not found at {path}")
    return path.read_text(encoding="utf-8")



# ---------------------------------------------------------------------------
# Abstract Provider Interface & Concrete Implementations
# ---------------------------------------------------------------------------
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, model: str, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        """Generate response text given a model, user prompt, and system prompt."""
        pass


class GeminiProvider(LLMProvider):
    """Native Gemini REST API client with zero third-party dependencies."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate(self, model: str, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        # Strip 'models/' prefix if present
        clean_model = model.replace("models/", "")
        url = f"{self.base_url}/{clean_model}:generateContent?key={self.api_key}"

        gen_config: dict[str, Any] = {"temperature": 0.0}
        if json_mode:
            gen_config["responseMimeType"] = "application/json"

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": gen_config,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404 and ("2.0" in clean_model or "1.5" in clean_model):
                fallback_model = "gemini-3.5-flash"
                fallback_url = f"{self.base_url}/{fallback_model}:generateContent?key={self.api_key}"
                fallback_req = urllib.request.Request(
                    fallback_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(fallback_req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            else:
                raise


        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()


class OpenAICompatibleProvider(LLMProvider):
    """Universal client for OpenAI, Ollama, Groq, DeepSeek, vLLM, OpenRouter."""

    def __init__(self, api_key: str | None, base_url: str):
        self.api_key = api_key or "ollama-no-key"
        self.base_url = base_url.rstrip("/")

    def generate(self, model: str, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        url = f"{self.base_url}/chat/completions"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.0,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "").strip()


class AnthropicProvider(LLMProvider):
    """Direct Anthropic Messages API client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.anthropic.com/v1/messages"

    def generate(self, model: str, prompt: str, system_prompt: str, json_mode: bool = False) -> str:
        payload = {
            "model": model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
            "temperature": 0.0,
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content_blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()


def resolve_provider() -> tuple[LLMProvider, str, str]:
    """Auto-detect or configure provider from environment variables."""
    provider_name = os.getenv("PROVIDER", "").lower().strip()

    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base = os.getenv("OPENAI_BASE_URL")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not provider_name:
        if gemini_key:
            provider_name = "gemini"
        elif anthropic_key:
            provider_name = "anthropic"
        elif openai_key or openai_base:
            provider_name = "openai"
        else:
            provider_name = "gemini"

    if provider_name == "gemini":
        if not gemini_key:
            raise ValueError(
                "Gemini provider selected but GEMINI_API_KEY is not set.\n"
                "Please add GEMINI_API_KEY to your .env file."
            )
        default_model = "gemini-3.5-flash"
        test_model = os.getenv("TEST_MODEL", default_model)
        judge_model = os.getenv("JUDGE_MODEL", default_model)
        return GeminiProvider(gemini_key), test_model, judge_model

    elif provider_name in ("openai", "ollama", "groq", "deepseek"):
        base_url = openai_base or "https://api.openai.com/v1"
        default_model = "gpt-4o-mini" if "openai.com" in base_url else "llama3.2"
        test_model = os.getenv("TEST_MODEL", default_model)
        judge_model = os.getenv("JUDGE_MODEL", default_model)
        return OpenAICompatibleProvider(openai_key, base_url), test_model, judge_model

    elif provider_name == "anthropic":
        if not anthropic_key:
            raise ValueError("Anthropic provider selected but ANTHROPIC_API_KEY is not set.")
        default_model = "claude-3-5-sonnet-latest"
        test_model = os.getenv("TEST_MODEL", default_model)
        judge_model = os.getenv("JUDGE_MODEL", default_model)
        return AnthropicProvider(anthropic_key), test_model, judge_model

    else:
        raise ValueError(f"Unsupported PROVIDER '{provider_name}'. Supported: gemini, openai, ollama, anthropic")


def _clean_json_text(text: str) -> str:
    """Extract and parse clean JSON from model output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    # Fallback to finding outermost JSON object if surrounding commentary exists
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0).strip()
    return text.strip()


def run_test_case(
    provider: LLMProvider,
    case: TestCase,
    system_prompt: str,
    test_model: str,
    judge_model: str,
) -> dict[str, Any]:
    """Execute a single test case through TEST_MODEL and evaluate with JUDGE_MODEL."""
    # 1. Model under test
    model_output = provider.generate(
        model=test_model,
        prompt=case.prompt,
        system_prompt=system_prompt,
        json_mode=False,
    )

    # 2. Judge evaluation
    judge_content = (
        f"PROMPT DEL USUARIO:\n{case.prompt}\n\n"
        f"RESPUESTA DEL MODELO BAJO PRUEBA:\n{model_output}\n\n"
        f"ASSERTIONS ESPERADAS:\n{json.dumps(case.assertions, indent=2)}\n\n"
        f"COMPORTAMIENTO ESPERADO SEGÚN ESPECIFICACIÓN:\n{case.expected_behavior}"
    )

    raw_judge_text = provider.generate(
        model=judge_model,
        prompt=judge_content,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        json_mode=True,
    )

    cleaned_judge_text = _clean_json_text(raw_judge_text)

    try:
        judge_data = json.loads(cleaned_judge_text)
    except json.JSONDecodeError:
        judge_data = {
            "assertions_results": {k: "FAIL" for k in case.assertions.keys()},
            "result": "FAIL",
            "judge_reasoning": f"Judge returned invalid JSON: {raw_judge_text[:120]}",
        }

    assertions_results = judge_data.get("assertions_results", {})
    overall_result = judge_data.get("result", "FAIL")
    if any(str(v).upper() != "PASS" for v in assertions_results.values()):
        overall_result = "FAIL"

    return {
        "id": case.id,
        "category": case.category,
        "prompt": case.prompt,
        "response": model_output,
        "assertions_results": assertions_results,
        "result": overall_result,
        "judge_reasoning": judge_data.get("judge_reasoning", ""),
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    system_prompt_path = repo_root / "system-prompt.md"
    if not system_prompt_path.is_file():
        print(f"[ERROR] system-prompt.md not found at: {system_prompt_path}", file=sys.stderr)
        sys.exit(1)

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    test_cases_path = repo_root / "tests" / "test-cases.md"
    cases = parse_test_cases(test_cases_path)

    try:
        provider, test_model, judge_model = resolve_provider()
    except ValueError as err:
        print(f"\n[ERROR] {err}", file=sys.stderr)
        sys.exit(1)

    provider_class = provider.__class__.__name__.replace("Provider", "")

    print("=" * 70)
    print(" DISAMBIGUATOR MULTI-PROVIDER AUTOMATED TEST RUNNER")
    print(f" Provider:    {provider_class}")
    print(f" Test Model:  {test_model}")
    print(f" Judge Model: {judge_model}")
    print(f" Total Cases: {len(cases)}")
    print("=" * 70)

    run_id = datetime.now(timezone.utc).isoformat()
    executed_cases: list[dict[str, Any]] = []

    passed_count = 0
    failed_count = 0

    for idx, case in enumerate(cases, 1):
        print(f"[{idx:02d}/20] Case #{case.id:02d} ({case.category[:11]}): {case.prompt[:35]}...", end=" ", flush=True)
        try:
            result_item = run_test_case(
                provider=provider,
                case=case,
                system_prompt=system_prompt,
                test_model=test_model,
                judge_model=judge_model,
            )
            executed_cases.append(result_item)

            if result_item["result"] == "PASS":
                passed_count += 1
                print("[\033[92mPASS\033[0m]")
            else:
                failed_count += 1
                print("[\033[91mFAIL\033[0m]")
                if result_item["judge_reasoning"]:
                    print(f"       Reason: {result_item['judge_reasoning']}")

        except Exception as exc:
            failed_count += 1
            print("[\033[91mERROR\033[0m]")
            print(f"       Execution error: {exc}", file=sys.stderr)
            executed_cases.append({
                "id": case.id,
                "category": case.category,
                "prompt": case.prompt,
                "response": "",
                "assertions_results": {k: "FAIL" for k in case.assertions.keys()},
                "result": "FAIL",
                "judge_reasoning": f"Execution exception: {str(exc)}",
            })

    output_payload = {
        "run_id": run_id,
        "provider": provider_class,
        "models": {
            "test_model": test_model,
            "judge_model": judge_model,
        },
        "summary": {
            "passed": passed_count,
            "failed": failed_count,
            "total": len(cases),
            "pass_rate_pct": round((passed_count / len(cases)) * 100, 1) if cases else 0.0,
        },
        "cases": executed_cases,
    }

    results_file = repo_root / "results.json"
    results_file.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 70)
    print(" RUN SUMMARY")
    print(f" Total:      {len(cases)}")
    print(f" Passed:     {passed_count}")
    print(f" Failed:     {failed_count}")
    print(f" Pass Rate:  {output_payload['summary']['pass_rate_pct']}%")
    print(f" Results:    {results_file.relative_to(repo_root)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
