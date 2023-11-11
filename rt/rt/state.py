from dataclasses import dataclass
from enum import Enum


BOARD_SIZE = 8


def is_occupied(row, col, board):
    """Checks if the position is occupied on the board.

    Args:
        - ind: The position on the board in index format.
        - board: The board to check.

    Returns:
        True if the position is occupied, False otherwise.
    """
    return rc2board(row, col) & board != 0


def is_inbounds(row, col):
    """Checks if the position is on the board.

    Args:
        - ind: The position in index format.

    Returns:
        True if the position is a valid position on the board, False otherwise.
    """
    ind = rc2ind(row, col)
    return ind >= 0 and ind <= BOARD_SIZE * BOARD_SIZE


def rc2ind(row, col):
    """Convert a position from RC (row, col) format to index format.

    Args:
        - row: The row index (0-based).
        - col: The column index (0-based).

    Returns:
        The position in index format.
    """
    return row * BOARD_SIZE + col


def rc2board(row, col):
    """Convert a position from RC (row, col) format to board format.

    Board format is an integer where the bits represent occupied places.

    Args:
        - row: The row index (0-based).
        - col: The column index (0-based).

    Returns:
        The position in board format.
    """
    return ind2board(rc2ind(row, col))


def ind2board(ind):
    """Convert a position from index format to board format.

    Board format is an integer where the bits represent occupied places.

    Args:
        - ind: The position in index format.

    Returns:
        The position in board format.
    """
    return 1 << ind


def iter_board():
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            yield row, col


def find_flips_along_direction(row, col, dr, dc, my_board, opponent_board):
    """Perform a search for flips in the direction given by (dr,dc).

    If we find only opponent tokens and then one of our tokens the
    search was successful. If we find an empty position or go out of
    bounds the search was unsuccessful.
    """
    pattern = 0
    # Scan along the line given by pos and (dr, dc). Worst case we are at the
    # edges. Scanning until BOARD_SIZE - 1 will then cause us to end up at the
    # other edge.
    for i in range(1, BOARD_SIZE):
        r = row + dr * i
        c = col + dc * i

        if not is_inbounds(r, c):
            return 0
        elif is_occupied(r, c, my_board):
            return pattern
        elif is_occupied(r, c, opponent_board):
            pattern |= rc2board(r, c)
        else:
            return 0
    return 0


def find_flips(row, col, my_board, opponent_board):
    return (
        find_flips_along_direction(row, col, 0, 1, my_board, opponent_board)
        | find_flips_along_direction(row, col, 0, -1, my_board, opponent_board)
        | find_flips_along_direction(row, col, 1, 0, my_board, opponent_board)
        | find_flips_along_direction(row, col, -1, 0, my_board, opponent_board)
        | find_flips_along_direction(row, col, -1, -1, my_board, opponent_board)
        | find_flips_along_direction(row, col, 1, -1, my_board, opponent_board)
        | find_flips_along_direction(row, col, 1, 1, my_board, opponent_board)
    )


def find_moves(my_board, opponent_board):
    moves = []
    for row, col in iter_board():
        # A move is only valid if the position is unoccupied
        if not is_occupied(row, col, my_board) and not is_occupied(row, col, opponent_board):
            flip_board = find_flips(row, col, my_board, opponent_board)
            # A move is only valid if it flips at least one token
            if flip_board != 0:
                moves.append(Move(row, col, flip_board))
    return moves


def single_board_to_string(board):
    res = [" abcdefgh"]
    for row in range(BOARD_SIZE):
        r = [str(row + 1)]
        for col in range(BOARD_SIZE):
            if is_occupied(row, col, board):
                r.append("X")
            else:
                r.append(".")
        res.append("".join(r))
    return "\n".join(res)


def col_to_string(col):
    return chr(col + ord("a"))


@dataclass
class Move:
    row: int
    col: int
    flip_board: int

    def __str__(self):
        return f"""{col_to_string(self.col)}{self.row + 1}
{single_board_to_string(self.flip_board)}
"""


