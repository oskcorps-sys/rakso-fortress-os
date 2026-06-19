import json
import unicodedata
from typing import Any, Set, Dict, List

# Comprehensive mapping of Greek and Cyrillic lookalikes to ASCII equivalents
HOMOGLYPH_MAP = {
    # Cyrillic lowercase
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p', '\u0441': 'c', 
    '\u0445': 'x', '\u0443': 'y', '\u0456': 'i', '\u0455': 's', '\u0458': 'j',
    # Cyrillic uppercase
    '\u0410': 'A', '\u0412': 'B', '\u0421': 'C', '\u0415': 'E', '\u041d': 'H', 
    '\u0406': 'I', '\u0408': 'J', '\u041a': 'K', '\u041c': 'M', '\u041e': 'O', 
    '\u0420': 'P', '\u0422': 'T', '\u0425': 'X', '\u04ae': 'Y', '\u0405': 'S',
    # Greek lowercase
    '\u03b1': 'a', '\u03b5': 'e', '\u03b9': 'i', '\u03ba': 'k', '\u03bf': 'o', 
    '\u03c1': 'r', '\u03c5': 'y', '\u03c7': 'x',
    # Greek uppercase
    '\u0391': 'A', '\u0392': 'B', '\u0395': 'E', '\u0396': 'Z', '\u0397': 'H', 
    '\u0399': 'I', '\u039a': 'K', '\u039c': 'M', '\u039d': 'N', '\u039f': 'O', 
    '\u03a1': 'P', '\u03a4': 'T', '\u03a5': 'Y', '\u03a7': 'X'
}

def normalize_string(text: str) -> str:
    """
    Decomposes Unicode, translates homoglyphs to ASCII, lowercases,
    and normalizes whitespace to a single space.
    """
    # Decompose unicode (NFKD)
    nfkd = unicodedata.normalize('NFKD', text)
    # Translate homoglyphs
    translated = nfkd.translate(str.maketrans(HOMOGLYPH_MAP))
    # Lowercase and normalize whitespace
    return " ".join(translated.lower().split())

def clean_whitespace(text: str) -> str:
    """Normalize whitespace without lowercasing or transliterating."""
    return " ".join(text.split())

def get_normalized_words(text: str) -> Set[str]:
    """Extract alphanumeric words from normalized text."""
    normalized = normalize_string(text)
    clean_text = "".join(char for char in normalized if char.isalnum() or char.isspace())
    return set(clean_text.split())

def serialize_to_clean_primitives(payload: Any) -> Any:
    """
    Serializes a payload (handling Pydantic models, custom classes)
    and loads it back as pure python primitives. This strips all custom subclass
    comparison overrides (BypassStr, BypassDict).
    """
    class PydanticEncoder(json.JSONEncoder):
        def default(self, obj: Any) -> Any:
            if hasattr(obj, "model_dump") and callable(obj.model_dump):
                return obj.model_dump()
            if hasattr(obj, "dict") and callable(obj.dict):
                return obj.dict()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            try:
                return super().default(obj)
            except TypeError:
                return str(obj)

    serialized = json.dumps(payload, cls=PydanticEncoder)
    return json.loads(serialized)

def get_value_at_path(payload: Any, path: str) -> Any:
    """Helper to retrieve value from a nested dict/list using dot-separated path."""
    parts = path.split('.')
    current = payload
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, (list, tuple)):
            try:
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            except ValueError:
                return None
        else:
            return None
    return current

def should_exclude_path(current_path: str, paths_list: List[str]) -> bool:
    """Check if the current path is in the exclusion/target list or is a child of one."""
    if not paths_list:
        return False
    for path in paths_list:
        if current_path == path:
            return True
        if current_path.startswith(path + "."):
            return True
    return False

