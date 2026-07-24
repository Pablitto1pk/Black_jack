from blackjack.cards import Deck
from blackjack.participants import Player, Dealer
from blackjack import engine
from blackjack import console_ui as ui

player = Player(name="Gracz", bankroll=1000)
dealer = Dealer()
shoe = Deck(num_decks=engine.NUM_DECKS)
shoe.shuffle()

while True:
    if engine.needs_reshuffle(shoe):
        ui.console_notify("reshuffle")
        shoe = Deck(num_decks=engine.NUM_DECKS)
        shoe.shuffle()

    max_bet = player.bankroll // engine.BET_RESERVE_MULTIPLIER
    bet = ui.console_decide_bet(player, engine.MIN_BET, max_bet, shoe)
    if bet is None:
        break

    results = engine.play_round(player, dealer, shoe, bet, ui.console_decide, ui.console_notify)
    ui.console_notify("round_end", results=results, bankroll=player.bankroll)

ui.console_notify("game_end", bankroll=player.bankroll)
