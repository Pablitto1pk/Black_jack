def show_board(player, dealer, reveal_dealer = False):
    #Funkcja do rysowania stolu w konsoli
    print("\n" + "="*20 + " STÓŁ " + "="*20)
    if reveal_dealer:
        print(f"Krupier: {[str(card) for card in dealer.hand.cards]} (Punkty: {dealer.hand.value})")
    else:
        print(f"Krupier: [{dealer.hand.cards[0]}, <ZAKRYTA>]")

    # Karty gracza
    for i, hand in enumerate(player.hands):
        print(f"{player.name} - Ręka {i+1}: {[str(card) for card in hand.cards]} (Punkty: {hand.get_display_value()})")
    print("="*46 + "\n")


# Komendy konsolowe

def display_msg(msg):
    #uniwersalna funkcja do wyswietlania wiadomosci
    print(f"\n {msg}")

def display_hit(card):
    print(f"\n >> Dobrano kartę {card.rank} of {card.suit} o wartości {card.value}")

def display_stand(hand_number):
    print(f"\n Zostajesz, dla ręki nr {hand_number}")

def display_blackjack_player():
    print(f"Black Jack!")

def display_21(hand_number):
    print(f"21 Punktów, koniec akcji, dla ręki nr {hand_number}")

def display_blackjack_dealer():
    print(f"\n Dealer ma Black Jacka")

def display_invalid_input():
    print("\n Niepoprawna komenda. Wpisz 'H' lub 'S'.")

def display_win(points):
    print(f"\n Wygrałeś {points} punktów")

def display_lose(points):
    print(f"\n Przegrałeś {points} punktów")

def display_points(points):
    print(f"\n Posiadasz {points} punktów")
    
def display_push():
    print(f"\n Remis (Push). Zatrzymujesz swoje żetony.")