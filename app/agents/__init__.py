"""
AI Agents package initialization - Fallback System.
"""

# Import fallback agents that handle multiple AI providers
from .qa_agent import medical_qa_agent
from .summarizer_fallback import visit_summarizer
from .base_agent import FallbackAgent

__all__ = [
    "medical_qa_agent",
    "visit_summarizer",
    "FallbackAgent"
]
