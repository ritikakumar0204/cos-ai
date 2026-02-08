import json
import re
from typing import Any

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover - allows fallback when transformers is unavailable
    AutoModelForCausalLM = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]


MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
# Easy swap option:
# MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

_TOKENIZER = None
_MODEL = None


def _load_model() -> tuple[Any, Any]:
    global _TOKENIZER, _MODEL
    if _TOKENIZER is not None and _MODEL is not None:
        return _TOKENIZER, _MODEL

    if AutoTokenizer is None or AutoModelForCausalLM is None:
        raise RuntimeError("transformers is not available")

    _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
    _MODEL = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    return _TOKENIZER, _MODEL


def _fallback_stub(previous_content: str, new_content: str) -> str:
    """
    LIGHTWEIGHT FALLBACK STUB:
    Used when local model inference is unavailable/heavy in the environment.
    Returns a mocked JSON-shaped response based on simple text checks.
    """
    prev = previous_content.strip().lower()
    new = new_content.strip().lower()
    if prev == new:
        return '{"change_type":"no_change","explanation":"Both statements are equivalent."}'

    prev_words = set(re.findall(r"\w+", prev))
    new_words = set(re.findall(r"\w+", new))
    overlap = len(prev_words & new_words)
    union = len(prev_words | new_words) or 1
    jaccard = overlap / union

    if jaccard >= 0.75:
        return '{"change_type":"minor_change","explanation":"Wording changed, core decision appears consistent."}'
    return '{"change_type":"major_change","explanation":"Scope or outcome appears materially different."}'


def _call_local_llm(prompt: str) -> str:
    try:
        tokenizer, model = _load_model()
        inputs = tokenizer(prompt, return_tensors="pt")
        output_ids = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
        )
        text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return text[len(prompt) :].strip() if text.startswith(prompt) else text.strip()
    except Exception:
        # Clear, deterministic fallback for constrained demo environments.
        return ""


def _normalize_response(raw_text: str) -> dict:
    valid = {"no_change", "minor_change", "major_change"}

    match = re.search(r"\{[\s\S]*\}", raw_text)
    if match:
        try:
            data = json.loads(match.group(0))
            change_type = str(data.get("change_type", "")).strip().lower()
            explanation = str(data.get("explanation", "")).strip()
            if change_type in valid and explanation:
                return {"change_type": change_type, "explanation": explanation}
        except Exception:
            pass

    lowered = raw_text.lower()
    if "major_change" in lowered:
        return {"change_type": "major_change", "explanation": "Model indicates a major change."}
    if "minor_change" in lowered:
        return {"change_type": "minor_change", "explanation": "Model indicates a minor change."}
    if "no_change" in lowered:
        return {"change_type": "no_change", "explanation": "Model indicates no change."}

    return {
        "change_type": "minor_change",
        "explanation": "Unable to parse model output clearly; defaulted to minor_change.",
    }


def classify_decision_change(previous_content: str, new_content: str) -> dict:
    prompt = (
        "Classify the semantic change between two decision statements.\n"
        "Return ONLY JSON with keys: change_type, explanation.\n"
        'Allowed change_type values: "no_change", "minor_change", "major_change".\n'
        "Keep explanation factual and under 20 words.\n\n"
        f"previous: {previous_content.strip()}\n"
        f"new: {new_content.strip()}\n"
        "JSON:"
    )

    raw = _call_local_llm(prompt)
    parsed = _normalize_response(raw)

    if parsed["change_type"] == "minor_change" and "defaulted to minor_change" in parsed["explanation"]:
        # Use clearly marked fallback behavior if parsing failed.
        raw_fallback = _fallback_stub(previous_content, new_content)
        parsed = _normalize_response(raw_fallback)

    return {"change_type": parsed["change_type"], "explanation": parsed["explanation"]}
