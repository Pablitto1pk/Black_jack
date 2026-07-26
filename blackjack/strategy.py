"""
Strategie decyzyjne (decide/decide_bet) dla silnika blackjacka.

Kazda strategia w tym module implementuje kontrakt engine.decide /
engine.decide_bet (patrz docstring engine.py) i moze byc podlaczona 1:1
do engine.play_round / simulation.run_session, bez zadnych zmian w
silniku ani w simulation.py.

Docelowo: obok ponizszej strategii testowej stanie tu basic_strategy_decide
(if/else = "basic strategy", matematycznie dowiedziony optimum bez liczenia
kart - patrz notatki projektu), potem strategia oparta o ML, a jeszcze
pozniej strategia z liczeniem kart + Kelly criterion (decide_bet).
"""


def flat_stand_decide(hand, dealer_upcard, allowed_actions):
    """
    "Strategia" testowa: zawsze Stand, jesli tylko to mozliwe.

    To DE FACTO tez jest strategia (kazda funkcja spelniajaca kontrakt
    decide() nia jest) - tylko celowo najprostsza i najgorsza z sensownych.
    Sluzy jako dolny punkt odniesienia (najgorszy mozliwy wynik) i jako
    smoke-test calego pipeline'u engine -> notify -> DbNotifyRound -> SQLite,
    NIE jako realna strategia gry.
    """
    return "S"


def flat_bet(player, min_bet, max_bet, shoe):
    """
    Stala stawka rowna minimalnej - brak liczenia kart, wiec zmiana stawki
    i tak nie mialaby sensu (patrz dyskusja w projekcie o EV/wariancji:
    bez informacji o skladzie buta, wieksza stawka to tylko wieksza
    wariancja wokol tej samej ujemnej EV, nie lepszy wynik).
    """
    if player.bankroll < min_bet:
        return None
    return min_bet


