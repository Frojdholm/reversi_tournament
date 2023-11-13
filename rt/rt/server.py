import argparse
import subprocess
import shlex
import shutil
import os
import logging

from rt.state import Player, GameState


logger = logging.getLogger(__name__)


def popen(cmd):
    return subprocess.Popen(
        shlex.split(cmd),
        bufsize=1,  # line buffered
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )


class PlayerError(Exception):
    pass


class PlayerProcess:
    def __init__(self, tag, cmd):
        self.tag = tag
        self.cmd = shutil.which(cmd)
        self.name = None
        self.author = None
        self.process = None

    def __enter__(self):
        self.process = popen(self.cmd)
        return self

    def __exit__(self, *args):
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.terminate()
        return False

    def __str__(self):
        return f"{self.name} by {self.author}"

    def _write(self, msg):
        msg = msg.strip()
        logger.debug("send to %s: %s", self.tag, msg)
        self.process.stdin.write(msg + "\n")

    def _read(self):
        msg = self.process.stdout.readline().strip()
        logger.debug("recv from %s: %s", self.tag, msg)
        return msg

    def expect_enter(self):
        if self.process is None:
            raise PlayerError

    def start(self):
        self.expect_enter()
        self._write("reversi_v1")
        while True:
            line = self._read()
            if line == "reversi_v1_ok":
                break
            id_, command, *value = line.split()
            assert id_ == "id"
            if command == "name":
                self.name = " ".join(value)
            elif command == "author":
                self.author = " ".join(value)
            else:
                raise PlayerError

    def newgame(self, player):
        self.expect_enter()
        self._write(f"newgame {player.value}")

    def isready(self):
        self.expect_enter()
        self._write("isready")
        msg = self._read()
        if msg != "readyok":
            raise PlayerError

    def send_position(self, position):
        self.expect_enter()
        self._write(f"position {position}")

    def send_go(self, btime, wtime, binc, winc):
        self.expect_enter()
        self._write(f"go btime={btime} wtime={wtime} binc={binc} winc={winc}")
        response = self._read()
        command, move = response.split()
        if command != "bestmove":
            raise PlayerError
        return move


def get_move(player_proc, player, moves, state):
    # TODO: Implement timing
    btime = 10000
    wtime = 10000
    binc = 10000
    winc = 10000

    player_proc.send_position(" ".join(moves))
    player_proc.isready()
    bestmove = player_proc.send_go(btime=btime, wtime=wtime, binc=binc, winc=winc)
    for move in state.possible_moves(player):
        if str(move) == bestmove:
            return move

    # Invalid move is being played
    return None


def play_game(pb, pw):
    pb.newgame(Player.Black)
    pw.newgame(Player.White)
    pb.isready()
    pw.isready()

    moves = ["startpos"]
    state = GameState.start_position()
    while (next_player := state.next_player()) is not None:
        if next_player == Player.Black:
            bestmove = get_move(pb, next_player, moves, state)
        elif next_player == Player.White:
            bestmove = get_move(pw, next_player, moves, state)

        # The player made an illegal move so the opponent wins
        if bestmove is None:
            logger.info("illegal move by %s", next_player)
            return next_player.opponent()

        moves.append(str(bestmove))
        state = state.make_move(bestmove)
    # When the game is over the winner of the last state wins the game
    return state.winner()


def run_server(player1, player2):
    iterations = 100
    wins_p1 = 0
    wins_p2 = 0
    draws = 0
    with PlayerProcess("p1", player1) as p1, PlayerProcess("p2", player2) as p2:
        p1.start()
        p2.start()
        print(p1, "vs", p2)
        for i in range(iterations // 2):
            winner = play_game(p1, p2)
            logger.info("game %d, winner %s", i, winner)
            if winner == Player.Black:
                wins_p1 += 1
            elif winner == Player.White:
                wins_p2 += 1
            else:
                draws += 1
        for i in range(iterations // 2, iterations):
            logger.info("game %d, winner %s", i, winner)
            winner = play_game(p2, p1)
            if winner == Player.Black:
                wins_p2 += 1
            elif winner == Player.White:
                wins_p1 += 1
            else:
                draws += 1
    print("P1:", wins_p1, "P2:", wins_p2, "Draw:", draws)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("player1")
    parser.add_argument("player2")

    args = parser.parse_args()

    logging.basicConfig(filename=f"server{os.getpid()}.log")
    run_server(args.player1, args.player2)
