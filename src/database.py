from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


DATABASE_PATH = "data/ranking.db"
TOP_SCORE_LIMIT = 10


@dataclass(frozen=True)
class ScoreRecord:
    player_name: str
    score: int
    reached_boss: bool
    defeated_boss: bool
    created_at: str


def initialize_database() -> None:
    try:
        path = Path(DATABASE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        reached_boss INTEGER NOT NULL,
                        defeated_boss INTEGER NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                _prune_scores(connection)
    except (OSError, sqlite3.Error) as exc:
        print(f"Aviso de banco de dados: não foi possível inicializar o ranking: {exc}")


def save_score(player_name: str, score: int, reached_boss: bool, defeated_boss: bool) -> None:
    try:
        initialize_database()
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO scores (
                        player_name,
                        score,
                        reached_boss,
                        defeated_boss,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        player_name,
                        score,
                        int(reached_boss),
                        int(defeated_boss),
                        created_at,
                    ),
                )
                _prune_scores(connection)
    except (OSError, sqlite3.Error) as exc:
        print(f"Aviso de banco de dados: não foi possível salvar a pontuação: {exc}")


def get_top_scores(limit: int = TOP_SCORE_LIMIT) -> list[ScoreRecord]:
    try:
        initialize_database()
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            rows = connection.execute(
                """
                SELECT player_name, score, reached_boss, defeated_boss, created_at
                FROM scores
                ORDER BY score DESC, defeated_boss DESC, reached_boss DESC, created_at ASC
                LIMIT ?;
                """,
                (limit,),
            ).fetchall()
    except (OSError, sqlite3.Error) as exc:
        print(f"Aviso de banco de dados: não foi possível carregar o ranking: {exc}")
        return []

    return [
        ScoreRecord(
            player_name=row[0],
            score=int(row[1]),
            reached_boss=bool(row[2]),
            defeated_boss=bool(row[3]),
            created_at=row[4],
        )
        for row in rows
    ]


def _prune_scores(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        DELETE FROM scores
        WHERE id NOT IN (
            SELECT id
            FROM scores
            ORDER BY
                score DESC,
                defeated_boss DESC,
                reached_boss DESC,
                created_at ASC,
                id ASC
            LIMIT ?
        );
        """,
        (TOP_SCORE_LIMIT,),
    )
