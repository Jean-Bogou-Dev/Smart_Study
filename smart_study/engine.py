from __future__ import annotations

import math
from datetime import datetime

from models import Chapter, Course, ReviewSession


def compute_stability(chapter: Chapter) -> float:
    """Calcule la stabilité mémorielle S (en jours) d'un chapitre."""
    base_stability = 2.0
    rep_factor = 1.0 + 0.60 * chapter.repetitions
    mastery_factor = max(0.5, 1.0 + 0.15 * (chapter.mastery_level - 3))
    difficulty_factor = max(0.5, 1.0 - 0.15 * (chapter.difficulty - 3))

    stability = base_stability * rep_factor * mastery_factor * difficulty_factor
    return max(0.5, stability)


def compute_retention(chapter: Chapter, now: datetime) -> float:
    """Calcule la rétention estimée R(t) = exp(-t / S) entre 0.0 et 1.0."""
    t_days = chapter.elapsed_days(now)
    stability = compute_stability(chapter)
    retention = math.exp(-t_days / stability)
    return min(1.0, max(0.0, retention))

def compute_urgency_score(
    chapter: Chapter,
    course: Course,
    now: datetime,
    threshold: float = 0.70,
) -> dict:
    """Calcule l'indice d'urgence d'un chapitre et retourne un dictionnaire détaillé."""
    retention = compute_retention(chapter, now)
    days_left = course.days_until_exam(now)

    deficit = max(0.0, threshold - retention)
    forget_risk = 0.6 * deficit + 0.4 * (1.0 - retention)
    exam_urgency = 1.0 + (14.0 / (days_left + 1.0))
    academic_weight = (course.coefficient / 2.0) * (0.75 + 0.10 * chapter.difficulty)

    score = round(forget_risk * exam_urgency * academic_weight * 100.0, 2)

    retention_pct = round(retention * 100, 1)
    threshold_pct = round(threshold * 100)
    reasons: list[str] = []

    if retention < threshold:
        reasons.append(f"rétention à {retention_pct}% (< {threshold_pct}%)")
    else:
        reasons.append(f"rétention à {retention_pct}%")

    if days_left == 0:
        reasons.append("examen aujourd'hui")
    else:
        reasons.append(f"examen dans {days_left} j")

    reasons.append(f"coeff {course.coefficient:g}, diff {chapter.difficulty}/5")

    return {
        "course_id": course.id,
        "course_name": course.name,
        "chapter_id": chapter.id,
        "chapter_title": chapter.title,
        "estimated_minutes": chapter.estimated_minutes,
        "difficulty": chapter.difficulty,
        "mastery_level": chapter.mastery_level,
        "repetitions": chapter.repetitions,
        "retention": round(retention, 4),
        "days_left": days_left,
        "score": score,
        "reason": " • ".join(reasons),
    }


def score_all_chapters(
    data: dict,
    now: datetime | None = None,
) -> list[dict]:
    """Évalue tous les chapitres de toutes les matières et les trie par score décroissant."""
    current_time = now or datetime.now()
    threshold = float(data.get("retention_threshold", 0.70))
    courses = [Course.from_dict(c) for c in data.get("courses", [])]

    scored: list[dict] = []
    for course in courses:
        for chapter in course.chapters:
            scored.append(compute_urgency_score(chapter, course, current_time, threshold))

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored

def select_daily_chapters(
    scored_items: list[dict],
    available_minutes: int,
    step_minutes: int = 5,
) -> dict:
    """Sélectionne les chapitres maximisant le score total dans la limite de temps disponible."""
    if available_minutes <= 0 or not scored_items:
        return {
            "selected": [],
            "total_minutes": 0,
            "remaining_minutes": max(0, available_minutes),
            "total_score": 0.0,
        }

    capacity = available_minutes // step_minutes
    if capacity == 0:
        return {
            "selected": [],
            "total_minutes": 0,
            "remaining_minutes": available_minutes,
            "total_score": 0.0,
        }

    items: list[tuple[int, float, dict]] = []
    for item in scored_items:
        minutes = max(step_minutes, int(item["estimated_minutes"]))
        cost = max(1, round(minutes / step_minutes))
        value = float(item["score"])
        items.append((cost, value, item))

    n = len(items)
    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    keep = [[False] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        cost, value, _ = items[i - 1]
        for w in range(capacity + 1):
            best = dp[i - 1][w]
            if cost <= w:
                candidate = dp[i - 1][w - cost] + value
                if candidate > best + 1e-9:
                    best = candidate
                    keep[i][w] = True
            dp[i][w] = best

    selected: list[dict] = []
    w = capacity
    for i in range(n, 0, -1):
        if keep[i][w]:
            cost, _, original_item = items[i - 1]
            selected.append(original_item)
            w -= cost

    selected.reverse()
    total_minutes = sum(int(ch["estimated_minutes"]) for ch in selected)
    total_score = round(sum(float(ch["score"]) for ch in selected), 2)

    return {
        "selected": selected,
        "total_minutes": total_minutes,
        "remaining_minutes": max(0, available_minutes - total_minutes),
        "total_score": total_score,
    }

def record_review(
    data: dict,
    chapter_id: str,
    quality: int,
    reviewed_at: datetime | None = None,
) -> dict:
    """Enregistre une session de révision (quality de 1 à 5) et met à jour le chapitre."""
    now = reviewed_at or datetime.now()
    clamped_quality = min(5, max(1, int(quality)))
    iso_now = now.isoformat(timespec="seconds")

    for course_dict in data.get("courses", []):
        for ch_dict in course_dict.get("chapters", []):
            if ch_dict.get("id") == chapter_id:
                chapter = Chapter.from_dict(ch_dict)
                chapter.repetitions += 1
                chapter.last_reviewed_at = iso_now

                if clamped_quality >= 4:
                    chapter.mastery_level = min(5, chapter.mastery_level + 1)
                elif clamped_quality <= 2:
                    chapter.mastery_level = max(1, chapter.mastery_level - 1)

                chapter.history.append(ReviewSession(date=iso_now, score=clamped_quality))
                ch_dict.clear()
                ch_dict.update(chapter.to_dict())
                return data

    raise ValueError(f"Chapitre introuvable : {chapter_id}")

def project_retention_curve(
    chapter: Chapter,
    now: datetime,
    days_ahead: int = 14,
) -> list[dict]:
    """Projette la rétention estimée d'un chapitre sur les prochains jours."""
    horizon = max(1, int(days_ahead))
    stability = compute_stability(chapter)
    current_elapsed = chapter.elapsed_days(now)

    points: list[dict] = []
    for day_offset in range(horizon + 1):
        future_t = current_elapsed + day_offset
        retention = min(1.0, max(0.0, math.exp(-future_t / stability)))
        points.append({
            "day_offset": day_offset,
            "retention": round(retention, 4),
            "retention_pct": round(retention * 100, 1),
        })

    return points