"""
Warstwa bazy danych (SQLite) - trwale przechowywanie sesji/rund/rak/decyzji,
wspolne dla ludzi i botow (patrz notatki projektu po uzasadnienie schematu).

Ten modul jest samodzielny i przetestowany, ale NIE jest jeszcze podpiety
pod engine.py/main.py - to swiadoma decyzja, zeby nie ruszac dzialajacego
kodu przy okazji dodawania bazy. Podpiecie (np. funkcja notify wywolujaca
ponizsze log_*) to naturalny nastepny krok, gdy zaczniemy pisac pierwsza
symulacje/bota.

WYDAJNOSC PRZY MASOWEJ SYMULACJI: funkcje log_round/log_hand/log_decision
CELOWO nie robia commit() same - przy setkach tysiecy wywolan zapis na
dysk po kazdym pojedynczym wierszu byiby wolny. Wywolujacy (petla
symulacji) powinien wolac conn.commit() okresowo (np. co N rund) albo na
koncu sesji, nie po kazdym insertcie. Funkcje "konfiguracyjne"
(agent/rule_profile/session - rzadkie, jednorazowe) commitują od razu.
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "blackjack_data.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    config TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (name, kind)
);

CREATE TABLE IF NOT EXISTS rule_profiles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    num_decks INTEGER NOT NULL,
    cut_card_penetration REAL NOT NULL,
    das_allowed INTEGER NOT NULL,
    max_hands INTEGER NOT NULL,
    min_bet INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id),
    rule_profile_id INTEGER NOT NULL REFERENCES rule_profiles(id),
    starting_bankroll REAL NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    round_number INTEGER NOT NULL,
    bet REAL NOT NULL,
    bankroll_before REAL NOT NULL,
    bankroll_after REAL
);

CREATE TABLE IF NOT EXISTS hands (
    id INTEGER PRIMARY KEY,
    round_id INTEGER NOT NULL REFERENCES rounds(id),
    hand_number INTEGER NOT NULL,
    bet REAL NOT NULL,
    final_value INTEGER,
    result TEXT,
    payout REAL
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY,
    hand_id INTEGER NOT NULL REFERENCES hands(id),
    decision_index INTEGER NOT NULL,
    hand_value INTEGER NOT NULL,
    is_soft INTEGER NOT NULL,
    dealer_upcard INTEGER NOT NULL,
    allowed_actions TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    optimal_action TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_rounds_session ON rounds(session_id);
CREATE INDEX IF NOT EXISTS idx_hands_round ON hands(round_id);
CREATE INDEX IF NOT EXISTS idx_decisions_hand ON decisions(hand_id);
"""


def connect(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # duzo szybsze masowe zapisy
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# --- Funkcje "konfiguracyjne" - rzadkie, commitują od razu ---

def get_or_create_agent(conn, name, kind, config=None):
    cur = conn.execute("SELECT id FROM agents WHERE name = ? AND kind = ?", (name, kind))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO agents (name, kind, config) VALUES (?, ?, ?)",
        (name, kind, config),
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_rule_profile(conn, name, num_decks, cut_card_penetration,
                                das_allowed, max_hands, min_bet):
    cur = conn.execute("SELECT id FROM rule_profiles WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        """INSERT INTO rule_profiles
           (name, num_decks, cut_card_penetration, das_allowed, max_hands, min_bet)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, num_decks, cut_card_penetration, int(das_allowed), max_hands, min_bet),
    )
    conn.commit()
    return cur.lastrowid


def start_session(conn, agent_id, rule_profile_id, starting_bankroll):
    cur = conn.execute(
        "INSERT INTO sessions (agent_id, rule_profile_id, starting_bankroll) VALUES (?, ?, ?)",
        (agent_id, rule_profile_id, starting_bankroll),
    )
    conn.commit()
    return cur.lastrowid


