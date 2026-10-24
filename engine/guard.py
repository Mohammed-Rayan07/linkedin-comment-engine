"""Truth gate + anti-slop checks. Every draft passes through here before it reaches you.

The truth gate is the most important part of the engine: a made-up number or client result under your
name does far more damage than a missed comment. A draft that fails is regenerated once with the
violations as feedback, and dropped if it still fails.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

BANNED_OPENERS = [
    "great post", "love this", "so true", "this!", "well said", "spot on", "couldn't agree more",
    "absolutely", "100%", "thanks for sharing", "interesting perspective", "as someone who",
    "great insights", "great point", "totally agree", "fantastic",
]
BANNED_PHRASES = [
    "game-changer", "game changer", "revolutionary", "unlock", "unleash", "transformative",
    "in today's world", "in today’s world", "fast-paced", "here's the thing", "here’s the thing",
    "let that sink in", "delve", "landscape", "tapestry", "navigate the", "elevate", "empower",
    "synergy", "seamless", "robust", "cutting-edge", "cutting edge", "paradigm", "at the end of the day",
    "needle-moving", "deep dive", "thoughts?", "what do you think?", "agree?",
]
PITCH_PHRASES = [
    "dm me", "i help businesses", "i help companies", "check my profile", "we offer", "book a call",
    "happy to help", "feel free to reach out", "link in bio", "link in comments", "my agency can", "let's connect",
    "hit me up",
]
NEVER_CLAIM_PATTERNS = [
    r"\bmy (dad|father|family)\b",
    r"\byears of experience\b",
    r"\bfluent in arabic\b",
]
CLIENT_CLAIM_PATTERNS = [
    r"\b(our|my) clients?\b",
    r"\bfor (a|one|our|my) (client|customer)s?\b",
    r"\b(we|i) (helped|cut|increased|grew|boosted|saved|reduced|doubled|tripled|generated)\b",
    r"\bclients? (saw|got|achieved|went from)\b",
    r"\bdeployed (for|at|in) \d+",
]
NOT_X_ITS_Y = re.compile(r"\bit[’']?s not (just |only )?[^.!?]{1,50}[,.;:]\s*it[’']?s\b", re.I)
# "The hard part isn't A. It is B." / "...isn't A, but B": the most common shape in the drafts readers flagged as AI
ISNT_X_BUT_Y = re.compile(
    r"\b(?:is|are)(?:n[’']t| not) (?:just |only |really |about )?[^.!?\n]{1,80}?"
    r"(?:,\s*but (?:rather )?(?:the|that|how|whether|\w+ing)\b|[,.;:]\s*(?:it|they)(?:[’']s| is| are)\b)", re.I)
# Consultant templates that recur across drafts; one of them is enough to sound machine-written.
AI_TEMPLATES = [
    re.compile(r"\bthe (?:step|part|thing) most [^.!?]{0,50}\b(?:skip|miss|overlook|ignore)", re.I),
    re.compile(r"\busually comes down to\b", re.I),
    re.compile(r"\bthe hidden cost\b", re.I),
]
EM_DASH = re.compile(r"—|\s–\s")
NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?%?")
TIME_OR_247 = re.compile(r"\b24/7\b|\b\d{1,2}(?::\d{2})?\s?(?:am|pm)\b", re.I)
# Small numbers are normally fine ("3 things", "a 2-step check"), but not when they describe an outcome.
UNIT_NUMBER = re.compile(
    r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s?(?:hours?|hrs?|days?|weeks?|months?|minutes?|mins?|seconds?|"
    r"bookings?|calls?|leads?|consults?|patients?|appointments?|clients?|customers?|deals?|sales|"
    r"viewings?|reviews?|orders?)\b", re.I)
MULTIPLIER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?x\b", re.I)
OUTCOME_WORDS = re.compile(r"\b(doubled|tripled|quadrupled|halved|in half)\b", re.I)


_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
          "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_WORD_NUM = re.compile(
    r"\b(?:(" + "|".join(_TENS) + r")(?:[- ](" + "|".join(_UNITS[1:10]) + r"))?|(" + "|".join(_UNITS) + r"))"
    r"(?:\s+(hundred|thousand))?\b(\s*percent)?", re.I)


def digitize(text: str) -> str:
    """'thirty percent' -> '30%', 'ten seconds' -> '10 seconds', so spelled-out numbers can't dodge the gate."""
    def repl(m: re.Match) -> str:
        tens, unit, single, scale, pct = m.groups()
        n = (_TENS[tens.lower()] + (_UNITS.index(unit.lower()) if unit else 0)) if tens else _UNITS.index(single.lower())
        if scale:
            n *= 100 if scale.lower() == "hundred" else 1000
        return f"{n}%" if pct else str(n)
    return _WORD_NUM.sub(repl, text)


