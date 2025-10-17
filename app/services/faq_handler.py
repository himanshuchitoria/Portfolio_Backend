import json
import asyncio
from typing import Optional
from rapidfuzz import process, fuzz
import logging

logger = logging.getLogger(__name__)

class FAQHandler:
    """
    Handles FAQ dataset queries for exact and fuzzy matching.
    Returns specific company info from faqs.json or a fallback prompt
    that triggers Gemini for side/help responses.
    """

    def __init__(self, faq_file_path: str = None):
        # Adjust default path to your data directory as needed
        self.faq_file_path = faq_file_path or "app/data/faqs.json"
        self.faq_data = {}
        self.question_list = []
        self.load_lock = asyncio.Lock()
        self.initialized = False

    async def initialize(self) -> None:
        """
        Asynchronously loads the FAQ data from JSON file once and caches it
        for repeated use to avoid repeated IO in a running server instance.
        """
        async with self.load_lock:
            if not self.initialized:
                try:
                    with open(self.faq_file_path, "r", encoding="utf-8") as f:
                        self.faq_data = json.load(f)
                    self.question_list = list(self.faq_data.keys())
                    self.initialized = True
                    logger.info("FAQ dataset successfully loaded.")
                except Exception as e:
                    logger.error(f"Failed to load FAQ file {self.faq_file_path}: {e}")
                    # Keep fallback prompt available even if FAQ load fails
                    self.faq_data = {}
                    self.question_list = []

    def get_faq_answer(self, query: str) -> Optional[str]:
        """
        Returns the most relevant FAQ answer from company data.
        If no strong match is found, returns a fallback prompt guiding Gemini to assist.

        Parameters:
            query (str): User input query

        Returns:
            Optional[str]: FAQ response or fallback prompt
        """

        if not self.initialized:
            # Synchronously load on first use if async initialization hasn't occurred yet (e.g. during dev or startup)
            try:
                with open(self.faq_file_path, "r", encoding="utf-8") as f:
                    self.faq_data = json.load(f)
                self.question_list = list(self.faq_data.keys())
                self.initialized = True
                logger.info("FAQ dataset synchronously loaded on first use.")
            except Exception as e:
                logger.error(f"Failed to synchronously load FAQ file {self.faq_file_path}: {e}")
                self.faq_data = {}
                self.question_list = []

        query_trimmed = query.strip()

        # Exact case-insensitive match
        for key in self.faq_data.keys():
            if key.lower() == query_trimmed.lower():
                return self.faq_data[key]

        # Fuzzy match with the help of rapidfuzz 
        if self.question_list:
            best_match, score, _ = process.extractOne(
                query_trimmed, self.question_list, scorer=fuzz.token_set_ratio
            )

            if score >= 75:
                return self.faq_data.get(best_match)

        #if want to give any fallback prompt
        fallback_prompt = (
            "I'm here to assist specifically with questions related to our company and services. "
            "For other topics, I can try to help, but my expertise is limited to company-related info. "
            "Could you please clarify or ask about our company or products?"
        )
        return None
