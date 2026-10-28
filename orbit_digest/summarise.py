import re

from .rank import PATTERNS

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])")
CUES = re.compile(
    r"\b(we propose|we present|we show|we introduce|we demonstrate|this paper|this article|"
    r"results|achieve|outperform|novel|demonstrate|reduce|improve)\b",
    re.I,
)
JARGON = re.compile(
    r"\b(theorem|lemma|convergence|stochastic|bayesian|manifold|variational|lyapunov|"
    r"gradient|kernel|probabilistic|optimal control|markov|eigen\w*|covariance|nonlinear|"
    r"kalman|asymptotic\w*|polynomial)\b",
    re.I,
)

WHY = {
    ("space", "robotics"): "Relevant to robots that must work far from Earth, where remote control and repair are limited.",
    ("space", "ai"): "Shows how AI can help spacecraft and rovers decide for themselves when Earth is too far away to help.",
    ("robotics", "ai"): "Shows how learning methods are making robots more capable, a core skill area for robotics roles.",
    ("space", "automation"): "Shows how automation keeps space systems running safely with fewer people in the loop.",
    ("space",): "Gives context on the space industry and where autonomy and robotics are needed next.",
    ("robotics",): "Useful background on how robots sense, plan and act in the real world.",
    ("ai",): "Useful background on where AI methods are heading and what they can and cannot do.",
    ("automation",): "Shows practical ways to automate monitoring, diagnosis and decision making.",
}
DEFAULT_WHY = "Broad context for the space, robotics and AI field."


def split_sentences(text: str) -> list:
    return [s.strip() for s in SENTENCE_SPLIT.split(text.strip()) if len(s.strip()) > 20]


def trim(sentence: str, limit: int = 260) -> str:
    if len(sentence) <= limit:
        return sentence
    cut = sentence[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "..."


def keyword_score(sentence: str) -> int:
    lowered = sentence.lower()
    return sum(w for patterns in PATTERNS.values() for p, w in patterns if p.search(lowered))


def extractive_summary(text: str, count: int = 3) -> list:
    sentences = split_sentences(text)
    if len(sentences) <= count:
        return [trim(s) for s in sentences]
    scored = []
    for index, sentence in enumerate(sentences):
        value = keyword_score(sentence) + (4 if CUES.search(sentence) else 0) + (3 if index == 0 else 0)
        scored.append((value, index))
    best = sorted(sorted(scored, reverse=True)[:count], key=lambda pair: pair[1])
    return [trim(sentences[i]) for _, i in best]


def why_it_matters(topics: list) -> str:
    key = tuple(sorted(t for t in topics if t in ("space", "robotics", "ai", "automation")))
    for pair, text in WHY.items():
        if set(pair) <= set(key) and len(pair) == len(key):
            return text
    for pair, text in WHY.items():
        if set(pair) <= set(key):
            return text
    return DEFAULT_WHY


def paper_difficulty(text: str) -> str:
    points = len(JARGON.findall(text)) + (1 if len(text) > 1300 else 0)
    if points >= 3:
        return "Hard"
    if points >= 1:
        return "Intermediate"
    return "Beginner"


def apply_summary(item) -> None:
    item.summary = extractive_summary(item.text) or [trim(item.title)]
    item.why = why_it_matters(item.topics)
    item.difficulty = paper_difficulty(item.text) if item.kind == "paper" else "Easy read"
