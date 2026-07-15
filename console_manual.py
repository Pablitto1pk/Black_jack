from blackjack.cards import Deck
from blackjack.participants import Player, Dealer
from blackjack.hand import Hand
from blackjack import console_ui as ui


#Inicjalizacja
player = Player(name="Gracz", bankroll=1000)
dealer = Dealer()

MIN_BET = 50
MAX_HANDS = 4  # maksymalna liczba rak po splitach (3 splity => 4 rece)
DAS_ALLOWED = False  # double after split - wylaczone (zgodnie z przyjetymi zasadami stolu)

# Najgorszy przypadek dla POJEDYNCZEGO zakladu B zalezy od DAS_ALLOWED:
# - gdy DAS wlaczone: mozna I splitowac DO MAX_HANDS rak, I kazda z nich podwoic ->
#   (MAX_HANDS-1) splitow + MAX_HANDS doubli + samo B na starcie = 2*MAX_HANDS*B
# - gdy DAS wylaczone: split i double wykluczaja sie na tej samej rece (po splicie
#   nie mozna juz podwoic), wiec najgorszy przypadek to po prostu maksymalna sciezka
#   samych splitow -> MAX_HANDS*B (co i tak >= "1 reka podwojona" = 2*B, dla MAX_HANDS>=2)
if DAS_ALLOWED:
    BET_RESERVE_MULTIPLIER = 2 * MAX_HANDS
else:
    BET_RESERVE_MULTIPLIER = MAX_HANDS

MIN_BANKROLL = MIN_BET * BET_RESERVE_MULTIPLIER  # rezerwa na najgorszy przypadek przy MIN_BET

NUM_DECKS = 6  # liczba talii w bucie (shoe)
CUT_CARD_PENETRATION = 0.5  # karta odcinajaca w polowie buta - po jej osiagnieciu tasujemy od nowa
SHOE_SIZE = NUM_DECKS * 52

shoe = Deck(num_decks=NUM_DECKS)
shoe.shuffle()

def needs_reshuffle(shoe):
    # Prawdziwy krupier tnie talie kartą odcinającą ustawioną w danym miejscu buta -
    # gdy do niej dojdzie, dogrywa biezaca reke, po czym tasuje od nowa przed kolejna.
    # My upraszczamy: sprawdzamy przed KAZDA nowa reka, czy zostalo wystarczajaco kart.
    return len(shoe.all_cards) <= SHOE_SIZE * (1 - CUT_CARD_PENETRATION)

WYPLATY = {"bust": 0,"lose": 0, "push": 1, "win": 2, "blackjack": 2.5}

def apply_payouts(player, results):
    for i in range(len(results)):
        hand = player.hands[i]
        wynik = results[i]
        payout = hand.bet * WYPLATY[wynik]
        player.bankroll += payout

        if wynik in ("win", "blackjack"):
            ui.display_win(payout - hand.bet)
        elif wynik == "push":
            ui.display_push()
        else:
            ui.display_lose(hand.bet)

