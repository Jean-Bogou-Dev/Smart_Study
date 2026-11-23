from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@dataclass
class ReviewSession:
    date: str
    score: int

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ReviewSession:
        return cls(
            date=str(data.get("date", datetime.now().isoformat())),
            score=int(data.get("score", 3)),
        )


@dataclass
class Chapter:
    id: str
    title: str
    estimated_minutes: int
    difficulty: int = 3
    mastery_level: int = 2
    repetitions: int = 0
    last_reviewed_at: str | None = None
    history: list[ReviewSession] = field(default_factory=list)

    def elapsed_days(self, now: datetime) -> float:
        last_dt = parse_iso_datetime(self.last_reviewed_at)
        if last_dt is None:
            return 3.0
        delta_seconds = (now - last_dt).total_seconds()
        return max(0.0, delta_seconds / 86400.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "estimated_minutes": int(self.estimated_minutes),
            "difficulty": int(self.difficulty),
            "mastery_level": int(self.mastery_level),
            "repetitions": int(self.repetitions),
            "last_reviewed_at": self.last_reviewed_at,
            "history": [session.to_dict() for session in self.history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Chapter:
        raw_history = data.get("history") or []
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            estimated_minutes=max(5, int(data.get("estimated_minutes", 30))),
            difficulty=min(5, max(1, int(data.get("difficulty", 3)))),
            mastery_level=min(5, max(1, int(data.get("mastery_level", 2)))),
            repetitions=max(0, int(data.get("repetitions", 0))),
            last_reviewed_at=data.get("last_reviewed_at"),
            history=[ReviewSession.from_dict(item) for item in raw_history],
        )


@dataclass
class Course:
    id: str
    name: str
    coefficient: float
    exam_date: str
    chapters: list[Chapter] = field(default_factory=list)

    def days_until_exam(self, now: datetime) -> int:
        try:
            exam_dt = datetime.fromisoformat(self.exam_date)
        except ValueError:
            exam_dt = datetime.strptime(self.exam_date, "%Y-%m-%d")

        diff_days = (exam_dt.date() - now.date()).days
        return max(0, diff_days)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "coefficient": float(self.coefficient),
            "exam_date": self.exam_date,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Course:
        raw_chapters = data.get("chapters") or []
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            coefficient=max(0.5, float(data.get("coefficient", 1.0))),
            exam_date=str(data.get("exam_date", "2026-12-15")),
            chapters=[Chapter.from_dict(ch) for ch in raw_chapters],
        )