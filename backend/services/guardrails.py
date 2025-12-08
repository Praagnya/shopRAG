"""
Input Guardrails for RAG Pipeline
Validates and secures user inputs before processing.
"""

import re
from typing import Tuple
from datetime import datetime, timedelta


class InputGuardrails:
    """Validates user queries for security and quality."""

    MAX_QUERY_LENGTH = 500
    MIN_QUERY_LENGTH = 3

    # Patterns that might indicate prompt injection attacks
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+(instructions|prompts?|commands?)",
        r"you\s+are\s+now\s+a?",
        r"system\s*:",
        r"forget\s+(everything|all|previous)",
        r"disregard\s+(the\s+)?(above|previous)",
        r"new\s+instructions?",
        r"pretend\s+(you|to)\s+are",
    ]

    def __init__(self):
        """Initialize guardrails."""
        self.rate_limit_store = {}
        print("✓ Input Guardrails initialized")

    def validate_query(self, query: str, user_id: str = "default") -> Tuple[bool, str]:
        """
        Validate user query against security checks.

        Args:
            query: User's question
            user_id: User identifier for rate limiting

        Returns:
            (is_valid, error_message) - error_message is empty if valid
        """
        # Check if empty
        if not query or not query.strip():
            return False, "Query cannot be empty"

        query_clean = query.strip()

        # Check length
        if len(query_clean) < self.MIN_QUERY_LENGTH:
            return False, f"Query too short (minimum {self.MIN_QUERY_LENGTH} characters)"

        if len(query_clean) > self.MAX_QUERY_LENGTH:
            return False, f"Query too long (maximum {self.MAX_QUERY_LENGTH} characters)"

        # Check for prompt injection
        is_injection, injection_msg = self._detect_prompt_injection(query_clean)
        if is_injection:
            return False, injection_msg

        # Check rate limiting
        is_rate_limited, rate_msg = self._check_rate_limit(user_id)
        if is_rate_limited:
            return False, rate_msg

        return True, ""

    def _detect_prompt_injection(self, query: str) -> Tuple[bool, str]:
        """Check for potential prompt injection attacks."""
        query_lower = query.lower()

        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                print(f"⚠️  Blocked prompt injection attempt: {pattern}")
                return True, "Invalid query detected"

        return False, ""

    def _check_rate_limit(self, user_id: str, max_requests: int = 20,
                          window_minutes: int = 1) -> Tuple[bool, str]:
        """
        Simple rate limiting using in-memory storage.
        Allows max_requests per window_minutes.
        """
        now = datetime.now()

        if user_id not in self.rate_limit_store:
            self.rate_limit_store[user_id] = []

        # Get user's recent requests
        user_requests = self.rate_limit_store[user_id]

        # Remove old requests outside time window
        cutoff_time = now - timedelta(minutes=window_minutes)
        user_requests = [ts for ts in user_requests if ts > cutoff_time]

        # Check if limit exceeded
        if len(user_requests) >= max_requests:
            print(f"⚠️  Rate limit exceeded for user: {user_id}")
            return True, f"Too many requests. Maximum {max_requests} per {window_minutes} minute(s)"

        # Add current request
        user_requests.append(now)
        self.rate_limit_store[user_id] = user_requests

        return False, ""


# Singleton instance
_guardrails_instance = None


def get_guardrails() -> InputGuardrails:
    """Get or create the guardrails instance."""
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = InputGuardrails()
    return _guardrails_instance