def validate_no_alteration(
    original_text: str,
    payload: Any,
    active_paths: List[str] = None,
    metadata_paths: List[str] = None
) -> None:
    """
    Ensure the original text is present verbatim and not altered, omitted, or hallucinated.
    Raises ValueError on integrity violations.
    """
    if active_paths is None:
        active_paths = []
    if metadata_paths is None:
        metadata_paths = []

    # Basic sanity check
    if not original_text or not original_text.strip():
        raise ValueError("Original text is empty")

    # Clean the input payload using serialization to resolve custom objects and subclasses
    clean_payload = serialize_to_clean_primitives(payload)

    # Get words for overlap checks
    orig_words = get_normalized_words(original_text)
    orig_len = len(original_text)
    norm_orig = normalize_string(original_text)
    clean_orig = clean_whitespace(original_text)

    found_exact = False

    # 1. Verbatim exact check on active paths (if active_paths are defined)
    if active_paths:
        for path in active_paths:
            val = get_value_at_path(clean_payload, path)
            if not isinstance(val, str):
                raise ValueError(
                    f"Integrity Violation: Active path '{path}' does not contain a string value."
                )
            if normalize_string(val) == norm_orig:
                if clean_whitespace(val) == clean_orig:
                    found_exact = True
                else:
                    raise ValueError(
                        f"Integrity Violation: Character-level mismatch or homoglyph alteration detected in active path '{path}'."
                    )
            else:
                raise ValueError(
                    f"Integrity Violation: Active path '{path}' does not match original text verbatim."
                )

    non_exact_strings: List[str] = []

    def walk(node: Any, current_path: str) -> None:
        nonlocal found_exact

        # Exclude metadata paths from recursive walk
        if should_exclude_path(current_path, metadata_paths):
            return

        # Exclude active paths from recursive walk (they are validated directly)
        if should_exclude_path(current_path, active_paths):
            return

        if isinstance(node, str):
            # Check if this string is a verbatim match
            norm_node = normalize_string(node)
            if norm_node == norm_orig:
                # Verbatim match check (case, punctuation, and character-level)
                if clean_whitespace(node) == clean_orig:
                    found_exact = True
                else:
                    raise ValueError(
                        f"Integrity Violation: Character-level mismatch or homoglyph alteration detected in field value '{node}'."
                    )
            else:
                # Not a verbatim match, store for subsequent checks
                non_exact_strings.append(node)
        elif isinstance(node, dict):
            for k, val in node.items():
                next_path = f"{current_path}.{k}" if current_path else k
                walk(val, next_path)
        elif isinstance(node, (list, tuple, set)):
            for idx, item in enumerate(node):
                next_path = f"{current_path}.{idx}" if current_path else str(idx)
                walk(item, next_path)

    walk(clean_payload, "")

    # Omission Check
    if not found_exact:
        raise ValueError(
            f"Integrity Violation: Original message content was omitted or altered. "
            f"Expected exact match for: '{original_text}'"
        )

    # Helper to check a non-exact string for substring addition or high overlap
    def check_non_exact(s: str, is_concatenated: bool = False) -> None:
        norm_s = normalize_string(s)
        
        # Substring Addition Check
        if norm_orig in norm_s:
            context = "concatenated payload fields" if is_concatenated else f"field value '{s}'"
            raise ValueError(
                f"Integrity Violation: Suspected message alteration (unauthorized substring addition) in {context}."
            )

        # Word-based Overlap Checks
        if orig_words:
            s_words = get_normalized_words(s)
            intersection = orig_words.intersection(s_words)
            overlap_ratio = len(intersection) / len(orig_words)
            
            # Standard overlap threshold
            if overlap_ratio > 0.5:
                context = "concatenated payload fields" if is_concatenated else f"field value '{s}'"
                raise ValueError(
                    f"Integrity Violation: Suspected message alteration in {context}. "
                    f"Overlaps {overlap_ratio:.1%} with original text but does not contain it verbatim."
                )
            
            # Stricter overlap threshold for long strings (to catch low-overlap bypasses)
            if orig_len >= 10 and len(s) > 0.5 * orig_len and overlap_ratio > 0.2:
                context = "concatenated payload fields" if is_concatenated else f"field value '{s}'"
                raise ValueError(
                    f"Integrity Violation: Suspected message alteration in long {context}. "
                    f"Overlaps {overlap_ratio:.1%} with original text but is not verbatim."
                )
        else:
            # Punctuation-only copy check (character-level substring)
            if clean_orig in clean_whitespace(s):
                context = "concatenated payload fields" if is_concatenated else f"field value '{s}'"
                raise ValueError(
                    f"Integrity Violation: Suspected message alteration in punctuation-only copy in {context}."
                )

    # Check each non-exact string individually
    for s in non_exact_strings:
        check_non_exact(s, is_concatenated=False)

    # Check concatenated non-exact strings (Split Payload Bypass Check)
    if non_exact_strings:
        concatenated = " ".join(non_exact_strings)
        check_non_exact(concatenated, is_concatenated=True)
