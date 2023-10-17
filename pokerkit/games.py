""":mod:`pokerkit.games` implements various poker game definitions."""

from __future__ import annotations

from abc import ABC

from pokerkit.hands import (
    StandardHighHand
)
from pokerkit.state import BettingStructure, Opening, Automation, State, Street
from pokerkit.utilities import Deck, RankOrder, ValuesLike


class Poker(ABC):
    """The abstract base class for poker games."""

    max_down_card_count: int
    """The maximum number of down cards."""
    max_up_card_count: int
    """The maximum number of up cards."""
    max_board_card_count: int
    """The maximum number of board cards."""
    rank_orders: tuple[RankOrder, ...]
    """The rank orders."""
    button_status: bool
    """The button status."""


class TexasHoldem(Poker, ABC):
    """The abstract base class for Texas hold'em games."""

    max_down_card_count = 2
    max_up_card_count = 0
    max_board_card_count = 5
    rank_orders = (RankOrder.STANDARD,)
    button_status = True


class FixedLimitTexasHoldem(TexasHoldem):
    """The class for fixed-limit Texas hold'em games."""

    @classmethod
    def create_state(
            cls,
            automations: tuple[Automation, ...],
            ante_trimming_status: bool,
            antes: ValuesLike,
            blinds_or_straddles: ValuesLike,
            small_bet: int,
            big_bet: int,
            starting_stacks: ValuesLike,
            player_count: int,
    ) -> State:
        """Create a fixed-limit Texas hold'em game.

        Below is an example hand in fixed-limit Texas hold'em.

        >>> state = FixedLimitTexasHoldem.create_state(
        ...     (
        ...         Automation.ANTE_POSTING,
        ...         Automation.BET_COLLECTION,
        ...         Automation.BLIND_OR_STRADDLE_POSTING,
        ...         Automation.CARD_BURNING,
        ...         Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
        ...         Automation.HAND_KILLING,
        ...         Automation.CHIPS_PUSHING,
        ...         Automation.CHIPS_PULLING,
        ...     ),
        ...     True,
        ...     None,
        ...     (1, 2),
        ...     2,
        ...     4,
        ...     200,
        ...     2,
        ... )

        Below shows the pre-flop dealings and actions.

        >>> state.deal_hole('AcAs')
        HoleDealing(player_index=0, cards=(Ac, As), statuses=(False, False))
        >>> state.deal_hole('7h6h')
        HoleDealing(player_index=1, cards=(7h, 6h), statuses=(False, False))

        >>> state.complete_bet_or_raise_to()
        CompletionBettingOrRaisingTo(player_index=1, amount=4)
        >>> state.complete_bet_or_raise_to()
        CompletionBettingOrRaisingTo(player_index=0, amount=6)
        >>> state.fold()
        Folding(player_index=1)

        Below show the final stacks.

        >>> state.stacks
        [204, 196]

        :param antes: The antes.
        :param blinds_or_straddles: The blinds or straddles.
        :param small_bet: The small bet.
        :param big_bet: The big bet.
        :param starting_stacks: The starting stacks.
        :param player_count: The number of players.
        :return: The created state.
        """
        return State(
            automations,
            Deck.STANDARD,
            (StandardHighHand,),
            (
                Street(
                    False,
                    (False,) * 2,
                    0,
                    False,
                    Opening.POSITION,
                    small_bet,
                    4,
                ),
                Street(
                    True,
                    (),
                    3,
                    False,
                    Opening.POSITION,
                    small_bet,
                    4,
                ),
                Street(
                    True,
                    (),
                    1,
                    False,
                    Opening.POSITION,
                    big_bet,
                    4,
                ),
                Street(
                    True,
                    (),
                    1,
                    False,
                    Opening.POSITION,
                    big_bet,
                    4,
                ),
            ),
            BettingStructure.FIXED_LIMIT,
            ante_trimming_status,
            antes,
            blinds_or_straddles,
            0,
            starting_stacks,
            player_count,
        )


