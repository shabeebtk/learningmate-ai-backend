import json
import re
from llm.providers.gemini_provider import generate_gemini
from llm.providers.openai_provider import generate_openai

class LLMClient:

    @staticmethod
    def generate(
        provider: str,
        model: str,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 300,
        top_p: float = 1,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        response_format: str = "json",
    ):

        if provider == "openai":
            content = generate_openai(
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )

        elif provider == "gemini":
            content = generate_gemini(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Clean markdown JSON if model wrapped it
        content = re.sub(r"^```json|```$", "", content.strip(), flags=re.MULTILINE).strip()

        if response_format == "json":
            try:
                return json.loads(content)
            except Exception:
                return {"raw_response": content}

        return content