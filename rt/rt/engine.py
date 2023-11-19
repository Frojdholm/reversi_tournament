import sys
import logging
from enum import Enum, auto

from rt.state import GameState, Move, Player
from rt.agent import RandomAgent


logger = logging.getLogger(__name__)


class EngineError(Exception):
    pass


def expect(expected, actual):
    if expected != actual:
        raise EngineError(f"expected: {expected}, got: {actual}")


class Engine:
    """An `Engine` is a state machine that drives the communication with the UI.

    It implements the engine part of the RT v1 protocol and can be used
    to more easily pass data to and from an `Agent`. The engine will parse
    commands and translate them to calls to the `Agent` interface.

    If a command is unexpected or wrong an `EngineError` will be raised.
    """

    class State(Enum):
        Uninitialized = auto()
        """The engine is unitialized and awaiting the "reversi_v1" command."""
        AwaitingNewGame = auto()
        """The engine has been initialized and sent its id commands, but no game has been started."""
        NewGameCompleted = auto()
        """A game has been created and the engine is awaiting "isready"."""
        AwaitingPosition = auto()
        """The engine is ready to receive positions."""
        PositionParsed = auto()
        """The position has been parsed and the engine is awaiting "isready"."""
        AwaitingGo = auto()
        """The engine is ready to search and is awaiting the "go" command."""

    def __init__(self, agent_factory, instream, outstream):
        """Create a new Engine.

        Args:
            agent_factory: A callable that when called with "b" or "w" will
                           create a new agent ready to play as black or white
                           respectively.
            instream: The file-like object to get input from.
            outstream: The file-like object to send output to.
        """
        self.agent_factory = agent_factory
        self.instream = instream
        self.outstream = outstream
        self.state = Engine.State.Uninitialized
        self.name = "TESTENGINE 1.0"
        self.author = "<author>"
        self.game_state = None
        self.agent = None
        logger.info("creating engine: %s by %s", self.name, self.author)

    def run(self):
        for msg in self.instream:
            msg = msg.strip()
            logger.debug("recv: %s", msg)
            try:
                self.parse(msg)
                # Flush to ensure the message is sent to the UI.
                self.outstream.flush()
            except EngineError as err:
                logger.error("error: %s", err)

    def parse(self, msg):
        """Parse a message from the UI.

        This function will respond to the message by sending text on `stdout`.
        Multiple messages might we written and `stdout` will not be flushed.

        Args:
            msg: The message from the UI.

        Raises:
            EngineError: If the message was unexpected or wrong.
        """
        command, *args = msg.split()

        # The newgame command is allowed any time after the engine has
        # been initialized. In that case we intercept it here and reset
        # the engine state.
        if command == "newgame" and self.state != Engine.State.Uninitialized:
            self.state = Engine.State.AwaitingNewGame
            # TODO: Resetting the state here is not really necessary since it
            # should be overwritten by the next UI commands anyway
            self.agent = None
            self.game_state = None

        match self.state:
            case Engine.State.Uninitialized:
                expect("reversi_v1", command)
                self.send_id()
                self.state = Engine.State.AwaitingNewGame
            case Engine.State.AwaitingNewGame:
                expect("newgame", command)
                self.setup_agent(args)
                self.state = Engine.State.NewGameCompleted
            case Engine.State.NewGameCompleted:
                expect("isready", command)
                self.send_ready_ok()
                self.state = Engine.State.AwaitingPosition
            case Engine.State.AwaitingPosition:
                expect("position", command)
                self.parse_position(args)
                self.state = Engine.State.PositionParsed
            case Engine.State.PositionParsed:
                expect("isready", command)
                self.send_ready_ok()
                self.state = Engine.State.AwaitingGo
            case Engine.State.AwaitingGo:
                expect("go", command)
                self.send_best_move(args)
                self.state = Engine.State.AwaitingPosition

    def send_id(self):
        self.respond(f"id name {self.name}")
        self.respond(f"id author {self.author}")
        self.respond("reversi_v1_ok")

    def setup_agent(self, args):
        if len(args) != 1:
            raise EngineError(f"invalid newgame args: {args}")
        p = args[0].lower()
        if p not in ("b", "w"):
            raise EngineError(f"invalid newgame args: {args}")
        player = Player.Black if p == "b" else Player.White
        self.agent = self.agent_factory(player)

    def send_best_move(self, args):
        if len(args) != 4:
            raise EngineError(f"invalid go args: {args}")
        kwargs = {}
        for a in args:
            key, value = a.split("=")
            kwargs[key] = int(value)
        # TODO: Make this robust in case an argument is wrong
        move = self.agent.search(**kwargs)
        self.respond(f"bestmove {move}")

    def send_ready_ok(self):
        self.respond("readyok")

    def parse_position(self, moves):
        expect("startpos", moves[0])
        state = GameState.start_position()
        for m in moves[1:]:
            # TODO: Raise an error if the move is invalid
            move = Move.from_str(m, state)
            state = state.make_move(move)

        logger.debug("parsed position: %r", state)
        self.agent.set_state(state)

    def respond(self, msg):
        # Strip to ensure only a single newline is written
        msg = msg.strip()
        logger.debug("send: %s", msg)
        self.outstream.write(msg + "\n")


def run():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("player")

    args = parser.parse_args()

    logging.basicConfig(filename=f"engine{args.player}.log", level=logging.DEBUG)
    engine = Engine(RandomAgent, instream=sys.stdin, outstream=sys.stdout)
    engine.run()
