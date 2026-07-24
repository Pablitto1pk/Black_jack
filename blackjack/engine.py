"""
Silnik gry - reguly Blackjacka, calkowicie niezalezne od tego, JAK podejmowane
sa decyzje (input z konsoli, bot, przycisk w GUI) i JAK ogłaszane sa zdarzenia
(print, log do bazy, rendering).

decide(hand, dealer_upcard, allowed_actions) -> jedna z wartosci allowed_actions
    Silnik UFA, ze zwrocona wartosc nalezy do allowed_actions - walidacja "czy
    user/bot nie strzelil glupoty" to problem KONKRETNEJ implementacji decide
    (np. console_decide), nie silnika.

decide_bet(player, min_bet, max_bet, shoe) -> int (kwota zakladu) albo None
    None = koniec gry (rezygnacja). Parametr shoe jest dzis ignorowany przez
    wszystkie implementacje - zostawiony pod przyszle boty liczace karty
    (Kelly criterion), zeby nie trzeba bylo pozniej zmieniac tej sygnatury.

notify(event, **data) -> None
    Silnik "ogłasza" co sie dzieje, nie wiedzac (i nie musząc wiedziec), czy
    ktokolwiek go slucha.
"""

from blackjack.hand import Hand

MIN_BET = 50
MAX_HANDS = 4  # maksymalna liczba rak po splitach (3 splity => 4 rece)
DAS_ALLOWED = False  # double after split - wylaczone (zgodnie z przyjetymi zasadami stolu)

# Patrz console_manual.py po uzasadnienie tej formuly (rozdzielone na wypadek DAS)
if DAS_ALLOWED:
    BET_RESERVE_MULTIPLIER = 2 * MAX_HANDS
else:
    BET_RESERVE_MULTIPLIER = MAX_HANDS

NUM_DECKS = 6
CUT_CARD_PENETRATION = 0.5
SHOE_SIZE = NUM_DECKS * 52

WYPLATY = {"bust": 0, "lose": 0, "push": 1, "win": 2, "blackjack": 2.5}


def needs_reshuffle(shoe):
    return len(shoe.all_cards) <= SHOE_SIZE * (1 - CUT_CARD_PENETRATION)


def apply_payouts(player, results, notify):
    for i in range(len(results)):
        hand = player.hands[i]
        wynik = results[i]
        payout = hand.bet * WYPLATY[wynik]
        player.bankroll += payout

        if wynik in ("win", "blackjack"):
            notify("win", hand_number=i + 1, amount=payout - hand.bet)
        elif wynik == "push":
            notify("push", hand_number=i + 1)
        else:
            notify("lose", hand_number=i + 1, amount=hand.bet)


