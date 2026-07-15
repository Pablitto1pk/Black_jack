from blackjack.cards import Deck
from blackjack.participants import Player, Dealer
from blackjack.hand import Hand
from blackjack import console_ui as ui


#Inicjalizacja
player = Player(name="Gracz", bankroll=1000)
dealer = Dealer()
shoe = Deck(num_decks=5)
shoe.shuffle()

MIN_BET = 50
MIN_BANKROLL = MIN_BET * 8  # rezerwa na najgorszy przypadek: 4 rece (3 splity), kazda podwojona

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

    # 1. Pobieranie zakładu
    while True:
        bet = int(input(f"Ile obstawiasz? (min. {MIN_BET}) "))
        if bet < MIN_BET:
            print(f"Zaklad musi wynosic co najmniej {MIN_BET}.")
            continue
        if bet > player.bankroll:
            print("Nie stac Cie na taki zaklad.")
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

    # Sprawdzenie Black Jackow graczy
    player_hands_bj = []
    for i in range(len(player.hands)):
        player_hands_bj.append((len(player.hands[i].cards) == 2 and player.hands[i].value == 21))

    dealer_has_bj = dealer.check_for_blackjack()
    results = []
    if dealer_has_bj:
        ui.display_blackjack_dealer()
        ui.show_board(player, dealer, reveal_dealer=True)
        for i in range(len(player_hands_bj)):
            if player_hands_bj[i]:
                results.append("push")
            else:
                results.append("lose")

        apply_payouts(player, results)
        return results

    for i in range(len(player_hands_bj)):
        if player_hands_bj[i]:
            results.append("blackjack")
        else:
            while True:
                ui.display_choice()
                decision = input().upper()
                if decision not in ("H", "S"):
                    ui.display_invalid_input()
                    continue
                if decision == "H":
                    player.hands[i].add_card(shoe.deal_one())
                    ui.display_hit(player.hands[i].cards[-1])
                    ui.show_board(player, dealer, reveal_dealer=False)
                    if player.hands[i].value > 21:
                        ui.display_bust(i+1)
                        results.append("bust")
                        break
                    elif player.hands[i].value == 21:
                        ui.display_21(i+1)
                        results.append("stand")
                        break
                else:
                    ui.display_stand(i+1)
                    results.append("stand")
                    break

    while dealer.hand.value < 17:
        dealer.hand.add_card(shoe.deal_one())

    ui.show_board(player, dealer, reveal_dealer=True)

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

    apply_payouts(player, results)
    return results


while True:

    if player.bankroll < MIN_BANKROLL:
        print(f"\nKoniec gry - portfel ({player.bankroll} PLN) nie starcza juz na bezpieczna gre (min. {MIN_BANKROLL} PLN).")
        break

    results = play_round(player, dealer, shoe)
    print(results)
    print(f"Portfel: {player.bankroll:.0f} PLN")

    again = input("Zagrac jeszcze raz? [T/n] ").strip().lower()
    if again in ("n", "nie"):
        break

print(f"\nKoniec gry. Koncowy portfel: {player.bankroll} PLN")