# ---------------------------------------------------------------------------
# Basic strategy - tabele decyzyjne
#
# Zrodlo: github.com/gsdriver/blackjack-strategy (MIT License), plik
# src/Suggestion.js - silnik strategii sparametryzowany dokladnie takimi
# samymi opcjami gry, jakie ma nasz engine.py. Tabele ponizej zostaly
# WYGENEROWANE programistycznie (nie przepisane z pamieci/internetu), przez
# wywolanie GetRecommendedPlayerAction(...) z tej biblioteki dla kazdej reki
# (hard 9-17, soft 13-20, kazda para) przeciwko kazdej karcie krupiera, z
# opcjami:
#   numberOfDecks: 6            <- engine.NUM_DECKS
#   hitSoft17: false            <- engine.py: "while dealer.hand.value < 17"
#                                   (brak wyjatku dla soft 17 = S17)
#   doubleAfterSplit: false     <- engine.DAS_ALLOWED = False
#   maxSplitHands: 4            <- engine.MAX_HANDS
#   surrender: "none"           <- engine.py nigdy nie oferuje surrender
#   offerInsurance: false       <- engine.py nie modeluje ubezpieczenia
#   doubleRange: [0, 21]        <- double dozwolony na kazde pierwsze 2 karty
#   resplitAces: false          <- rozdzielone Asy dostaja dokladnie 1 karte
#   strategyComplexity: "simple"<- total + is_soft, bez overrides na dokladny
#                                   sklad kart (ExactComposition.js pominiete)
#
# Biblioteka uzywa konwencji Asa=1 (zarowno dla karty krupiera jak i pary As-As);
# w tabelach ponizej przemapowane na konwencje tego projektu, gdzie Ace.value=11
# (patrz cards.py). Wynik zweryfikowany testem jednostkowym biblioteki
# (40/40 testow w test/suggestion.spec.js) przed uzyciem.
#
# Klucz zewnetrzny = wartosc reki gracza (total), klucz wewnetrzny = wartosc
# karty krupiera (2-10, 11=As). Wartosc to para (akcja_podstawowa, akcja_awaryjna),
# gdzie akcja_awaryjna jest uzywana gdy akcja_podstawowa to "D" (double), ale
# "D" nie jest tego rozdania dostepne w allowed_actions (np. brak srodkow na
# double, lub reka pochodzi ze splitu i DAS jest wylaczony).
HARD_TOTALS = {
    9: {2: ("H", "H"), 3: ("D", "H"), 4: ("D", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    10: {2: ("D", "H"), 3: ("D", "H"), 4: ("D", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("D", "H"), 8: ("D", "H"), 9: ("D", "H"), 10: ("H", "H"), 11: ("H", "H")},
    11: {2: ("D", "H"), 3: ("D", "H"), 4: ("D", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("D", "H"), 8: ("D", "H"), 9: ("D", "H"), 10: ("D", "H"), 11: ("H", "H")},
    12: {2: ("H", "H"), 3: ("H", "H"), 4: ("S", "S"), 5: ("S", "S"), 6: ("S", "S"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    13: {2: ("S", "S"), 3: ("S", "S"), 4: ("S", "S"), 5: ("S", "S"), 6: ("S", "S"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    14: {2: ("S", "S"), 3: ("S", "S"), 4: ("S", "S"), 5: ("S", "S"), 6: ("S", "S"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    15: {2: ("S", "S"), 3: ("S", "S"), 4: ("S", "S"), 5: ("S", "S"), 6: ("S", "S"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    16: {2: ("S", "S"), 3: ("S", "S"), 4: ("S", "S"), 5: ("S", "S"), 6: ("S", "S"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    17: {2: ("S", "S"), 3: ("S", "S"), 4: ("S", "S"), 5: ("S", "S"), 6: ("S", "S"), 7: ("S", "S"), 8: ("S", "S"), 9: ("S", "S"), 10: ("S", "S"), 11: ("S", "S")},
}

SOFT_TOTALS = {
    13: {2: ("H", "H"), 3: ("H", "H"), 4: ("H", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    14: {2: ("H", "H"), 3: ("H", "H"), 4: ("H", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    15: {2: ("H", "H"), 3: ("H", "H"), 4: ("D", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    16: {2: ("H", "H"), 3: ("H", "H"), 4: ("D", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    17: {2: ("H", "H"), 3: ("D", "H"), 4: ("D", "H"), 5: ("D", "H"), 6: ("D", "H"), 7: ("H", "H"), 8: ("H", "H"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
    18: {2: ("S", "S"), 3: ("D", "S"), 4: ("D", "S"), 5: ("D", "S"), 6: ("D", "S"), 7: ("S", "S"), 8: ("S", "S"), 9: ("H", "H"), 10: ("H", "H"), 11: ("H", "H")},
}

# Para -> True/False (czy split jest podstawowa/poprawna akcja przeciwko danej
# karcie krupiera). Klucz zewnetrzny = wartosc pojedynczej karty w parze
# (11 = para Asow, 10 = para 10/J/Q/K - w tym projekcie hand.can_split()
# jest oparte na wartosci karty, wiec 10+K tez liczy sie jako "para").
PAIRS_SPLIT = {
    11: {2: True, 3: True, 4: True, 5: True, 6: True, 7: True, 8: True, 9: True, 10: True, 11: True},
    2: {2: False, 3: False, 4: True, 5: True, 6: True, 7: True, 8: False, 9: False, 10: False, 11: False},
    3: {2: False, 3: False, 4: True, 5: True, 6: True, 7: True, 8: False, 9: False, 10: False, 11: False},
    4: {2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False, 10: False, 11: False},
    5: {2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False, 10: False, 11: False},
    6: {2: False, 3: True, 4: True, 5: True, 6: True, 7: False, 8: False, 9: False, 10: False, 11: False},
    7: {2: True, 3: True, 4: True, 5: True, 6: True, 7: True, 8: False, 9: False, 10: False, 11: False},
    8: {2: True, 3: True, 4: True, 5: True, 6: True, 7: True, 8: True, 9: True, 10: True, 11: True},
    9: {2: True, 3: True, 4: True, 5: True, 6: True, 7: False, 8: True, 9: True, 10: False, 11: False},
    10: {2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False, 10: False, 11: False},
}


def basic_strategy_decide(hand, dealer_upcard, allowed_actions):
    """
    Prawdziwa "basic strategy" - matematycznie wyliczona optymalna decyzja
    (bez liczenia kart) dla kazdej kombinacji (reka gracza, karta krupiera),
    dopasowana do DOKLADNIE tych zasad stolu co engine.py (S17, DAS off,
    6 talii, bez surrender/ubezpieczenia - patrz komentarz przy tabelach
    powyzej). Nie jest to strategia "ogolna z internetu" - kazda zmienna
    zasada (np. H17 zamiast S17, albo wlaczony DAS) zmienia konkretne pola
    tych tabel, dlatego tabele zostaly wygenerowane specjalnie pod to gre.

    Kolejnosc sprawdzania (zgodna z tym, jak realny gracz podejmuje decyzje
    przy stole):
      1. Czy to para i czy tabela mowi "split" - i czy split jest w ogole
         dostepny (allowed_actions) w tym rozdaniu (np. bankroll, MAX_HANDS)?
      2. Jesli nie splitujemy (para ktora nie powinna byc split, albo split
         niedostepny), reka jest traktowana zwyczajnie wg swojej wartosci
         totalnej - stad brak osobnej tabeli "co robic z para po
         nie-splicie": to jest juz dokladnie ten sam przypadek co
         odpowiedni hard/soft total w tabelach ponizej (np. 5-5 nie-split
         to zwykle hard 10).
      3. Hard/soft total spoza zakresu tabel (hard <=8, hard 18-20, soft 12
         = para Asow nie-split, soft 19-20) ma jedna, stala odpowiedz
         niezaleznie od karty krupiera - potwierdzone przy generowaniu
         tabel (patrz derive2.js), wiec nie ma sensu trzymac tego w
         slowniku.
      4. Jesli tabela mowi "double", ale double nie jest dostepny w tym
         rozdaniu (allowed_actions), uzywamy zapisanej z gory akcji
         awaryjnej (hit albo stand, w zaleznosci od reki).
    """
    dealer_value = dealer_upcard.value  # Card.value: 2-10, As=11 (patrz cards.py)

    if "P" in allowed_actions and hand.can_split():
        pair_value = hand.cards[0].value
        if PAIRS_SPLIT[pair_value][dealer_value]:
            return "P"
        # nie splitujemy - reka "spada" do zwyklej logiki hard/soft ponizej

    total = hand.value
    is_soft = hand.aces > 0 and total < 21  # ta sama formula co w engine.play_round (event "decision")

    if is_soft:
        if total <= 12:   # A+A niesplitowane (jedyny mozliwy soft total <=12) - zawsze Hit
            return "H"
        if total >= 19:   # soft 19/20 - zawsze Stand
            return "S"
        primary, fallback = SOFT_TOTALS[total][dealer_value]
    else:
        if total <= 8:    # hard <=8 (w tym niesplitowane 2-2/3-3/4-4) - zawsze Hit
            return "H"
        if total >= 18:   # hard 18-20 - zawsze Stand
            return "S"
        primary, fallback = HARD_TOTALS[total][dealer_value]

    if primary == "D" and "D" not in allowed_actions:
        return fallback
    return primary
