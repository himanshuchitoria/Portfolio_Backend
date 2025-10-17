import re
from typing import List, Dict

# Escalation trigger phrases to detect fallback/unhelpful LLM responses
ESCALATION_TRIGGER_PHRASES = [
    "i'm unable to answer",
    "i don't know",
    "please contact support",
    "escalate",
    "sorry, i cannot assist with that",
    "not sure",
    "could you please clarify",
    "unable to help",
    "can't help",
    "try to help",
    "clarify or rephrase your question:",
    "do not have that information",
    "i'm here to assist specifically with questions about himanshu",
    "for other topics, i may have limited knowledge",
    "please clarify or ask about himanshu",
]

ESCALATION_TRIGGER_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in ESCALATION_TRIGGER_PHRASES]

# Personal knowledge base injected into prompts
PERSONAL_PROFILE_CONTENT = """
Himanshu Chitoria is a Computer Science student at VIT Bhopal and pursuing a part-time Bachelor of Science in Data Science at IIT Madras. 
Specializes in full-stack web development, healthcare technology, and cybersecurity.
Skills: Python, JavaScript (React.js, Next.js), Node.js, REST APIs, MongoDB, AWS, TensorFlow, OpenCV.
Internships at IDEMIA, Hitachi, ValU5Healthcare involving facial recognition, AWS automation, secure healthcare APIs.
Notable projects: DevSync (real-time collaboration), FinSave (AI finance tracker), TrendHire (AI resume optimizer).
Certifications in Data Fundamentals (IBM), Cloud Computing (NPTEL), Python Essentials (Vityarthi), and Networking (Google).
Fluent in Hindi, English, and Japanese.
"""

# Prompt templates
SUMMARY_PROMPT_TEMPLATE = (
    "You are the personal assistant of Himanshu Chitoria. Use the following knowledge base about Himanshu to answer all questions accurately, "
    "reflecting his skills, education, and projects:\n"
    "{knowledge_base}\n\n"
    "Please provide a concise and clear summary of the following conversation:\n"
    "{conversation}"
)

NEXT_ACTIONS_PROMPT_TEMPLATE = (
    "You are assisting users interested in Himanshu Chitoria's skills and projects. "
    "Based on this response, suggest 3 actionable next steps for users to engage with Himanshu professionally:\n"
    "{response}"
)


def is_unsatisfactory(response_text: str) -> bool:
    """
    Detect if the LLM response is unsatisfactory and should be escalated.
    """
    for pattern in ESCALATION_TRIGGER_PATTERNS:
        if pattern.search(response_text):
            return True

    lowered = response_text.lower()
    fallback_indicators = ["sorry", "unable to help", "expertise is limited", "please clarify"]
    if any(indicator in lowered for indicator in fallback_indicators):
        print(f"Potential fallback response detected for escalation: {response_text}")

    return False


def build_conversational_prompt(user_query: str, conversation_history: List[str]) -> List[Dict]:
    """
    Construct the messages list to send to the LLM with personal profile context,
    restricting answers to information about Himanshu only.
    """
    system_content = (
        "You are the personal assistant of Himanshu Chitoria, a Computer Science student at VIT Bhopal and part-time Data Science student at IIT Madras. "
        "Only answer questions related to Himanshu's skills, projects, internships, certifications, education, and interests based on the knowledge below. "
        "Do NOT discuss yourself or any AI model information. Politely decline unrelated questions.\n"
        f"Knowledge base:\n{PERSONAL_PROFILE_CONTENT}"
    )
    messages = [{"role": "system", "content": system_content}]

    # Add conversation history (user and assistant in pairs)
    for i in range(0, len(conversation_history), 2):
        user_msg = conversation_history[i]
        if i + 1 < len(conversation_history):
            assistant_msg = conversation_history[i + 1]
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        else:
            messages.append({"role": "user", "content": user_msg})

    # Append latest user query
    messages.append({"role": "user", "content": user_query})

    return messages


def build_summary_prompt(conversation: str) -> str:
    return SUMMARY_PROMPT_TEMPLATE.format(knowledge_base=PERSONAL_PROFILE_CONTENT, conversation=conversation)


def build_next_actions_prompt(response: str) -> str:
    return NEXT_ACTIONS_PROMPT_TEMPLATE.format(response=response)
