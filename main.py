from blackjack.cards import Deck
from blackjack.participants import Player, Dealer
from blackjack.hand import Hand
from blackjack import console_ui as ui


#Inicjalizacja
player = Player(name="Gracz", bankroll=1000)
dealer = Dealer()
shoe = Deck(num_decks=5)
shoe.shuffle()

def play_round(player, dealer, shoe):
    # --- POCZĄTEK RUNDY ---
    print(f"Twój portfel: {player.bankroll} PLN")

    # 1. Pobieranie zakładu
    bet = int(input("Ile obstawiasz? "))
    player.bankroll -= bet

    # 2. Resetowanie stołu przed nowym rozdaniem
    player.hands = []            # Czyścimy stare ręce gracza
    first_hand = Hand()          # Tworzymy nową pustą rękę...
    player.add_hand(first_hand)  # ...i przypisujemy ją graczowi
    dealer.hand = Hand()         # Czyścimy rękę krupiera

    # 3. Rozdanie początkowe (po 2 karty naprzemiennie)
    for _ in range(2):
        player.hands[0].add_card(shoe.deal_one())
        dealer.hand.add_card(shoe.deal_one())

    # 4. Pokazanie stołu (krupier ukrywa jedną kartę)
    ui.show_board(player, dealer, reveal_dealer=False)

    # Sprawdzenie Black Jackow graczy
    player_hands_bj = []
    for i in range(len(player.hands)) :
        player_hands_bj.append((len(player.hands[i].cards) == 2 and player.hands[i].value == 21)) 

    dealer_has_bj = dealer.check_for_blackjack()
    results = []
    if dealer_has_bj:
        for i in range(len(player_hands_bj)):
            if player_hands_bj[i]:
                results.append("push")
            else:
                results.append("lose")

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

    return results


results = play_round(player, dealer, shoe)
print(results)  # tymczasowo, zeby sprawdzic ze dziala - pozniej podepniemy ui