from pokerkit import Poker, NoLimitTexasHoldem, Automation

state = NoLimitTexasHoldem.create_state(
     (
         Automation.ANTE_POSTING,
         Automation.BET_COLLECTION,
         Automation.BLIND_OR_STRADDLE_POSTING,
         Automation.CARD_BURNING,
         Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
         Automation.HAND_KILLING,
         Automation.CHIPS_PUSHING,
         Automation.CHIPS_PULLING,
     ),
     True,
     3000,
     {-1: 3000},
     3000,
     (495000, 232000, 362000, 403000, 301000, 204000),
     6,
)
# Below shows the pre-flop dealings and actions.
state.deal_hole('Th8h')  # Badziakouski
state.deal_hole('QsJd')  # Zhong
state.deal_hole('QhQd')  # Xuan
state.deal_hole('8d7c')  # Jun
state.deal_hole('KhKs')  # Phua
state.deal_hole('8c7h')  # Koon
state.check_or_call()  # Badziakouski
state.check_or_call()  # Zhong
state.complete_bet_or_raise_to(35000)  # Xuan
state.fold()  # Jun
state.complete_bet_or_raise_to(298000)  # Phua

state.fold()  # Koon
state.fold()  # Badziakouski
state.fold()  # Zhong
state.check_or_call()  # Xuan
state.deal_board('9h6cKc')
state.deal_board('Jh')
state.deal_board('Ts')
state.stacks