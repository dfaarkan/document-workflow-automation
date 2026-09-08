"""Document workflow automation package."""

from .core import RulesError, classify_text, extract_text, load_rules

__all__ = ["RulesError", "classify_text", "extract_text", "load_rules"]
