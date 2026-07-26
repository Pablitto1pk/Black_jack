"""
Symulacja bez konsoli - do testowania silnika/bazy i (docelowo) botow.

Domyslna strategia (flat_stand_decide/flat_bet) mieszka w
blackjack/strategy.py - to zwykla strategia jak kazda inna (spelnia
kontrakt decide()/decide_bet()), tylko celowo najprostsza i najgorsza z
sensownych, uzywana jako dolny punkt odniesienia i smoke-test calego
pipeline'u engine -> notify -> DbNotifyRound -> SQLite. run_session()
przyjmuje decide/decide_bet jako parametry, wiec podstawienie prawdziwej
strategii (np. basic_strategy_decide) nie wymaga zadnych zmian w tym pliku.

Dwie funkcje symulujace, dwa rozne zastosowania:
- run_session() - gra ustalona z gory liczbe rund, tasuje sie w tle ile
  razy trzeba. Dobre pod "smoke test" i dlugie sesje.
- run_session_n_shoes() - gra dokladnie N butow (od pierwszej karty do
  karty odciecia), koniec po N-tym przetasowaniu albo wczesniej jak
  zabraknie na zaklad. To jest jednostka pod przyszle liczenie
  kart/penetracje - running count zeruje sie przy kazdym tasowaniu, wiec
  "ile rund" nie ma tu znaczenia, tylko "ile butow".

Zadna z nich nic nie printuje - to jest tryb "headless" symulacji, w
przeciwienstwie do main.py (konsolowa powloka nad tym samym engine.play_round).
"""

from blackjack.cards import Deck
from blackjack.participants import Player, Dealer
from blackjack import engine
from blackjack import database
from blackjack.strategy import flat_stand_decide, flat_bet


def _open_session(conn, agent_name, starting_bankroll):
    """Wspolny kawalek dla obu run_session* - agent/rule_profile/session, zwraca session_id."""
    agent_id = database.get_or_create_agent(conn, agent_name, kind="bot")
    rule_profile_id = database.get_or_create_rule_profile(
        conn, name="default",
        num_decks=engine.NUM_DECKS,
        cut_card_penetration=engine.CUT_CARD_PENETRATION,
        das_allowed=engine.DAS_ALLOWED,
        max_hands=engine.MAX_HANDS,
        min_bet=engine.MIN_BET,
    )
    return database.start_session(conn, agent_id, rule_profile_id, starting_bankroll)


def run_session(conn, agent_name, num_rounds, starting_bankroll=1000,
                 decide=flat_stand_decide, decide_bet=flat_bet):
    """
    Rozgrywa num_rounds rund dla jednego agenta (bota) i loguje wszystko do
    bazy pod jedna sesja (agents/rule_profiles/sessions/rounds/hands/decisions).
    Zwraca session_id.
    """
    session_id = _open_session(conn, agent_name, starting_bankroll)

    player = Player(name=agent_name, bankroll=starting_bankroll)
    dealer = Dealer()
    shoe = Deck(num_decks=engine.NUM_DECKS)
    shoe.shuffle()

    for round_number in range(1, num_rounds + 1):
        if engine.needs_reshuffle(shoe):
            shoe = Deck(num_decks=engine.NUM_DECKS)
            shoe.shuffle()

        max_bet = player.bankroll // engine.BET_RESERVE_MULTIPLIER
        bet = decide_bet(player, engine.MIN_BET, max_bet, shoe)
        if bet is None:
            break

        bankroll_before = player.bankroll
        round_id = database.log_round(conn, session_id, round_number, bet, bankroll_before)
        notify = database.DbNotifyRound(conn, round_id)

        engine.play_round(player, dealer, shoe, bet, decide, notify)

        database.finish_round(conn, round_id, player.bankroll)

        if round_number % 500 == 0:
            conn.commit()  # okresowy commit - patrz docstring database.py

    conn.commit()
    database.end_session(conn, session_id)
    return session_id


def run_session_n_shoes(conn, agent_name, num_shoes, starting_bankroll=1000,
                         decide=flat_stand_decide, decide_bet=flat_bet):
    """
    Jak run_session, ale koniec sesji jest zdefiniowany przez liczbe butow
    (przetasowan), nie liczbe rund. Gramy but od pierwszej karty do karty
    odciecia, potem albo tasujemy i lecimy dalej (jesli jeszcze nie
    wyczerpalismy num_shoes), albo konczymy sesje.

    Zwraca (session_id, busted):
    - busted=False - sesja przezyla wszystkie num_shoes butow.
    - busted=True - zabraklo na zaklad (decide_bet zwrocilo None) zanim
      zdazylismy odegrac wszystkie num_shoes butow. To jest wlasnie ta
      informacja, ktorej nie da sie latwo wyciagnac pozniej z samej
      tabeli rounds (nie wiadomo z niej, ile butow ktos zdazyl rozegrac),
      wiec caller (np. notebook) musi ja zebrac na biezaco z kazdego
      wywolania.
    """
    session_id = _open_session(conn, agent_name, starting_bankroll)

    player = Player(name=agent_name, bankroll=starting_bankroll)
    dealer = Dealer()
    shoe = Deck(num_decks=engine.NUM_DECKS)
    shoe.shuffle()

    round_number = 0
    shoes_played = 0
    busted = False

    while True:
        if engine.needs_reshuffle(shoe):
            shoes_played += 1
            if shoes_played >= num_shoes:
                break
            shoe = Deck(num_decks=engine.NUM_DECKS)
            shoe.shuffle()

        max_bet = player.bankroll // engine.BET_RESERVE_MULTIPLIER
        bet = decide_bet(player, engine.MIN_BET, max_bet, shoe)
        if bet is None:
            busted = True
            break

        round_number += 1
        bankroll_before = player.bankroll
        round_id = database.log_round(conn, session_id, round_number, bet, bankroll_before)
        notify = database.DbNotifyRound(conn, round_id)

        engine.play_round(player, dealer, shoe, bet, decide, notify)

        database.finish_round(conn, round_id, player.bankroll)

    conn.commit()
    database.end_session(conn, session_id)
    return session_id, busted


if __name__ == "__main__":
    conn = database.connect()
    session_id = run_session(conn, agent_name="flat_stand_bot", num_rounds=5000)
    print(f"Session {session_id} done.")
    print("Win rate:", database.win_rate(conn, session_id))
    print("Avg bankroll change/round:", database.average_bankroll_change_per_round(conn, session_id))
