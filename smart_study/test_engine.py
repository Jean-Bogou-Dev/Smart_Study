from datetime import datetime

from engine import record_review, score_all_chapters, select_daily_chapters
from storage import generate_demo_data, save_data


def main() -> None:
    now = datetime(2026, 11, 23, 14, 0, 0)
    data = generate_demo_data(reference_now=now)
    save_data(data, "../data/study_data.json")

    scored = score_all_chapters(data, now=now)
    print("=== CHAPITRES TRIÉS PAR URGENCE ===")
    for item in scored:
        print(
            f"[{item['score']:6.2f}] {item['course_name']} — {item['chapter_title']} "
            f"({item['estimated_minutes']} min) | {item['reason']}"
        )

    plan = select_daily_chapters(scored, available_minutes=120)
    print("\n=== PLAN RECOMMANDÉ (120 MIN MAX) ===")
    for ch in plan["selected"]:
        print(f"- {ch['chapter_title']} ({ch['estimated_minutes']} min, score {ch['score']})")
    print(
        f"Temps utilisé : {plan['total_minutes']} min | "
        f"Temps restant : {plan['remaining_minutes']} min | "
        f"Score total : {plan['total_score']}"
    )

    if plan["selected"]:
        top_id = plan["selected"][0]["chapter_id"]
        record_review(data, chapter_id=top_id, quality=4, reviewed_at=now)
        rescored = score_all_chapters(data, now=now)
        updated = next(x for x in rescored if x["chapter_id"] == top_id)
        print(
            f"\nAprès révision de '{updated['chapter_title']}' "
            f"-> nouveau score : {updated['score']}"
        )


if __name__ == "__main__":
    main()