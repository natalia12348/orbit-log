import re
from datetime import datetime, timedelta, timezone

TOPICS = {
    "space": [
        ("spacecraft", 3), ("satellite", 3), ("rover", 3), ("orbit", 2), ("lunar", 2),
        ("moon", 1), ("mars", 2), ("planetary", 2), ("rocket", 2), ("launch", 1),
        ("space", 2), ("onboard", 1), ("on-board", 1), ("astronaut", 2), ("cubesat", 3),
    ],
    "robotics": [
        ("robot", 3), ("manipulat", 2), ("autonomous", 2), ("navigation", 2), ("slam", 2),
        ("locomotion", 2), ("drone", 1), ("gripper", 2), ("swarm", 2), ("teleoperation", 2),
    ],
    "ai": [
        ("neural", 1), ("machine learning", 2), ("deep learning", 2), ("reinforcement", 2),
        ("vision", 1), ("llm", 2), ("language model", 2), ("agent", 1),
        ("foundation model", 2), ("transformer", 1), ("artificial intelligence", 2),
    ],
    "automation": [
        ("automation", 2), ("automated", 1), ("pipeline", 1), ("workflow", 1),
        ("scheduling", 1), ("fault", 2), ("anomaly", 2), ("diagnos", 2),
    ],
}
PATTERNS = {
    topic: [(re.compile(rf"(?<![a-z]){re.escape(word)}"), weight) for word, weight in words]
    for topic, words in TOPICS.items()
}
TOPIC_CAP = 6
WINDOWS = {"paper": timedelta(hours=96), "news": timedelta(hours=48)}


def score_item(item) -> None:
    title = item.title.lower()
    body = item.text.lower()
    total = 0.0
    hits = []
    for topic, patterns in PATTERNS.items():
        points = 0
        for pattern, weight in patterns:
            if pattern.search(title):
                points += weight * 2
            elif pattern.search(body):
                points += weight
        if points:
            hits.append(topic)
        total += min(points, TOPIC_CAP)
    if len(hits) >= 2:
        total += 3
    item.score = total
    item.topics = hits


def select(items, seen, now=None, papers: int = 5, news: int = 8, min_score: float = 4.0) -> tuple:
    now = now or datetime.now(timezone.utc)
    picked = {"paper": [], "news": []}
    unique = {}
    for item in items:
        if item.id in seen or item.id in unique:
            continue
        if now - item.published > WINDOWS[item.kind]:
            continue
        score_item(item)
        if item.score >= min_score:
            unique[item.id] = item
    for item in unique.values():
        picked[item.kind].append(item)
    for kind in picked:
        picked[kind].sort(key=lambda i: (i.score, i.published), reverse=True)
    return picked["paper"][:papers], picked["news"][:news]
