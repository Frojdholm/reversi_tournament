# Reversi Tournament

## Rules

The game is played on an 8x8 board where the players (B and W) start in the following position.
```
 a b c d e f g h
1
2
3
4      B W
5      W B
6
7
8
```

The game starts with player B's turn and the players then take turns
placing tokens. Each turn the players make a move by placing a token on
a non-occupied position on the board. For a move to be valid it needs
to cause at least 1 of the opponent's tokens to be flipped.

Tokens are flipped if, after the new token has been placed, they are
sandwiched directly between two tokens of the opposing color. There can
be no gaps and the tokens are only flipped to the first same colored
token. For flips 8 directions are considered; up, down, left, right
and diagonally:
```
 a b c d e f g h
1x     x     x
2  x   x   x
3    x x x
4x x x B x x x x
5    x x x
6  x   x   x
7x     x     x
8      x       x
```
For example if, from the starting position, player B chooses to play e3
the W token on e4 should be flipped.
```
 a b c d e f g h
1
2
3        b
4      B X
5      W B
6
7
8
```
If the player B in the below position places a token on b3 the W token
on g3 should not be flipped since the path is interuppted by the B token
on f3.
```
 a b c d e f g h
1
2
3  b X X X B W B
4
5
6
7
8
```
Only the new token is considered when flipping. In other words, flipping
is not recursive and flipped tokens *do not* cause additional flips.

If a player does not have a valid move they are forced to pass that
turn. The game ends when no player has any valid moves.

## Communication Protocol

The communcation protocol is loosely based on UCI. For a full
specification read the [Communication Protocol](communication_protocol.md)