def _norm(tok: str) -> str:
    """'3,000' -> '3000', '$1.30' -> '1.3'. A trailing % is kept: 40% must match a percentage, not '40 items'."""
    pct = tok.endswith("%")
    tok = tok.rstrip("%").lstrip("$").replace(",", "")
    if "." in tok:
        tok = tok.rstrip("0").rstrip(".")
    return tok + ("%" if pct else "")


def numbers_in(text: str) -> set[str]:
    return {_norm(m.group()) for m in NUMBER.finditer(text)}


def allowed_numbers(profile: dict[str, Any], post_text: str) -> set[str]:
    """Numbers the writer may use: anything in the proof bank, plus numbers quoted from the post itself."""
    chunks: list[str] = [post_text]
    for proof in profile.get("proofs", []):
        chunks.append(proof.get("summary", ""))
        chunks.extend(proof.get("facts", []))
    chunks.extend(profile.get("opinions", []))
    allowed: set[str] = set()
    for c in chunks:
        allowed |= numbers_in(TIME_OR_247.sub(" ", c))  # "7 PM" in the bank doesn't license "7 hours"
    return allowed


def _is_trivial(tok: str) -> bool:
    if tok.endswith("%"):
        return False
    try:
        v = float(tok)
    except ValueError:
        return False
    return v <= 10 and "." not in tok


def _contains_any(text: str, phrases: Iterable[str]) -> list[str]:
    return [p for p in phrases if p in text]


def check(comment: str, profile: dict[str, Any], post_text: str, min_chars: int, max_chars: int) -> list[str]:
    """Return a list of human-readable violations (empty list = clean)."""
    v: list[str] = []
    text = comment.strip()
    low = text.lower()

    if len(text) < min_chars:
        v.append(f"too short ({len(text)} chars, min {min_chars})")
    if len(text) > max_chars:
        v.append(f"too long ({len(text)} chars, max {max_chars})")
    for opener in BANNED_OPENERS:
        if low.startswith(opener):
            v.append(f"generic opener: '{opener}'")
    for p in _contains_any(low, BANNED_PHRASES):
        v.append(f"AI-sounding phrase: '{p}'")
    for p in _contains_any(low, PITCH_PHRASES):
        v.append(f"pitchy phrase: '{p}'")
    if re.search(r"\bleverag(e|es|ing)\b", low):
        v.append("AI-sounding word: 'leverage'")
    if NOT_X_ITS_Y.search(text):
        v.append("uses the 'it's not X, it's Y' construction")
    elif ISNT_X_BUT_Y.search(text):
        v.append("uses the 'isn't X, but Y' construction")
    for pat in AI_TEMPLATES:
        if m := pat.search(text):
            v.append(f"templated AI phrasing: '{m.group()}'")
    if EM_DASH.search(text):
        v.append("contains an em dash")
    if re.search(r"(^|\s)#\w", text):
        v.append("contains a hashtag")
    if re.search(r"https?://|www\.", low):
        v.append("contains a link")
    for pat in NEVER_CLAIM_PATTERNS:
        if re.search(pat, low):
            v.append(f"forbidden claim matches /{pat}/")
    for pat in CLIENT_CLAIM_PATTERNS:
        if re.search(pat, low):
            v.append("claims a client result; none are verified in expert_profile.yaml")
            break

    text = digitize(text)  # spelled-out numbers are checked like digits
    allowed = allowed_numbers(profile, digitize(post_text))
    bank_text = (post_text + " " + " ".join(
        " ".join([pr.get("summary", "")] + pr.get("facts", [])) for pr in profile.get("proofs", []))).lower()
    scrubbed = TIME_OR_247.sub(" ", text)
    for m in MULTIPLIER.finditer(scrubbed):
        if m.group().lower() not in bank_text:
            v.append(f"multiplier '{m.group()}' is not in your proof bank or the post")
    for m in OUTCOME_WORDS.finditer(scrubbed):
        if m.group().lower() not in bank_text:
            v.append(f"outcome claim '{m.group()}' is not backed by your proof bank or the post")
    unit_numbers = {_norm(m.group(1)) for m in UNIT_NUMBER.finditer(scrubbed)}
    for tok in numbers_in(scrubbed):
        if (tok in unit_numbers or not _is_trivial(tok)) and tok not in allowed:
            v.append(f"number '{tok}' is not in your proof bank or the post")
    return v
