def show_board(player, dealer, reveal_dealer = False):
    #Funkcja do rysowania stolu w konsoli
    print("\n" + "="*20 + " STÓŁ " + "="*20)
    if reveal_dealer:
        print(f"Krupier: {[str(card) for card in dealer.hand.cards]} (Punkty: {dealer.hand.value})")
    else:
        print(f"Krupier: [{dealer.hand.cards[0]}, <ZAKRYTA>] (Punkty: {dealer.hand.cards[0].value})")

    # Karty gracza
    for i, hand in enumerate(player.hands):
        print(f"{player.name} - Ręka {i+1}: {[str(card) for card in hand.cards]} (Punkty: {hand.get_display_value()})")
    print("="*46 + "\n")


# Komendy konsolowe

def display_msg(msg):
    #uniwersalna funkcja do wyswietlania wiadomosci
    print(f"\n {msg}")

def display_choice(can_double=False, can_split=False):
    opcje = "H/S"
    if can_double:
        opcje += "/D"
    if can_split:
        opcje += "/P"
    print(f"\n >> {opcje}?")

def display_hit(card):
    print(f"\n >> Dobrano kartę {card.rank} of {card.suit} o wartości {card.value}")

def display_stand(hand_number):
    print(f"\n Zostajesz, dla ręki nr {hand_number}")


def display_bust(hand_number):
    print(f"Ponad 21 punktów, ręka nr {hand_number} przegrała")

def display_blackjack_player():
    print(f"Black Jack!")

def display_21(hand_number):
    print(f"21 Punktów, koniec akcji, dla ręki nr {hand_number}")

def display_blackjack_dealer():
    print(f"\n Dealer ma Black Jacka")

def display_invalid_input():
    print("\n Niepoprawna komenda. Wpisz 'H', 'S', 'D' lub 'P' (zależnie od dostępnych opcji).")

def display_win(points):
    print(f"\n Wygrałeś {points} punktów")

def display_lose(points):
    print(f"\n Przegrałeś {points} punktów")

def display_points(points):
    print(f"\n Posiadasz {points} punktów")

def display_push():
    print(f"\n Remis (Push). Zatrzymujesz swoje żetony.")

def display_double(hand_number):
    print(f"\n >> Podwajasz zakład dla ręki nr {hand_number}!")

def display_split(hand_number):
    print(f"\n >> Rozdzielasz parę - ręka nr {hand_number} zostaje podzielona na dwie ręce!")


# --- Implementacje decide/decide_bet/notify pod silnik (blackjack/engine.py) ---
# To jest JEDYNE miejsce, gdzie konsolowa gra dotyka input()/print bezposrednio
# w kontekscie silnika - cala reszta (walidacja, retry przy zlym wpisie) siedzi
# tutaj, nie w engine.py.

def console_decide(hand, dealer_upcard, allowed_actions):
    can_double = "D" in allowed_actions
    can_split = "P" in allowed_actions
    while True:
        display_choice(can_double=can_double, can_split=can_split)
        decision = input().upper()
        if decision not in allowed_actions:
            display_invalid_input()
            continue
        return decision


def console_decide_bet(player, min_bet, max_bet, shoe):
    # Parametr shoe jest tu ignorowany - zostaje pod przyszle boty liczace karty,
    # zeby nie trzeba bylo pozniej zmieniac sygnatury tej funkcji.
    while True:
        wpis = input(f"Ile obstawiasz? (min. {min_bet}, albo 'n' aby zakonczyc) ").strip().lower()
        if wpis in ("n", "nie"):
            return None
        try:
            bet = int(wpis)
        except ValueError:
            print("Podaj liczbe (kwote zakladu) albo 'n' aby zakonczyc.")
            continue
        if bet < min_bet:
            print(f"Zaklad musi wynosic co najmniej {min_bet}.")
            continue
        if bet > max_bet:
            print(f"Za wysoki zaklad - portfel musi pokrywac rezerwe na ewentualne "
                  f"splity/double. Maksymalny bezpieczny zaklad: {max_bet}.")
            continue
        return bet


def console_notify(event, **data):
    if event == "board_update":
        show_board(data["player"], data["dealer"], reveal_dealer=data.get("reveal_dealer", False))
    elif event == "dealer_blackjack":
        display_blackjack_dealer()
    elif event == "player_blackjack":
        display_blackjack_player()
    elif event == "hit":
        display_hit(data["card"])
    elif event == "stand":
        display_stand(data["hand_number"])
    elif event == "bust":
        display_bust(data["hand_number"])
    elif event == "twenty_one":
        display_21(data["hand_number"])
    elif event == "double":
        display_double(data["hand_number"])
    elif event == "split":
        display_split(data["hand_number"])
    elif event == "win":
        display_win(data["amount"])
    elif event == "push":
        display_push()
    elif event == "lose":
        display_lose(data["amount"])
    elif event == "reshuffle":
        display_msg("Karta odcinajaca osiagnieta - tasujemy nowy but.")
    elif event == "round_end":
        print(data["results"])
        print(f"Portfel: {data['bankroll']:.0f} PLN")
    elif event == "game_end":
        print(f"\nKoniec gry. Koncowy portfel: {data['bankroll']} PLN")
    else:
        # nieznany event - przydatne przy dodawaniu nowych eventow w przyszlosci,
        # zeby cicho nie zgubic informacji zamiast rzucic wyjatek
        print(f"[nieznany event notify]: {event} {data}")
