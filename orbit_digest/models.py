from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Item:
    id: str
    kind: str
    title: str
    link: str
    text: str
    source: str
    published: datetime
    authors: list = field(default_factory=list)
    score: float = 0.0
    topics: list = field(default_factory=list)
    summary: list = field(default_factory=list)
    why: str = ""
    difficulty: str = ""
    pl: dict = field(default_factory=dict)
