import re

from .rank import PATTERNS

SUMMARY_SENTENCES = 2
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
    ("space", "robotics"): (
        "Relevant to robots that must work far from Earth, where remote control and repair are limited.",
        "Ważne dla robotów, które muszą działać daleko od Ziemi, gdzie zdalne sterowanie i naprawy są ograniczone.",
    ),
    ("space", "ai"): (
        "Shows how AI can help spacecraft and rovers decide for themselves when Earth is too far away to help.",
        "Pokazuje, jak AI może pomóc statkom kosmicznym i łazikom decydować samodzielnie, gdy Ziemia jest za daleko, by pomóc.",
    ),
    ("robotics", "ai"): (
        "Shows how learning methods are making robots more capable, a core skill area for robotics roles.",
        "Pokazuje, jak metody uczenia sprawiają, że roboty są coraz zdolniejsze. To kluczowy obszar w pracy w robotyce.",
    ),
    ("space", "automation"): (
        "Shows how automation keeps space systems running safely with fewer people in the loop.",
        "Pokazuje, jak automatyzacja pozwala bezpiecznie utrzymywać systemy kosmiczne przy mniejszym udziale ludzi.",
    ),
    ("space",): (
        "Gives context on the space industry and where autonomy and robotics are needed next.",
        "Daje kontekst o branży kosmicznej i o tym, gdzie potrzebna będzie autonomia i robotyka.",
    ),
    ("robotics",): (
        "Useful background on how robots sense, plan and act in the real world.",
        "Przydatne tło o tym, jak roboty postrzegają, planują i działają w prawdziwym świecie.",
    ),
    ("ai",): (
        "Useful background on where AI methods are heading and what they can and cannot do.",
        "Przydatne tło o kierunku rozwoju metod AI oraz o tym, co potrafią, a czego nie.",
    ),
    ("automation",): (
        "Shows practical ways to automate monitoring, diagnosis and decision making.",
        "Pokazuje praktyczne sposoby automatyzacji monitoringu, diagnozowania i podejmowania decyzji.",
    ),
}
DEFAULT_WHY = (
    "Broad context for the space, robotics and AI field.",
    "Ogólny kontekst dla dziedziny kosmosu, robotyki i AI.",
)
WHY_TO_PL = {en: pl for en, pl in [*WHY.values(), DEFAULT_WHY]}


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


def extractive_summary(text: str, count: int = SUMMARY_SENTENCES) -> list:
    sentences = split_sentences(text)
    if len(sentences) <= count:
        return [trim(s) for s in sentences]
    scored = []
    for index, sentence in enumerate(sentences):
        value = keyword_score(sentence) + (4 if CUES.search(sentence) else 0) + (3 if index == 0 else 0)
        scored.append((value, index))
    best = sorted(sorted(scored, reverse=True)[:count], key=lambda pair: pair[1])
    return [trim(sentences[i]) for _, i in best]


def why_pair(topics: list) -> tuple:
    key = tuple(sorted(t for t in topics if t in ("space", "robotics", "ai", "automation")))
    for pair, texts in WHY.items():
        if set(pair) <= set(key) and len(pair) == len(key):
            return texts
    for pair, texts in WHY.items():
        if set(pair) <= set(key):
            return texts
    return DEFAULT_WHY


def why_it_matters(topics: list) -> str:
    return why_pair(topics)[0]


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