def play_round(player, dealer, shoe):
    # --- POCZĄTEK RUNDY ---
    print(f"Twój portfel: {player.bankroll} PLN")

    # 1. Pobieranie zakładu (albo rezygnacja z gry - "n"/"nie" zamiast kwoty)
    while True:
        wpis = input(f"Ile obstawiasz? (min. {MIN_BET}, albo 'n' aby zakonczyc) ").strip().lower()
        if wpis in ("n", "nie"):
            return None
        try:
            bet = int(wpis)
        except ValueError:
            print("Podaj liczbe (kwote zakladu) albo 'n' aby zakonczyc.")
            continue
        if bet < MIN_BET:
            print(f"Zaklad musi wynosic co najmniej {MIN_BET}.")
            continue
        if bet * BET_RESERVE_MULTIPLIER > player.bankroll:
            max_bet = player.bankroll // BET_RESERVE_MULTIPLIER
            print(f"Za wysoki zaklad - portfel musi pokrywac rezerwe na ewentualne "
                  f"splity/double ({BET_RESERVE_MULTIPLIER}x zakladu). Maksymalny bezpieczny zaklad: {max_bet}.")
            continue
        break
    player.bankroll -= bet

    # 2. Resetowanie stołu przed nowym rozdaniem
    player.hands = []
    first_hand = Hand()
    first_hand.bet = bet
    player.add_hand(first_hand)
    dealer.hand = Hand()

    # 3. Rozdanie początkowe (po 2 karty naprzemiennie)
    for _ in range(2):
        player.hands[0].add_card(shoe.deal_one())
        dealer.hand.add_card(shoe.deal_one())

    # 4. Pokazanie stołu (krupier ukrywa jedną kartę)
    ui.show_board(player, dealer, reveal_dealer=False)

    # Sprawdzenie Black Jacka - tylko dla pierwszej, jeszcze niepodzielonej reki
    player_has_bj = (len(player.hands[0].cards) == 2 and player.hands[0].value == 21)
    dealer_has_bj = dealer.check_for_blackjack()

    if dealer_has_bj:
        ui.display_blackjack_dealer()
        ui.show_board(player, dealer, reveal_dealer=True)
        results = ["push"] if player_has_bj else ["lose"]
        apply_payouts(player, results)
        return results

    results = [None]
    if player_has_bj:
        ui.display_blackjack_player()
        results[0] = "blackjack"

    # 5. Petla akcji gracza (H/S/D/P) - indeksowa, bo split moze dopisac rece w trakcie
    i = 0
    while i < len(player.hands):
        if results[i] is not None:
            # reka juz rozstrzygnieta (np. naturalny Black Jack) - pomijamy
            i += 1
            continue

        hand = player.hands[i]

        while True:
            can_split = (hand.can_split() and len(player.hands) < MAX_HANDS
                         and player.bankroll >= hand.bet)
            can_double = (len(hand.cards) == 2 and player.bankroll >= hand.bet
                          and (DAS_ALLOWED or not hand.from_split))

            ui.display_choice(can_double=can_double, can_split=can_split)
            decision = input().upper()

            dozwolone = ["H", "S"]
            if can_double:
                dozwolone.append("D")
            if can_split:
                dozwolone.append("P")

            if decision not in dozwolone:
                ui.display_invalid_input()
                continue

            if decision == "H":
                hand.add_card(shoe.deal_one())
                ui.display_hit(hand.cards[-1])
                ui.show_board(player, dealer, reveal_dealer=False)
                if hand.value > 21:
                    ui.display_bust(i+1)
                    results[i] = "bust"
                    break
                elif hand.value == 21:
                    ui.display_21(i+1)
                    results[i] = "stand"
                    break
                # inaczej: petla pyta dalej o kolejna decyzje dla tej reki

            elif decision == "S":
                ui.display_stand(i+1)
                results[i] = "stand"
                break

            elif decision == "D":
                player.bankroll -= hand.bet
                hand.bet *= 2
                ui.display_double(i+1)
                hand.add_card(shoe.deal_one())
                ui.display_hit(hand.cards[-1])
                ui.show_board(player, dealer, reveal_dealer=False)
                if hand.value > 21:
                    ui.display_bust(i+1)
                    results[i] = "bust"
                else:
                    ui.display_stand(i+1)
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
                ui.display_split(i+1)

                # obie rece dostaja od razu po jednej nowej karcie
                hand.add_card(shoe.deal_one())
                ui.display_hit(hand.cards[-1])
                new_hand.add_card(shoe.deal_one())
                ui.display_hit(new_hand.cards[-1])

                player.hands.insert(i+1, new_hand)

                if aces_split:
                    # rozdzielone Asy - kazda reka dostaje tylko jedna karte i od razu stoi
                    if hand.value > 21:
                        ui.display_bust(i+1)
                        results[i] = "bust"
                    else:
                        ui.display_stand(i+1)
                        results[i] = "stand"

                    if new_hand.value > 21:
                        ui.display_bust(i+2)
                        results.insert(i+1, "bust")
                    else:
                        ui.display_stand(i+2)
                        results.insert(i+1, "stand")

                    ui.show_board(player, dealer, reveal_dealer=False)
                    break
                else:
                    results.insert(i+1, None)
                    ui.show_board(player, dealer, reveal_dealer=False)
                    if hand.value == 21:
                        ui.display_21(i+1)
                        results[i] = "stand"
                        break
                    # inaczej: petla pyta dalej dla tej samej (pierwszej) reki

        i += 1

    # 6. Ruch krupiera
    while dealer.hand.value < 17:
        dealer.hand.add_card(shoe.deal_one())

    ui.show_board(player, dealer, reveal_dealer=True)

    # 7. Rozstrzygniecie rak ktore stoja ("stand") - porownanie z krupierem
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

    apply_payouts(player, results)
    return results


while True:

    if player.bankroll < MIN_BANKROLL:
        print(f"\nKoniec gry - portfel ({player.bankroll} PLN) nie starcza juz na bezpieczna gre (min. {MIN_BANKROLL} PLN).")
        break

    if needs_reshuffle(shoe):
        ui.display_msg("Karta odcinajaca osiagnieta - tasujemy nowy but.")
        shoe = Deck(num_decks=NUM_DECKS)
        shoe.shuffle()

    results = play_round(player, dealer, shoe)
    if results is None:
        break

    print(results)
    print(f"Portfel: {player.bankroll:.0f} PLN")

print(f"\nKoniec gry. Koncowy portfel: {player.bankroll} PLN")
