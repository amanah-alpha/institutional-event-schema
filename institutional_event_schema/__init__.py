"""Independent public schema validation; no assurance engine dependency."""
from ._json import InputError, load_document
from .validation import Diagnostic, diagnostics as validate

__version__ = "0.1.0"
__all__ = ["Diagnostic", "InputError", "load_document", "validate"]
