"""Claude API wrapper for consistent LLM interactions."""

import os
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ClaudeClient:
    """Wrapper around Anthropic Claude API for job search assistant."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-sonnet-4-20250514)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in .env file or pass as parameter."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ) -> str:
        """
        Generate text completion from Claude.

        Args:
            prompt: User prompt/message
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text response
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        # Extract text from response
        return response.content[0].text

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate JSON response from Claude.

        Args:
            prompt: User prompt requesting JSON output
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate

        Returns:
            JSON string response
        """
        full_system = system_prompt or ""
        full_system += "\n\nYou must respond with valid JSON only. No other text or formatting."

        return self.generate(
            prompt=prompt,
            system_prompt=full_system,
            max_tokens=max_tokens,
            temperature=0.0,  # Lower temperature for structured output
        )

    def generate_with_retries(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        retries: int = 3,
    ) -> str:
        """
        Generate with automatic retries on API errors.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            retries: Number of retry attempts

        Returns:
            Generated response

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(retries):
            try:
                return self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    continue

        raise last_error or RuntimeError("All retries exhausted")
