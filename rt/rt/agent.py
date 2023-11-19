import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rt.state import Move


logger = logging.getLogger(__name__)


class Agent(ABC):
    @abstractmethod
    def __init__(self, player):
        raise NotImplementedError

    @abstractmethod
    def set_state(self, state):
        raise NotImplementedError

    @abstractmethod
    def search(self, btime, wtime, binc, winc):
        raise NotImplementedError


class RandomAgent(Agent):
    def __init__(self, player):
        self.player = player
        self.state = None

    def set_state(self, state):
        self.state = state

    def search(self, btime, wtime, binc, winc):
        moves = self.state.possible_moves(self.player)
        move = random.choice(moves)
        return str(move)