class NoLimitTexasHoldem(TexasHoldem):
    """The class for no-limit Texas hold'em games."""

    @classmethod
    def create_state(
            cls,
            automations: tuple[Automation, ...],
            ante_trimming_status: bool,
            antes: ValuesLike,
            blinds_or_straddles: ValuesLike,
            min_bet: int,
            starting_stacks: ValuesLike,
            player_count: int,
    ) -> State:
        """Create a no-limit Texas hold'em game.

        Below shows the first televised million dollar pot between
        Tom Dwan and Phil Ivey.

        Link: https://youtu.be/GnxFohpljqM

        >>> state = NoLimitTexasHoldem.create_state(
        ...     (
        ...         Automation.ANTE_POSTING,
        ...         Automation.BET_COLLECTION,
        ...         Automation.BLIND_OR_STRADDLE_POSTING,
        ...         Automation.CARD_BURNING,
        ...         Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
        ...         Automation.HAND_KILLING,
        ...         Automation.CHIPS_PUSHING,
        ...         Automation.CHIPS_PULLING,
        ...     ),
        ...     True,
        ...     500,
        ...     (1000, 2000),
        ...     2000,
        ...     (1125600, 2000000, 553500),
        ...     3,
        ... )

        Below shows the pre-flop dealings and actions.

        >>> state.deal_hole('Ac2d')  # Ivey
        HoleDealing(player_index=0, cards=(Ac, 2d), statuses=(False, False))
        >>> state.deal_hole('5h7s')  # Antonius*
        HoleDealing(player_index=1, cards=(5h, 7s), statuses=(False, False))
        >>> state.deal_hole('7h6h')  # Dwan
        HoleDealing(player_index=2, cards=(7h, 6h), statuses=(False, False))

        >>> state.complete_bet_or_raise_to(7000)  # Dwan
        CompletionBettingOrRaisingTo(player_index=2, amount=7000)
        >>> state.complete_bet_or_raise_to(23000)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=23000)
        >>> state.fold()  # Antonius
        Folding(player_index=1)
        >>> state.check_or_call()  # Dwan
        CheckingOrCalling(player_index=2, amount=16000)

        Below shows the flop dealing and actions.

        >>> state.deal_board('Jc3d5c')
        BoardDealing(cards=(Jc, 3d, 5c))

        >>> state.complete_bet_or_raise_to(35000)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=35000)
        >>> state.check_or_call()  # Dwan
        CheckingOrCalling(player_index=2, amount=35000)

        Below shows the turn dealing and actions.

        >>> state.deal_board('4h')
        BoardDealing(cards=(4h,))

        >>> state.complete_bet_or_raise_to(90000)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=90000)
        >>> state.complete_bet_or_raise_to(232600)  # Dwan
        CompletionBettingOrRaisingTo(player_index=2, amount=232600)
        >>> state.complete_bet_or_raise_to(1067100)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=1067100)
        >>> state.check_or_call()  # Dwan
        CheckingOrCalling(player_index=2, amount=262400)

        Below shows the river dealing.

        >>> state.deal_board('Jh')
        BoardDealing(cards=(Jh,))

        Below show the final stacks.

        >>> state.stacks
        [572100, 1997500, 1109500]

        :param antes: The antes.
        :param blinds_or_straddles: The blinds or straddles.
        :param min_bet: The min bet.
        :param starting_stacks: The starting stacks.
        :param player_count: The number of players.
        :return: The created state.
        """
        return State(
            automations,
            Deck.STANDARD,
            (StandardHighHand,),
            (
                Street(
                    False,
                    (False,) * 2,
                    0,
                    False,
                    Opening.POSITION,
                    min_bet,
                    None,
                ),
                Street(
                    True,
                    (),
                    3,
                    False,
                    Opening.POSITION,
                    min_bet,
                    None,
                ),
                Street(
                    True,
                    (),
                    1,
                    False,
                    Opening.POSITION,
                    min_bet,
                    None,
                ),
                Street(
                    True,
                    (),
                    1,
                    False,
                    Opening.POSITION,
                    min_bet,
                    None,
                ),
            ),
            BettingStructure.NO_LIMIT,
            ante_trimming_status,
            antes,
            blinds_or_straddles,
            0,
            starting_stacks,
            player_count,
        )
