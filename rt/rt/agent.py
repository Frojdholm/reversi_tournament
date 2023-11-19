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


# The current score_func has a maximum value of 64
INF_SCORE = 65


@dataclass
class DfsResult:
    """The result from a depth-first search."""
    moves: tuple[Move]
    """The moves performed in this branch of the DFS."""
    score: int
    """The score for this branch of DFS."""
    remaining: bool
    """True if the search could have gone deeper.

    When all branches return False the search is completed, otherwise more
    states can be found by searching deeper (increasing the maximum depth
    of the search).
    """


def score_func(state, player):
    """An estimation of the score of the current state for the player."""
    return state.count(player) - state.count(player.opponent())


def dfs_alpha_beta(state, alpha, beta, depth, player, max_depth, prev_best_variation):
    """Perform a depth-limited alpha-beta depth first search.

    Note:
        The search is recursive, keep the maximum recursion limit in mind. Due
        to the high branching factor this will likely not be an issue though.

    Args:
        state: The root state of the search.
        alpha: The current alpha value. The highest value the maximizing player
               is guaranteed.
        beta: The current beta value. The minimum value that the minimizing
              player can force.
        player: The player that is searching (maximizing player). Note that
                this is not the same as next player to take a turn, which is
                found from the state.
        max_depth: The maximum depth to search.
        prev_best_variation: The sequence of moves that gave the highest score
                             in a previous (shallower) search.

    Returns:
        A DfsResult object containing an estimate of the score and a series of
        moves, the principal variation. The moves are the moves that would be
        made by the players to reach the state that was used for estimating the
        score.
    """
    if depth >= max_depth:
        return DfsResult(
            moves=tuple(),
            score=score_func(state, player),
            remaining=True  # The search was stopped by max_depth so there are most often more nodes.
        )

    next_player = state.next_player()
    if next_player is None:
        return DfsResult(
            moves=tuple(),
            score=score_func(state, player),
            remaining=False  # The game has ended so no more nodes.
        )

    maximizing_player = next_player == player
    moves = state.possible_moves(next_player)
    # If there is a best move from the previous iteration and it is part of
    # the current possible moves make sure to test it first.
    if depth < len(prev_best_variation):
        previous_best_move = prev_best_variation[depth]
        moves.sort(key=lambda e: e != previous_best_move)

    best_moves = tuple()
    remaining = False
    if maximizing_player:
        score = -INF_SCORE
        for m in moves:
            res = dfs_alpha_beta(
                state=state.make_move(m),
                alpha=alpha,
                beta=beta,
                depth=depth + 1,
                player=player,
                max_depth=max_depth,
                prev_best_variation=prev_best_variation
            )
            remaining |= res.remaining
            if res.score > score:
                best_moves = (m,) + res.moves
                score = res.score
            alpha = max(alpha, score)

            # If the score is higher than the lowest the minimizing player can
            # ensure stop the search since the minimizing player will never
            # allow this move.
            if res.score >= beta:
                break
    else:
        score = INF_SCORE
        for m in moves:
            res = dfs_alpha_beta(
                state=state.make_move(m),
                alpha=alpha,
                beta=beta,
                depth=depth + 1,
                player=player,
                max_depth=max_depth,
                prev_best_variation=prev_best_variation
            )
            remaining |= res.remaining
            if res.score < score:
                best_moves = (m,) + res.moves
                score = res.score
            beta = min(beta, score)

            # If the score is lower than the highest the maximizing player is
            # guaranteed stop the search since the maximizing player will never
            # play this move.
            if res.score <= alpha:
                break

    assert best_moves is not None
    return DfsResult(
        moves=best_moves,
        score=score,
        remaining=remaining
    )


def iterative_deepening(state, player, max_depth=3):
    """Perform an iterative deepening search of the game tree.

    Iterative deepening perfoms a breadth-first search (BFS) in depth-first
    search (DFS) order. This requires less memory than a BFS. Additionally,
    the previous iteration is used to guide the search. This helps the
    alpha-beta pruning algorithm prune more branches, leading to faster
    searches.

    Iterative deepening depth-first search (IDDFS) also has the advantage that
    it simple to abort a search if it is taking too long. Since there will be
    a result from the previous iteration the current DFS can be cancelled and
    the previous result can be used instead.

    Args:
        state: The root state of the search.
        player: The searching (maximizing) player.
        max_depth: The maximum depth to search.

    Return:
        A DfsResult object containing the estimated score and principal variation.
    """
    prev_best_variation = tuple()
    for current_depth in range(1, max_depth + 1):
        res = dfs_alpha_beta(
            state=state,
            alpha=-INF_SCORE,
            beta=INF_SCORE,
            depth=0,
            player=player,
            max_depth=current_depth,
            prev_best_variation=prev_best_variation
        )
        if not res.remaining or current_depth == max_depth:
            return res
        prev_best_variation = res.moves


class SimpleAgent(Agent):
    def __init__(self, player):
        self.player = player
        self.state = None

    def set_state(self, state):
        self.state = state

    def search(self, btime, wtime, binc, winc):
        try:
            res = iterative_deepening(self.state, self.player)
        except Exception as err:
            logger.error("exception encountered", exc_info=err)
            raise err
        logger.info("best move %s, score %d", res.moves[0], res.score)
        # The first move of the principal variation should be played.
        return str(res.moves[0])
