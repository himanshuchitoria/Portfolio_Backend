from typing import List
import logging

logger = logging.getLogger(__name__)

class EscalationHandler:
    """
    Handles escalation scenario by creating detailed, context-rich escalation notes.
    Designed to be extensible for notifications or integration with ticketing systems.
    """

    def __init__(self):
        # Future hooks for notification integration, ticket creation, etc.
        pass

    def create_escalation_note(self, user_query: str, conversation_history: List[str]) -> str:
        """
        Generates a detailed escalation note based on the user's query and conversation history.
        This note can be forwarded to human agents or support tickets.

        Parameters:
            user_query (str): The current user query triggering escalation.
            conversation_history (List[str]): The prior conversation entries alternating user and bot messages.

        Returns:
            str: A formatted escalation note string.
        """

        note_lines = [
            "=== Escalation Alert ===",
            "An AI customer support escalation has been triggered.",
            "",
            "User Query:",
            f"{user_query}",
            "",
            "Conversation Context (most recent messages last):"
        ]

        # Format conversation context as user-bot pairs
        for i in range(0, len(conversation_history), 2):
            user_msg = conversation_history[i]
            bot_msg = conversation_history[i + 1] if i + 1 < len(conversation_history) else "<No reply>"
            note_lines.append(f"User: {user_msg}")
            note_lines.append(f"Bot: {bot_msg}")
            note_lines.append("")

        note_lines.append("Recommended Action: Escalate this issue to a human customer support agent.")
        note_lines.append("=======================")

        return "\n".join(note_lines)

    async def notify_support_team(self, escalation_note: str) -> None:
        """
        Placeholder async method to notify support team of escalation.
        Extend with real email, ticket creation, or notification APIs.

        Parameters:
            escalation_note (str): The escalation note text to forward.
        """

        logger.info("Escalation Notification sent to support team:\n%s", escalation_note)
        print("Escalation Notification sent to support team:")
        print(escalation_note)