def end_session(conn, session_id):
    conn.execute("UPDATE sessions SET ended_at = datetime('now') WHERE id = ?", (session_id,))
    conn.commit()


def reset_agent_sessions(conn, agent_name, kind="bot"):
    """
    Kasuje WSZYSTKIE dane symulacji (sessions/rounds/hands/decisions) dla
    danego agenta, ale zostawia sam wiersz w `agents` - dzieki temu kolejne
    `get_or_create_agent` nadal zwroci ten sam `agent_id`, zamiast plodzic
    nowego agenta przy kazdym uruchomieniu.

    Po co to jest: notebook sprawozdania odpala symulacje NAPRAWDE (nie
    czyta tylko wczesniej zebranych danych) za kazdym razem, gdy komorki sa
    wykonywane od nowa. Bez resetu kazde kolejne "Run All" DOKLADALOBY nowe
    sesje do tych z poprzedniego uruchomienia (baza roslaby bez konca, a
    wykresy mieszalyby stare i nowe przebiegi w jedna, coraz mniej
    czytelna "srednia"). Wywolanie tej funkcji PRZED ponownym odpaleniem
    symulacji danego bota daje deterministyczny efekt: baza zawsze
    odzwierciedla TYLKO najswiezszy przebieg dla tego agenta.

    Usuwanie w kolejnosci od dzieci do rodzica (foreign_keys sa ON w
    connect()), zeby nie zlamac wiezow integralnosci referencyjnej.
    """
    cur = conn.execute("SELECT id FROM agents WHERE name = ? AND kind = ?", (agent_name, kind))
    row = cur.fetchone()
    if row is None:
        return  # agent jeszcze nie istnieje (pierwsze uruchomienie) - nic do skasowania

    agent_id = row[0]

    conn.execute(
        """DELETE FROM decisions WHERE hand_id IN (
               SELECT h.id FROM hands h
               JOIN rounds r ON h.round_id = r.id
               JOIN sessions s ON r.session_id = s.id
               WHERE s.agent_id = ?
           )""",
        (agent_id,),
    )
    conn.execute(
        """DELETE FROM hands WHERE round_id IN (
               SELECT r.id FROM rounds r
               JOIN sessions s ON r.session_id = s.id
               WHERE s.agent_id = ?
           )""",
        (agent_id,),
    )
    conn.execute(
        """DELETE FROM rounds WHERE session_id IN (
               SELECT id FROM sessions WHERE agent_id = ?
           )""",
        (agent_id,),
    )
    conn.execute("DELETE FROM sessions WHERE agent_id = ?", (agent_id,))
    conn.commit()


# --- Funkcje "gorace" (wywolywane co runde/rece/decyzje) - BEZ auto-commit ---

def log_round(conn, session_id, round_number, bet, bankroll_before, bankroll_after=None):
    cur = conn.execute(
        """INSERT INTO rounds (session_id, round_number, bet, bankroll_before, bankroll_after)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, round_number, bet, bankroll_before, bankroll_after),
    )
    return cur.lastrowid


def finish_round(conn, round_id, bankroll_after):
    conn.execute("UPDATE rounds SET bankroll_after = ? WHERE id = ?", (bankroll_after, round_id))


def log_hand(conn, round_id, hand_number, bet, final_value=None, result=None, payout=None):
    cur = conn.execute(
        """INSERT INTO hands (round_id, hand_number, bet, final_value, result, payout)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (round_id, hand_number, bet, final_value, result, payout),
    )
    return cur.lastrowid


