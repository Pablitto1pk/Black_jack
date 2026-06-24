from models import Card
from player import Hand

print("--- TESTOWANIE LOGIKI ASÓW ---")

# Tworzymy pustą rękę
test_hand = Hand()

# Dajemy graczowi Króla (10) i Asa (11)
test_hand.add_card(Card('Spades', 'King', 10))
test_hand.add_card(Card('Hearts', 'Ace', 11))

print(f"Karty w ręce: 10 + 11. Suma: {test_hand.value}")

# Dodajemy drugiego Asa (11)
print("\nDobieramy drugiego Asa...")
test_hand.add_card(Card('Clubs', 'Ace', 11))
print(f"Suma przed korektą: {test_hand.value}") # Tu wyjdzie 32 punkty

# Odpalamy naszą funkcję naprawczą
test_hand.adjust_for_ace()
print(f"Suma po korekcie: {test_hand.value}") # Tu powinno zbić do 12 (10 + 1 + 1)