from collections.abc import AsyncIterable
import re


TAIL_CHARS = 64


def _normalize_spaced_acronyms(text: str) -> str:
    replacements = {
        r"\bA\s*[- ]\s*I\b": "AI",
        r"\bC\s*[- ]\s*R\s*[- ]\s*M\s*[- ]\s*S\b": "CRMs",
        r"\bC\s*[- ]\s*R\s*M\b": "CRM",
        r"\bE\s*[- ]\s*R\s*[- ]\s*P\s*[- ]\s*S\b": "ERPs",
        r"\bE\s*[- ]\s*R\s*P\b": "ERP",
        r"\bU\s*[- ]\s*R\s*[- ]\s*L\s*[- ]\s*S\b": "URLs",
        r"\bU\s*[- ]\s*R\s*L\b": "URL",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def _expand_spoken_business_terms(text: str) -> str:
    text = re.sub(
        r"\bS\s*[- ]?\s*M\s*[- ]?\s*Bs\b",
        "small and medium-sized businesses",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bS\s*[- ]?\s*M\s*[- ]?\s*B\b",
        "small and medium-sized business",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _collapse_spelled_words(text: str) -> str:
    def replace_letter_run(match: re.Match[str]) -> str:
        letters = re.findall(r"[A-Za-z]", match.group(0))
        if len(letters) < 4:
            return match.group(0)

        return "".join(letters).capitalize()

    return re.sub(r"\b(?:[A-Za-z][ -]){3,}[A-Za-z]\b", replace_letter_run, text)


def normalize_spoken_text(text: str) -> str:
    text = text.replace("\u2026", "...")
    text = _normalize_spaced_acronyms(text)
    text = _expand_spoken_business_terms(text)
    text = _collapse_spelled_words(text)
    text = re.sub(r"\binbound\s*/\s*outbound\b", "inbound and outbound", text, flags=re.IGNORECASE)
    text = re.sub(r"\band\s*/\s*or\b", "or", text, flags=re.IGNORECASE)
    text = re.sub(r"\.{2,}", ", ", text)
    text = re.sub(r"!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r",{2,}", ",", text)
    text = re.sub(r"\s+([,!?;:])", r"\1", text)
    text = re.sub(r"([,!?;:])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


async def normalize_spoken_text_stream(text: AsyncIterable[str]) -> AsyncIterable[str]:
    buffer = ""

    async for chunk in text:
        buffer += chunk
        if len(buffer) <= TAIL_CHARS:
            continue

        normalized = normalize_spoken_text(buffer)
        flush_to = max(0, len(normalized) - TAIL_CHARS)
        if flush_to:
            yield normalized[:flush_to]
            buffer = normalized[flush_to:]
        else:
            buffer = normalized

    if buffer:
        yield normalize_spoken_text(buffer)
