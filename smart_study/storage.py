from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


DEFAULT_DATA_PATH = Path("../data/study_data.json")

def generate_demo_data(reference_now: datetime | None = None) -> dict:
    """Génère un jeu de données réaliste de cycle ingénieur pour la démo."""
    now = reference_now or datetime.now()

    def iso_days_ago(days: float) -> str:
        return (now - timedelta(days=days)).isoformat(timespec="seconds")

    def date_in_days(days: int) -> str:
        return (now + timedelta(days=days)).strftime("%Y-%m-%d")

    return {
        "daily_available_minutes": 120,
        "retention_threshold": 0.70,
        "courses": [
            {
                "id": "stat-101",
                "name": "Statistiques & Analyse de Données",
                "coefficient": 3.0,
                "exam_date": date_in_days(6),
                "chapters": [
                    {
                        "id": "st-ch1",
                        "title": "Paramètres de position, dispersion & quartiles",
                        "estimated_minutes": 35,
                        "difficulty": 2,
                        "mastery_level": 3,
                        "repetitions": 2,
                        "last_reviewed_at": iso_days_ago(5.5),
                        "history": [
                            {"date": iso_days_ago(11.0), "score": 3},
                            {"date": iso_days_ago(5.5), "score": 3},
                        ],
                    },
                    {
                        "id": "st-ch2",
                        "title": "Variance, covariance & lois usuelles",
                        "estimated_minutes": 45,
                        "difficulty": 4,
                        "mastery_level": 2,
                        "repetitions": 1,
                        "last_reviewed_at": iso_days_ago(4.0),
                        "history": [
                            {"date": iso_days_ago(4.0), "score": 2},
                        ],
                    },
                    {
                        "id": "st-ch3",
                        "title": "Estimation ponctuelle & intervalles de confiance",
                        "estimated_minutes": 40,
                        "difficulty": 4,
                        "mastery_level": 2,
                        "repetitions": 0,
                        "last_reviewed_at": None,
                        "history": [],
                    },
                ],
            },
            {
                "id": "net-102",
                "name": "Réseaux & Architecture TCP/IP",
                "coefficient": 3.0,
                "exam_date": date_in_days(10),
                "chapters": [
                    {
                        "id": "net-ch1",
                        "title": "Modèle OSI, topologies & trames",
                        "estimated_minutes": 30,
                        "difficulty": 2,
                        "mastery_level": 4,
                        "repetitions": 3,
                        "last_reviewed_at": iso_days_ago(2.0),
                        "history": [
                            {"date": iso_days_ago(12.0), "score": 3},
                            {"date": iso_days_ago(6.0), "score": 4},
                            {"date": iso_days_ago(2.0), "score": 4},
                        ],
                    },
                    {
                        "id": "net-ch2",
                        "title": "Adressage IPv4, masques & sous-réseaux VLSM",
                        "estimated_minutes": 45,
                        "difficulty": 4,
                        "mastery_level": 3,
                        "repetitions": 1,
                        "last_reviewed_at": iso_days_ago(6.5),
                        "history": [
                            {"date": iso_days_ago(6.5), "score": 3},
                        ],
                    },
                ],
            },
            {
                "id": "sys-103",
                "name": "Systèmes Linux & Algorithmique",
                "coefficient": 2.0,
                "exam_date": date_in_days(14),
                "chapters": [
                    {
                        "id": "sys-ch1",
                        "title": "Processus, signaux, permissions & shell",
                        "estimated_minutes": 30,
                        "difficulty": 3,
                        "mastery_level": 4,
                        "repetitions": 2,
                        "last_reviewed_at": iso_days_ago(3.0),
                        "history": [
                            {"date": iso_days_ago(8.0), "score": 3},
                            {"date": iso_days_ago(3.0), "score": 4},
                        ],
                    },
                    {
                        "id": "sys-ch2",
                        "title": "Complexité, graphes & programmation dynamique",
                        "estimated_minutes": 50,
                        "difficulty": 5,
                        "mastery_level": 2,
                        "repetitions": 1,
                        "last_reviewed_at": iso_days_ago(7.0),
                        "history": [
                            {"date": iso_days_ago(7.0), "score": 2},
                        ],
                    },
                ],
            },
        ],
    }

def save_data(data: dict, filepath: str | Path = DEFAULT_DATA_PATH) -> None:
    """Sauvegarde les données au format JSON de manière propre."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data(filepath: str | Path = DEFAULT_DATA_PATH) -> dict:
    """Charge les données JSON. Si le fichier n'existe pas ou est invalide, génère la démo."""
    path = Path(filepath)
    if not path.exists():
        data = generate_demo_data()
        save_data(data, path)
        return data

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "courses" not in data:
            raise ValueError("Structure JSON incomplète")
        return data
    except (json.JSONDecodeError, ValueError):
        data = generate_demo_data()
        save_data(data, path)
        return data