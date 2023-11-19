import sys

from rt.agent import RandomAgent, SimpleAgent
from rt.state import GameState, Player


def get_move(agent, player, state):
    # TODO: Implement timing
    btime = 10000
    wtime = 10000
    binc = 10000
    winc = 10000

    agent.set_state(state)
    bestmove = agent.search(btime=btime, wtime=wtime, binc=binc, winc=winc)
    for move in state.possible_moves(player):
        if str(move) == bestmove:
            return move

    # Invalid move is being played
    return None


def main():
    player1 = SimpleAgent(Player.Black)
    player2 = RandomAgent(Player.White)

    winner = None
    state = GameState.start_position()
    while (next_player := state.next_player()) is not None:
        if next_player == Player.Black:
            bestmove = get_move(player1, next_player, state)
        elif next_player == Player.White:
            bestmove = get_move(player2, next_player, state)

        # The player made an illegal move so the opponent wins
        if bestmove is None:
            print("illegal move played by", next_player, file=sys.stderr)
            winner = next_player.opponent()
            break
        state = state.make_move(bestmove)
    winner = state.winner()
    print("winner", winner)
