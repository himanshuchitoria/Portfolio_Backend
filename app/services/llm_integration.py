import asyncio
import logging
from typing import List, Union, Tuple
from google import genai
from app.utils.prompts import (
    NEXT_ACTIONS_PROMPT_TEMPLATE,
    SUMMARY_PROMPT_TEMPLATE,
    is_unsatisfactory,
    build_conversational_prompt,
    build_summary_prompt,
    build_next_actions_prompt,
)

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Google Gemini Generative Language API client customized as Himanshu's personal assistant,
    with retry, error handling, and prompt construction to answer only about Himanshu.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", max_retries: int = 3, retry_delay: float = 2.0):
        logger.info("[LLMClient] Initialized with model: %s", model_name)
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def _retry_api_call(self, func, *args, **kwargs):
        delay = self.retry_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error("LLM API call failed (attempt %d): %s", attempt, e)
                if attempt < self.max_retries:
                    logger.info("Retrying after %s seconds...", delay)
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error("Max retries reached for Gemini API call.")
                    raise

    async def generate_response(self, user_query: str, conversation_history: List[Union[str, dict, Tuple[str, str]]]):
        logger.info("[LLMClient] generate_response called")
        # Build prompt messages - convert conversation_history to List[str] if needed
        # For simplicity, assume conversation_history is List[str] alternating user and assistant
        messages = build_conversational_prompt(user_query, conversation_history)

        prompt = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}"
            for m in messages
        )

        async def call():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text

        try:
            response_text = await self._retry_api_call(call)
            logger.info("LLM raw response text: %s", response_text)

            if is_unsatisfactory(response_text):
                logger.info("Escalation triggered due to unhelpful response.")
                return {
                    "text": "Your query has been escalated to a human agent for assistance.",
                    "escalated": True,
                }
            return {
                "text": response_text,
                "escalated": False,
            }

        except Exception as ex:
            logger.exception("Failed to generate response from Gemini.")
            return {
                "text": "Sorry, I'm having trouble processing your request at the moment.",
                "escalated": False,
            }

    async def summarize_session(self, conversation: str) -> str:
        logger.info("[LLMClient] summarize_session called")
        prompt = build_summary_prompt(conversation)

        async def call():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text or "No summary available."

        try:
            return await self._retry_api_call(call)
        except Exception:
            logger.exception("Failed to get summary from Gemini.")
            return "Unable to generate summary at this time."

    async def get_suggestions(self, response_text: str) -> List[str]:
        """
        Generate 3 suggested next actions based on response_text.
        """
        prompt = build_next_actions_prompt(response_text)

        async def call():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            # Assuming response text contains suggestions separated by newline
            suggested = response.text or ""
            return [s.strip() for s in suggested.split("\n") if s.strip()]

        try:
            return await self._retry_api_call(call)
        except Exception:
            logger.exception("Failed to get next action suggestions from Gemini.")
            return []
