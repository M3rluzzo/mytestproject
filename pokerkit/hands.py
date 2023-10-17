""":mod:`pokerkit.hands` implements classes related to poker hands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
from functools import total_ordering
from itertools import chain, combinations
from typing import Any

from pokerkit.lookups import (
    Entry,
    Lookup,
    RegularLookup,
    StandardLookup,
)
from pokerkit.utilities import Card, CardsLike

@total_ordering
class Hand(Hashable, ABC):
    """The abstract base class for poker hands.

    Stronger hands are considered greater than weaker hands.

    >>> h0 = ShortDeckHoldemHand('6s7s8s9sTs')
    >>> h1 = ShortDeckHoldemHand('7c8c9cTcJc')
    >>> h2 = ShortDeckHoldemHand('2c2d2h2s3h')
    Traceback (most recent call last):
        ...
    ValueError: invalid hand '2c2d2h2s3h'
    >>> h0
    6s7s8s9sTs
    >>> h1
    7c8c9cTcJc
    >>> print(h0)
    Straight flush (6s7s8s9sTs)
    >>> h0 < h1
    True

    It does not make sense to compare hands of different types.

    >>> h = BadugiHand('6d7s8h9c')
    >>> h < 500
    Traceback (most recent call last):
        ...
    TypeError: '<' not supported between instances of 'BadugiHand' and 'int'

    The hands are hashable.

    >>> h0 = ShortDeckHoldemHand('6s7s8s9sTs')
    >>> h1 = ShortDeckHoldemHand('7c8c9cTcJc')
    >>> hands = {h0, h1}
    """

    lookup: Lookup
    """The hand lookup."""
    low: bool
    """The low status."""

    @classmethod
    @abstractmethod
    def from_game(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = None,
    ) -> Hand:
        """Create a poker hand from a game setting.

        In a game setting, a player uses private cards from their hole
        and the public cards from the board to make their hand.

        :param hole_cards: The hole cards.
        :param board_cards: The optional board cards.
        :return: The strongest hand from possible card combinations.
        """

    def __init__(self, cards: CardsLike) -> None:
        self.__cards = Card.clean(cards)

        if not self.lookup.has_entry(self.cards):
            raise ValueError(f'invalid hand \'{repr(self)}\'')

    def __eq__(self, other: Any) -> bool:
        if type(self) != type(other):
            return NotImplemented

        assert isinstance(other, Hand)

        return self.entry == other.entry

    def __hash__(self) -> int:
        return hash(self.entry)

    def __lt__(self, other: Hand) -> bool:
        if type(self) != type(other):
            return NotImplemented

        assert isinstance(other, Hand)

        if self.low:
            return self.entry > other.entry
        else:
            return self.entry < other.entry

    def __repr__(self) -> str:
        return ''.join(map(repr, self.cards))

    def __str__(self) -> str:
        return f'{self.entry.label.value} ({repr(self)})'

    @property
    def cards(self) -> tuple[Card, ...]:
        """Return the cards that form this hand.

        >>> hole = 'AsAc'
        >>> board = 'Kh3sAdAh'
        >>> hand = StandardHighHand.from_game(hole, board)
        >>> hand.cards
        (As, Ac, Kh, Ad, Ah)

        :return: The cards that form this hand.
        """
        return self.__cards

    @property
    def entry(self) -> Entry:
        """Return the hand entry.

        >>> hole = 'AsAc'
        >>> board = 'Kh3sAdAh'
        >>> hand = StandardHighHand.from_game(hole, board)
        >>> hand.entry.label
        <Label.FOUR_OF_A_KIND: 'Four of a kind'>

        :return: The hand entry.
        """
        return self.lookup.get_entry(self.cards)

class CombinationHand(Hand, ABC):
    """The abstract base class for combination hands."""

    card_count: int
    """The number of cards."""

    @classmethod
    def from_game(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = None,
    ) -> Hand:
        """Create a poker hand from a game setting.

        In a game setting, a player uses private cards from their hole
        and the public cards from the board to make their hand.

        >>> h0 = StandardHighHand.from_game('AcAdAhAsKc')
        >>> h1 = StandardHighHand('AcAdAhAsKc')
        >>> h0 == h1
        True
        >>> h0 = StandardHighHand.from_game('Ac9c', 'AhKhQhJhTh')
        >>> h1 = StandardHighHand('AhKhQhJhTh')
        >>> h0 == h1
        True

        >>> h0 = StandardLowHand.from_game('AcAdAhAsKc', '')
        >>> h1 = StandardLowHand('AcAdAhAsKc')
        >>> h0 == h1
        True
        >>> h0 = StandardLowHand.from_game('Ac9c', 'AhKhQhJhTh')
        >>> h1 = StandardLowHand('AcQhJhTh9c')
        >>> h0 == h1
        True

        >>> h0 = ShortDeckHoldemHand.from_game('AcKs', 'AhAsKcJsTs')
        >>> h1 = ShortDeckHoldemHand('AcAhAsKcKs')
        >>> h0 == h1
        True
        >>> h0 = ShortDeckHoldemHand.from_game('AcAd', '6s7cKcKd')
        >>> h1 = ShortDeckHoldemHand('AcAdKcKd7c')
        >>> h0 == h1
        True

        >>> h0 = EightOrBetterLowHand.from_game('As2s', '2c3c4c5c6c')
        >>> h1 = EightOrBetterLowHand('Ad2d3d4d5d')
        >>> h0 == h1
        True

        >>> h0 = RegularLowHand.from_game('AcAd', 'AhAsKcQdQh')
        >>> h1 = RegularLowHand('AcAsQdQhKc')
        >>> h0 == h1
        True
        >>> h0 = RegularLowHand.from_game('AcAd', 'AhAsKcQd')
        >>> h1 = RegularLowHand('AdAhAsKcQd')
        >>> h0 == h1
        True

        :param hole_cards: The hole cards.
        :param board_cards: The optional board cards.
        :return: The strongest hand from possible card combinations.
        """
        max_hand = None

        for combination in combinations(
                chain(Card.clean(hole_cards), Card.clean(board_cards)),
                cls.card_count,
        ):
            try:
                hand = cls(combination)
            except ValueError:
                pass
            else:
                if max_hand is None or hand > max_hand:
                    max_hand = hand

        if max_hand is None:
            raise ValueError('no valid hand')

        return max_hand

class StandardHand(CombinationHand, ABC):
    """The abstract base class for standard hands."""

    lookup = StandardLookup()
    card_count = 5

class StandardHighHand(StandardHand):
    """The class for standard high hands.

    >>> h0 = StandardHighHand('7c5d4h3s2c')
    >>> h1 = StandardHighHand('7c6d4h3s2c')
    >>> h2 = StandardHighHand('8c7d6h4s2c')
    >>> h3 = StandardHighHand('AcAsAd2s4s')
    >>> h4 = StandardHighHand('TsJsQsKsAs')
    >>> h0 < h1 < h2 < h3 < h4
    True

    >>> h = StandardHighHand('4c5dThJsAcKh2h')
    Traceback (most recent call last):
        ...
    ValueError: invalid hand '4c5dThJsAcKh2h'
    >>> h = StandardHighHand('Ac2c3c4c')
    Traceback (most recent call last):
        ...
    ValueError: invalid hand 'Ac2c3c4c'
    >>> h = StandardHighHand(())
    Traceback (most recent call last):
        ...
    ValueError: invalid hand ''
    """

    low = False

class StandardLowHand(StandardHand):
    """The class for standard low hands.

    >>> h0 = StandardLowHand('TsJsQsKsAs')
    >>> h1 = StandardLowHand('AcAsAd2s4s')
    >>> h2 = StandardLowHand('8c7d6h4s2c')
    >>> h3 = StandardLowHand('7c6d4h3s2c')
    >>> h4 = StandardLowHand('7c5d4h3s2c')
    >>> h0 < h1 < h2 < h3 < h4
    True

    >>> h = StandardLowHand('4c5dThJsAcKh2h')
    Traceback (most recent call last):
        ...
    ValueError: invalid hand '4c5dThJsAcKh2h'
    >>> h = StandardLowHand('Ac2c3c4c')
    Traceback (most recent call last):
        ...
    ValueError: invalid hand 'Ac2c3c4c'
    >>> h = StandardLowHand(())
    Traceback (most recent call last):
        ...
    ValueError: invalid hand ''
    """

    low = True

class BoardCombinationHand(CombinationHand, ABC):
    """The abstract base class for board-combination hands."""

    board_card_count: int
    """The number of board cards."""

    @classmethod
    def from_game(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = None,
    ) -> Hand:
        """Create a poker hand from a game setting.

        In a game setting, a player uses private cards from their hole
        and the public cards from the board to make their hand.

        >>> h0 = GreekHoldemHand.from_game('Ac2d', 'QdJdTh2sKs')
        >>> h1 = GreekHoldemHand('2s2dAcKsQd')
        >>> h0 == h1
        True
        >>> h0 = GreekHoldemHand.from_game('AsKs', 'QdJdTh2s2d')
        >>> h1 = GreekHoldemHand('AsKsQdJdTh')
        >>> h0 == h1
        True
        >>> h0 = GreekHoldemHand.from_game('Ac9c', 'AhKhQhJhTh')
        >>> h1 = GreekHoldemHand('AcAhKhQh9c')
        >>> h0 == h1
        True

        :param hole_cards: The hole cards.
        :param board_cards: The optional board cards.
        :return: The strongest hand from possible card combinations.
        """
        hole_cards = Card.clean(hole_cards)
        board_cards = Card.clean(board_cards)
        max_hand = None

        for combination in combinations(board_cards, cls.board_card_count):
            try:
                hand = super().from_game(hole_cards, combination)
            except ValueError:
                pass
            else:
                if max_hand is None or hand > max_hand:
                    max_hand = hand

        if max_hand is None:
            raise ValueError('no valid hand')

        return max_hand

class HoleBoardCombinationHand(BoardCombinationHand, ABC):
    """The abstract base class for hole-board-combination hands."""

    hole_card_count: int
    """The number of hole cards."""

    @classmethod
    def from_game(
            cls,
            hole_cards: CardsLike,
            board_cards: CardsLike = None,
    ) -> Hand:
        """Create a poker hand from a game setting.

        In a game setting, a player uses private cards from their hole
        and the public cards from the board to make their hand.

        >>> h0 = OmahaHoldemHand.from_game('6c7c8c9c', '8s9sTc')
        >>> h1 = OmahaHoldemHand('6c7c8s9sTc')
        >>> h0 == h1
        True
        >>> h0 = OmahaHoldemHand.from_game('6c7c8s9s', '8c9cTc')
        >>> h1 = OmahaHoldemHand('6c7c8c9cTc')
        >>> h0 == h1
        True
        >>> h0 = OmahaHoldemHand.from_game('6c7c8c9c', '8s9sTc9hKs')
        >>> h1 = OmahaHoldemHand('8c8s9c9s9h')
        >>> h0 == h1
        True
        >>> h0 = OmahaHoldemHand.from_game('6c7c8sAh', 'As9cTc2sKs')
        >>> h1 = OmahaHoldemHand('AhAsKsTc8s')
        >>> h0 == h1
        True

        >>> h0 = OmahaEightOrBetterLowHand.from_game('As2s3s4s', '2c3c4c5c6c')
        >>> h1 = OmahaEightOrBetterLowHand('Ad2d3d4d5d')
        >>> h0 == h1
        True
        >>> h0 = OmahaEightOrBetterLowHand.from_game('As6s7s8s', '2c3c4c5c6c')
        >>> h1 = OmahaEightOrBetterLowHand('Ad2d3d4d6d')
        >>> h0 == h1
        True

        :param hole_cards: The hole cards.
        :param board_cards: The optional board cards.
        :return: The strongest hand from possible card combinations.
        """
        hole_cards = Card.clean(hole_cards)
        board_cards = Card.clean(board_cards)
        max_hand = None

        for combination in combinations(hole_cards, cls.hole_card_count):
            try:
                hand = super().from_game(combination, board_cards)
            except ValueError:
                pass
            else:
                if max_hand is None or hand > max_hand:
                    max_hand = hand

        if max_hand is None:
            raise ValueError('no valid hand')

        return max_hand