class Player(Enum):
    Black = "B"
    White = "W"

    def opponent(self):
        if self == Player.Black:
            return Player.White
        else:
            return Player.Black


class GameState:
    """The state of the game at a certain point in time."""

    def __init__(self, black_board=0, white_board=0, last_played=Player.White):
        """Intialize an empty game state.

        Note:
            This state is not a valid game state and needs to be further
            initialized. Consider using `GameState.start_position()` instead.
        """
        self.black_board = black_board
        self.white_board = white_board
        self.last_played = last_played

    @staticmethod
    def start_position():
        """Return a GameState in the starting position."""
        state = GameState()
        state.black_board = rc2board(3, 3) | rc2board(4, 4)
        state.white_board = rc2board(3, 4) | rc2board(4, 3)
        return state

    def possible_moves(self, player):
        """Return a list of possible moves for the given player.

        Args:
            - player: The player to find moves for.

        Returns:
            A list of moves for the given player at the current GameState.
        """
        match player:
            case Player.Black:
                return find_moves(self.black_board, self.white_board)
            case Player.White:
                return find_moves(self.white_board, self.black_board)
            case _:
                raise ValueError(f"invalid player {player}")

    def _place_token(self, row, col, player):
        """Place a token on the board.

        Note:
            This function does not check if the position is unoccupied.
        """
        pattern = rc2board(row, col)
        match player:
            case Player.Black:
                self.black_board |= pattern
            case Player.White:
                self.white_board |= pattern
            case _:
                raise ValueError(f"invalid player {player}")

    def _next_player(self):
        """Return the next player or None if the game is over."""
        # TODO: You don't have to get both possible moves most of the time
        black_moves = self.possible_moves(Player.Black)
        white_moves = self.possible_moves(Player.White)
        match self.last_played:
            case Player.Black:
                if len(white_moves) > 0:
                    return Player.White
                elif len(black_moves) > 0:
                    return Player.Black
                else:
                    return None
            case Player.White:
                if len(black_moves) > 0:
                    return Player.Black
                elif len(white_moves) > 0:
                    return Player.White
                else:
                    return None
            case _:
                raise ValueError(f"invalid player {self.last_played}")

    def make_move(self, player, move):
        """Make a move from the given GameState.

        Args:
            - player: The player that is making the move.
            - move: The move about to be played.

        Returns:
            A new state where the given move has been played or None if the
            move is not legal.
        """
        # TODO: This feels pretty inefficient when trying to figure out if a
        # valid move is about to be played.
        if player != self._next_player():
            return None
        elif move not in self.possible_moves(player):
            return None
        elif is_occupied(move.row, move.col, self.black_board) or is_occupied(move.row, move.col, self.white_board):  # noqa: E501
            return None

        new_state = GameState(self.black_board, self.white_board, player)
        new_state._place_token(move.row, move.col, player)
        new_state.black_board ^= move.flip_board
        new_state.white_board ^= move.flip_board

        return new_state

    def _board_to_string(self):
        res = [" abcdefgh"]
        for row in range(BOARD_SIZE):
            r = [str(row + 1)]
            for col in range(BOARD_SIZE):
                if is_occupied(row, col, self.black_board):
                    r.append("B")
                elif is_occupied(row, col, self.white_board):
                    r.append("W")
                else:
                    r.append(".")
            res.append("".join(r))
        return "\n".join(res)

    def __str__(self):
        return f"""Next player: {self._next_player()}
{self._board_to_string()}
"""

    def __repr__(self):
        return f"GameState(black_board={self.black_board}, white_board={self.white_board}, last_played={self.last_played})"  # noqa: E501


if __name__ == "__main__":
    state = GameState().start_position()
    moves = state.possible_moves(Player.Black)
    state = state.make_move(Player.Black, moves[0])
    print(state)
