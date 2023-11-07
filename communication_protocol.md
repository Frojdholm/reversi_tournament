# RT V1 Communication Protocol

The communication protocol is loosely based on the Universal Chess Interface
(UCI).

All communication between the engine and the UI should be ended with a
single newline character `\n`. Newlines inside a message is not allowed,
but other arbitrary whitespace between fields is:

Valid message:
```
position\tstartpos e3b\n
```

Invalid message:
```
position\nstartpos e3b\n
```

All moves are 3 characters (for example `a5b`) where the first two characters
denote the square on the board
```
 a b c d e f g h
1
2
3
4
5
6
7
8
```
and the third character represents the player of the move, either `b` for
black or `w` for white. The move notation is case-insensitive.

The starting board configuration looks like the following:
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

## Rationale

The communication is designed to allow stateless engines. In other words,
the engine should not have to save any data between successive `go`
messages.  All data that is needed to evaluate a position is sent in the
`position` message. This helps with keeping the engine synchronized. If
the engine chooses to keep internal state these messages can be used to
detect mismatches between the engine and the UI.

## Rules

While not mandatory, an engine is allowed to save state between successive
`go` messages, however it is not allowed to modify any state related to
the search after the `bestmove` message has been sent. The `position`
message should be still be parsed into the internal state representation
of the engine, but no search can take place.

## Messages

### UI to engine

- `reversi_v1`
    - Initialize the engine to communicate according the protocol described
      in this document. This is required to be the first message sent from
      the UI to the engine and the engine needs to respond with `id` messages
      followed by `reversi_v1_ok`.
- `newgame (b|w)`
    - Initialize a new game in the engine. `position` and `go` commands
      sent after this should be assumed to belong to the same game. `b`
      or `w` gives the color that this engine is playing this game.
- `isready`
    - Used to wait for the engine when multiple commands have been sent for
      for synchronization purposes. Specifically this is sent after sending
      `newgame` or `position` to give the engine time to initialize fully
      before continuing.
- `position startpos moves...`
    - Load up the position for searching. `startpos` corresponds to the
      following squares being filled: `d4b e4w d5w e5b`. `moves...`
      is a list of moves describing the additional moves that have been
      played since the start of the game. Note that at the start of the
      game there are no additional moves, in which case the message is
      only `position startpos`.
- `go btime=<t> wtime=<t> binc=<t> winc<t>`
    - Initiate a search in the engine. The order of the `btime`, `wtime`,
      `binc` and `winc` key-values is not guaranteed. `btime` and `wtime`
      give the total time remaining for black and white respectively and
      `binc` and `winc` gives the time increase after each completed move.
      After sending this message the UI will await a `bestmove` message
      from the engine.

### Engine to UI

- `id`
    - `name MyEngine 1.0`
        - Sent from the engine to the UI after receiving `reversi_v1`. The
          message should specify the name of the engine, for example
          `id name MyEngine 1.0`
    - `author AuthorNickname`
        - Sent from the engine to the UI after receiving `reversi_v1`. The
          message should specify the author of the engine, for example
          `id author AuthorNickname`
- `reversi_v1_ok`
    - Sent after the `id` messages to signify that the engine configuration
      is complete.
- `readyok`
    - Sent by the engine in response to an `isready` from the UI.
- `bestmove <move>`
    - The best move found by the engine. Note that the player should
      still be included in the move.
