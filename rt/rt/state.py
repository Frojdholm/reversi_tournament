from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


BOARD_SIZE = 8


def is_occupied(row, col, board):
    """Checks if the position is occupied on the board.

    Args:
        ind: The position on the board in index format.
        board: The board to check.

    Returns:
        True if the position is occupied, False otherwise.
    """
    return rc2board(row, col) & board != 0


def is_inbounds(row, col):
    """Checks if the position is on the board.

    Args:
        ind: The position in index format.

    Returns:
        True if the position is a valid position on the board, False otherwise.
    """
    return row >= 0 and row < BOARD_SIZE and col >= 0 and col < BOARD_SIZE


def rc2ind(row, col):
    """Convert a position from RC (row, col) format to index format.

    Args:
        row: The row index (0-based).
        col: The column index (0-based).

    Returns:
        The position in index format.
    """
    return row * BOARD_SIZE + col


def rc2board(row, col):
    """Convert a position from RC (row, col) format to board format.

    Board format is an integer where the bits represent occupied places.

    Args:
        row: The row index (0-based).
        col: The column index (0-based).

    Returns:
        The position in board format.
    """
    return ind2board(rc2ind(row, col))


def ind2board(ind):
    """Convert a position from index format to board format.

    Board format is an integer where the bits represent occupied places.

    Args:
        ind: The position in index format.

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
        | find_flips_along_direction(row, col, -1, 1, my_board, opponent_board)
        | find_flips_along_direction(row, col, 1, 1, my_board, opponent_board)
    )


def find_moves(player, my_board, opponent_board):
    moves = []
    for row, col in iter_board():
        # A move is only valid if the position is unoccupied
        if not is_occupied(row, col, my_board) and not is_occupied(row, col, opponent_board):
            flip_board = find_flips(row, col, my_board, opponent_board)
            # A move is only valid if it flips at least one token
            if flip_board != 0:
                moves.append(Move(row, col, flip_board, player))
    return moves


def col_to_string(col):
    return chr(col + ord("a"))


def parse_move_string(move):
    """Parse the string representation of a move.

    The string representation of a move is "column-row-player" where the column
    is given as a letter a-h and the row as an index (1-based) and player is
    either "b" or "w".

    Some examples of valid string representations are: a3b, h8w and g4b.

    While the string representation can be a valid move, it is not guaranteed
    that the move is playable. For a move to be playable the move has to flip
    at least one of the opponents tokens which depends on the current state of
    the game.

    Args:
        move: The string representation of a move.

    Returns:
        A tuple containing the row-index (0-based), column-index (0-based) and
        the Player.
    """
    if len(move) != 3:
        raise ValueError(f"invalid move: {move}")

    col, row, player = move.lower()
    col = ord(col) - ord("a")
    row = int(row) - 1

    if not is_inbounds(row, col) or (player != "b" and player != "w"):
        raise ValueError(f"invalid move: {move}")

    player = Player.Black if player == "b" else Player.White
    return row, col, player


class Player(Enum):
    Black = "b"
    White = "w"

    def opponent(self):
        match self:
            case Player.Black:
                return Player.White
            case Player.White:
                return Player.Black


@dataclass
class Move:
    row: int
    col: int
    flip_board: int
    player: Player

    @staticmethod
    def from_str(move, state):
        row, col, player = parse_move_string(move)
        match player:
            case Player.Black:
                flip_board = find_flips(row, col, state.black_board, state.white_board)
            case Player.White:
                flip_board = find_flips(row, col, state.white_board, state.black_board)
        return Move(row, col, flip_board, player)

    def __str__(self):
        return f"{col_to_string(self.col)}{self.row + 1}{self.player.value}"


class GameState:
    """The state of the game at a certain point in time."""

    def __init__(self, black_board=0, white_board=0, last_played=Player.White):
        """Intialize an empty game state.

        Note:
            This state is likely not a valid game state and needs to be further
            initialized. Consider using `GameState.start_position()` instead and
            playing moves.
        """
        self.black_board = black_board
        self.white_board = white_board
        self.last_played = last_played

    @staticmethod
    def start_position():
        """Return a GameState in the starting position."""
        state = GameState()
        state.black_board = rc2board(3, 4) | rc2board(4, 3)
        state.white_board = rc2board(3, 3) | rc2board(4, 4)
        return state

    def possible_moves(self, player):
        """Return a list of possible moves for the given player.

        Args:
            player: The player to find moves for.

        Returns:
            A list of moves for the given player at the current GameState.
        """
        return possible_moves(self, player)

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

    def next_player(self):
        """Return the next player or None if the game is over."""
        match self.last_played:
            case Player.Black:
                if len(self.possible_moves(Player.White)) > 0:
                    return Player.White
                elif len(self.possible_moves(Player.Black)) > 0:
                    return Player.Black
                else:
                    return None
            case Player.White:
                if len(self.possible_moves(Player.Black)) > 0:
                    return Player.Black
                elif len(self.possible_moves(Player.White)) > 0:
                    return Player.White
                else:
                    return None

    def make_move(self, move):
        """Make a move from the given GameState.

        Args:
            move: The move about to be played. Note that move is assumed to be
                  playable. Use `GameState.possible_moves` and `GameState.next_player`
                  to determine if a move is possible before calling this function.

        Returns:
            A new state where the given move has been played.
        """
        # TODO: Add optional assertions here to check that move is actually valid
        new_state = GameState(self.black_board, self.white_board, move.player)
        new_state._place_token(move.row, move.col, move.player)
        new_state.black_board ^= move.flip_board
        new_state.white_board ^= move.flip_board

        return new_state

    def winner(self):
        b = self.count(Player.Black)
        w = self.count(Player.White)
        if b > w:
            return Player.Black
        elif w > b:
            return Player.White
        else:
            return None

    def count(self, player):
        match player:
            case Player.Black:
                return bin(self.black_board).count("1")
            case Player.White:
                return bin(self.white_board).count("1")

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
        return f"""Next player: {self.next_player()}
{self._board_to_string()}
"""

    def __repr__(self):
        return f"GameState(black_board={self.black_board}, white_board={self.white_board}, last_played={self.last_played})"


@lru_cache
def possible_moves(state, player):
    match player:
        case Player.Black:
            return find_moves(player, state.black_board, state.white_board)
        case Player.White:
            return find_moves(player, state.white_board, state.black_board)