def log_decision(conn, hand_id, decision_index, hand_value, is_soft, dealer_upcard,
                  allowed_actions, action_taken, optimal_action=None):
    conn.execute(
        """INSERT INTO decisions
           (hand_id, decision_index, hand_value, is_soft, dealer_upcard,
            allowed_actions, action_taken, optimal_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (hand_id, decision_index, hand_value, int(is_soft), dealer_upcard,
         ",".join(allowed_actions), action_taken, optimal_action),
    )


# --- Kilka gotowych zapytan pod analize/srednie ---

def average_bankroll_change_per_round(conn, session_id):
    cur = conn.execute(
        """SELECT AVG(bankroll_after - bankroll_before) FROM rounds
           WHERE session_id = ? AND bankroll_after IS NOT NULL""",
        (session_id,),
    )
    return cur.fetchone()[0]


def win_rate(conn, session_id):
    cur = conn.execute(
        """SELECT
               SUM(CASE WHEN h.result IN ('win', 'blackjack') THEN 1 ELSE 0 END) * 1.0
               / COUNT(*)
           FROM hands h
           JOIN rounds r ON h.round_id = r.id
           WHERE r.session_id = ?""",
        (session_id,),
    )
    return cur.fetchone()[0]


def deviation_rate(conn, session_id):
    # % decyzji, w ktorych bot/gracz odbiegl od optimal_action - wymaga,
    # zeby optimal_action bylo wypelnione (dopiero gdy bedzie bot if/else
    # jako punkt odniesienia).
    cur = conn.execute(
        """SELECT
               SUM(CASE WHEN d.action_taken != d.optimal_action THEN 1 ELSE 0 END) * 1.0
               / COUNT(*)
           FROM decisions d
           JOIN hands h ON d.hand_id = h.id
           JOIN rounds r ON h.round_id = r.id
           WHERE r.session_id = ? AND d.optimal_action IS NOT NULL""",
        (session_id,),
    )
    return cur.fetchone()[0]


# --- Most z notify() (engine.py) do bazy ---

class DbNotifyRound:
    """
    notify() kompatybilne z engine.play_round, ktore loguje decyzje i rece
    JEDNEJ rundy do bazy. Tworzone na nowo dla kazdej rundy (potrzebuje
    round_id, ktore powstaje przez log_round PRZED wywolaniem play_round).

    Uzycie (w petli symulacji):
        round_id = database.log_round(conn, session_id, nr, bet, player.bankroll)
        notify = DbNotifyRound(conn, round_id)
        results = engine.play_round(player, dealer, shoe, bet, decide, notify)
        database.finish_round(conn, round_id, player.bankroll)
        conn.commit()  # okresowo, nie po kazdej rundzie - patrz docstring modulu

    Decyzje sa buforowane w pamieci (per hand_number) i zapisywane do bazy
    dopiero gdy przyjdzie "hand_resolved" dla danej reki - bo wiersz w hands
    (rodzic decisions przez klucz obcy hand_id) nie istnieje wczesniej;
    decyzje w engine.py zapadaja PRZED rozstrzygnieciem reki.
    """

    def __init__(self, conn, round_id):
        self.conn = conn
        self.round_id = round_id
        self._pending_decisions = {}

    def __call__(self, event, **data):
        if event == "decision":
            hn = data["hand_number"]
            self._pending_decisions.setdefault(hn, []).append(data)

        elif event == "hand_resolved":
            hn = data["hand_number"]
            hand_id = log_hand(
                self.conn, self.round_id, hn,
                bet=data["bet"], final_value=data["final_value"],
                result=data["result"], payout=data["payout"],
            )
            for idx, dec in enumerate(self._pending_decisions.pop(hn, [])):
                log_decision(
                    self.conn, hand_id, idx,
                    hand_value=dec["hand_value"], is_soft=dec["is_soft"],
                    dealer_upcard=dec["dealer_upcard"],
                    allowed_actions=dec["allowed_actions"],
                    action_taken=dec["action"],
                )

        # Pozostale eventy (board_update, hit, stand, bust, twenty_one, double,
        # split, dealer_blackjack, player_blackjack, win, push, lose) sa tu
        # nieistotne - agregaty w bazie licza sie z hands/decisions, nie z
        # pojedynczych zdarzen "kosmetycznych" (te sa dla console_ui).