def play_round(player, dealer, shoe, bet, decide, notify):
    # Zaklad zostal juz ustalony przez wywolujacego (glowna petla) - tu tylko
    # egzekwujemy go i rozgrywamy DOKLADNIE jedna runde.
    player.bankroll -= bet

    player.hands = []
    first_hand = Hand()
    first_hand.bet = bet
    player.add_hand(first_hand)
    dealer.hand = Hand()

    for _ in range(2):
        player.hands[0].add_card(shoe.deal_one())
        dealer.hand.add_card(shoe.deal_one())

    notify("board_update", player=player, dealer=dealer, reveal_dealer=False)

    player_has_bj = (len(player.hands[0].cards) == 2 and player.hands[0].value == 21)
    dealer_has_bj = dealer.check_for_blackjack()

    if dealer_has_bj:
        notify("dealer_blackjack")
        notify("board_update", player=player, dealer=dealer, reveal_dealer=True)
        results = ["push"] if player_has_bj else ["lose"]
        apply_payouts(player, results, notify)
        return results

    results = [None]
    if player_has_bj:
        notify("player_blackjack")
        results[0] = "blackjack"

    # Petla akcji gracza (H/S/D/P) - indeksowa, bo split moze dopisac rece w trakcie
    i = 0
    while i < len(player.hands):
        if results[i] is not None:
            i += 1
            continue

        hand = player.hands[i]

        while True:
            can_split = (hand.can_split() and len(player.hands) < MAX_HANDS
                         and player.bankroll >= hand.bet)
            can_double = (len(hand.cards) == 2 and player.bankroll >= hand.bet
                          and (DAS_ALLOWED or not hand.from_split))

            allowed_actions = ["H", "S"]
            if can_double:
                allowed_actions.append("D")
            if can_split:
                allowed_actions.append("P")

            decision = decide(hand, dealer.hand.cards[0], allowed_actions)
            assert decision in allowed_actions, (
                f"decide() zwrocilo niedozwolona akcje {decision!r}, "
                f"dozwolone byly: {allowed_actions} (to blad implementacji decide, nie silnika)"
            )

            if decision == "H":
                hand.add_card(shoe.deal_one())
                notify("hit", hand_number=i + 1, card=hand.cards[-1])
                notify("board_update", player=player, dealer=dealer, reveal_dealer=False)
                if hand.value > 21:
                    notify("bust", hand_number=i + 1)
                    results[i] = "bust"
                    break
                elif hand.value == 21:
                    notify("twenty_one", hand_number=i + 1)
                    results[i] = "stand"
                    break
                # inaczej: petla pyta dalej o kolejna decyzje dla tej reki

            elif decision == "S":
                notify("stand", hand_number=i + 1)
                results[i] = "stand"
                break

            elif decision == "D":
                player.bankroll -= hand.bet
                hand.bet *= 2
                notify("double", hand_number=i + 1)
                hand.add_card(shoe.deal_one())
                notify("hit", hand_number=i + 1, card=hand.cards[-1])
                notify("board_update", player=player, dealer=dealer, reveal_dealer=False)
                if hand.value > 21:
                    notify("bust", hand_number=i + 1)
                    results[i] = "bust"
                else:
                    notify("stand", hand_number=i + 1)
                    results[i] = "stand"
                break

            elif decision == "P":
                card1 = hand.cards[0]
                card2 = hand.cards[1]
                aces_split = (card1.rank == "Ace")

                # przebudowujemy pierwsza reke tak, by miala tylko pierwsza karte
                hand.cards = []
                hand.value = 0
                hand.aces = 0
                hand.add_card(card1)

                # druga reka dostaje druga karte i taki sam zaklad jak pierwsza
                new_hand = Hand()
                new_hand.add_card(card2)
                new_hand.bet = hand.bet

                hand.from_split = True
                new_hand.from_split = True

                player.bankroll -= hand.bet
                notify("split", hand_number=i + 1)

                # obie rece dostaja od razu po jednej nowej karcie
                hand.add_card(shoe.deal_one())
                notify("hit", hand_number=i + 1, card=hand.cards[-1])
                new_hand.add_card(shoe.deal_one())
                notify("hit", hand_number=i + 2, card=new_hand.cards[-1])

                player.hands.insert(i + 1, new_hand)

                if aces_split:
                    # rozdzielone Asy - kazda reka dostaje tylko jedna karte i od razu stoi
                    if hand.value > 21:
                        notify("bust", hand_number=i + 1)
                        results[i] = "bust"
                    else:
                        notify("stand", hand_number=i + 1)
                        results[i] = "stand"

                    if new_hand.value > 21:
                        notify("bust", hand_number=i + 2)
                        results.insert(i + 1, "bust")
                    else:
                        notify("stand", hand_number=i + 2)
                        results.insert(i + 1, "stand")

                    notify("board_update", player=player, dealer=dealer, reveal_dealer=False)
                    break
                else:
                    results.insert(i + 1, None)
                    notify("board_update", player=player, dealer=dealer, reveal_dealer=False)
                    if hand.value == 21:
                        notify("twenty_one", hand_number=i + 1)
                        results[i] = "stand"
                        break
                    # inaczej: petla pyta dalej dla tej samej (pierwszej) reki

        i += 1

    # Ruch krupiera
    while dealer.hand.value < 17:
        dealer.hand.add_card(shoe.deal_one())

    notify("board_update", player=player, dealer=dealer, reveal_dealer=True)

    # Rozstrzygniecie rak ktore stoja ("stand") - porownanie z krupierem
    for i in range(len(results)):
        if results[i] in ("bust", "blackjack"):
            continue
        if dealer.hand.value > 21:
            if results[i] == "stand":
                results[i] = "win"
        else:
            if dealer.hand.value < player.hands[i].value:
                results[i] = "win"
            elif dealer.hand.value == player.hands[i].value:
                results[i] = "push"
            else:
                results[i] = "lose"

    apply_payouts(player, results, notify)
    return results
