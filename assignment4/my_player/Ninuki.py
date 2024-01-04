#!/usr/bin/python3
# Set the path to your python3 above

"""
Go0 random Go player
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller
"""
from typing import Tuple, List, Union, Any

from numpy import signedinteger, intc
from numpy._typing import _32Bit

from gtp_connection import GtpConnection
from board_base import DEFAULT_SIZE, GO_POINT, GO_COLOR, PASS
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine
import random

EMPTY = GO_COLOR(0)
BLACK = GO_COLOR(1)
WHITE = GO_COLOR(2)
BORDER = GO_COLOR(3)
class Go0(GoEngine):
    def __init__(self) -> None:
        """
        Go player that selects moves randomly from the set of legal moves.
        Does not use the fill-eye filter.
        Passes only if there is no other legal move.
        """
        GoEngine.__init__(self, "Go0", 1.0)
        self._policy_type = "random"

    def set_policy(self, policy_type: str) -> None:
        """
        Set the policy type
        """
        self._policy_type = policy_type

    def get_policy(self) -> str:
        """
        Get the policy type
        """
        return self._policy_type
    def get_move(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        empty = len(board.get_empty_points())
        win_moves = [27,28,29,35,36,37,43,44,45]
        random.shuffle(win_moves)
        # print(board.get_empty_points())
        # opponent = EMPTY
        if color == BLACK:
            opponent = WHITE
        elif color == WHITE:
            opponent = BLACK
        has_better = 0

        protect = board.protect(color)
        if len(protect) > 0:
            moves = [protect[0]]
            has_better +=1
        capture = board.capture(color)
        if len(capture) > 0:
            moves = [capture[0]]
            has_better +=1
        opponent_open_four = board.open_four(opponent)
        if len(opponent_open_four) > 0:
            moves = [opponent_open_four[0]]
            has_better += 1
        open_four = board.open_four(color)
        if len(open_four) >0:
            moves = [open_four[0]]
            has_better+=1
        block_win = board.block_win(color)
        if len(block_win) > 0:
            moves = [block_win[0]]
            has_better+=1
        immediate_win = board.win_search(color)
        if len(immediate_win) > 0:
            moves = [immediate_win[0]]
            has_better +=1
        if color == BLACK:
            if empty == 49:
                moves = [36]
            elif empty >= 41:
                if has_better == 0:
                    for move in win_moves:
                        if move in board.get_empty_points():
                            moves = [move]
            else:
                print("simulating")
                moves = self.generate_moves(board, color)
        return moves
    def solve(self, board: GoBoard):
        """
        A2: Implement your search algorithm to solve a board
        Change if deemed necessary
        """
        pass
        
    def random_simulation(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        """
        Returns a move for a random simulation player
            Part 1: simulation-based ninuki player

            A simulation consists of a series of moves generated uniformly at random,
            and ends when the game is over (win or draw).

            The player runs N=10 simulations for each legal move, and picks one move with the highest win
            percentage. See simulation_player.py for a sample implementation of the algorithm.
            You are free to break ties between equally good moves in any way you wish.

            As in assignment 1, your player should resign or pass only when the game is over.
        """
        num_simulations = 10
        # get list of all legal moves
        legal_moves = GoBoardUtil.generate_legal_moves(board, color)
        # initialize a dictionary to store the win percentage for each legal move
        win_percentage = dict.fromkeys(legal_moves, 0)

        # for each legal move in the list, run num_simulations, where each simulation is a series of moves
        # generated uniformly at random until the game is over (win or draw) and store the win percentage
        for move in legal_moves:
            # one_deep_board = board.copy()

            for i in range(num_simulations):
                cboard = board.copy()
                cboard.play_move(move, color)
                while not cboard.end_of_game():
                    random_moves = GoBoardUtil.generate_legal_moves(cboard, cboard.current_player)
                    if random_moves == []:
                        break
                    random.shuffle(random_moves)
                    # print(random_moves)
                    random_move = random_moves[0]
                    cboard.play_move(random_move, cboard.current_player)

                if cboard.end_of_game() == color:
                    win_percentage[move] += (1 / num_simulations)
            # print(win_percentage)
        return max(win_percentage, key=win_percentage.get)

    def policy_simulation(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        """
        Returns a move for a random simulation player
            Part 1: simulation-based ninuki player

            A simulation consists of a series of moves generated uniformly at random,
            and ends when the game is over (win or draw).

            The player runs N=10 simulations for each legal move, and picks one move with the highest win
            percentage. See simulation_player.py for a sample implementation of the algorithm.
            You are free to break ties between equally good moves in any way you wish.

            As in assignment 1, your player should resign or pass only when the game is over.
        """
        num_simulations = 20
        # get list of all legal moves
        legal_moves = GoBoardUtil.generate_legal_moves(board, color)
        # initialize a dictionary to store the win percentage for each legal move
        win_percentage = dict.fromkeys(legal_moves, 0)

        # for each legal move in the list, run num_simulations, where each simulation is a series of moves
        # generated uniformly at random until the game is over (win or draw) and store the win percentage
        cboard = board.copy()
        tple = self.rule_based(cboard, color)
        moves = tple[1]
        for m in moves:
            # one_deep_board = board.copy()

            for i in range(num_simulations):
                cboard = board.copy()
                tple = self.rule_based(cboard, color)
                moves = tple[1]
                random.shuffle(moves)
                move = moves[0]
                # print(move)
                cboard.play_move(move, color)
                while not cboard.end_of_game():
                    tple = self.rule_based(cboard, color)
                    # print(tple)
                    theMove = tple[1]
                    random.shuffle(theMove)
                    # print(theMove)
                    cboard.play_move(theMove[0], cboard.current_player)

                if cboard.end_of_game() == color:
                    win_percentage[move] += (1 / num_simulations)
            print(win_percentage)
        return max(win_percentage, key=win_percentage.get)

    def rule_based(self, board: GoBoard, color: GO_COLOR) -> tuple[str, Any]:
        if color == BLACK:
            opponent = WHITE
        elif color == WHITE:
            opponent = BLACK
        immediate_win = board.win_search(color)
        if len(immediate_win) > 0:
            return "Win", immediate_win
        block_win = board.block_win(color)
        if len(block_win) > 0:
            return "BlockWin", block_win
        open_four = board.open_four(color)
        if len(open_four) >0:
            return"OpenFour", open_four
        opponent_open_four = board.open_four(opponent)
        if len(opponent_open_four) > 0:
            return "OOF", opponent_open_four
        capture = board.capture(color)
        if len(capture) > 0:
            return "Capture", capture
        protect = board.protect(color)
        if len(protect) > 0:
            return "Protect", protect

        return "Random", GoBoardUtil.generate_legal_moves(board, color)

    def generate_policy_moves(self, board: GoBoard, color: GO_COLOR) -> Union[
        tuple[str, list[Any]], tuple[str, list], tuple[Any, Any]]:
        """
        Generate a list of moves based on the policy type
        """
        if self.get_policy() == "rule_based":
            scenario, available_moves = self.rule_based(board, color)
            if len(available_moves) == 0:
                return "Random", [PASS]
            return scenario, available_moves
        elif self.get_policy() == "random":
            available_moves = GoBoardUtil.generate_legal_moves(board, color)
            if available_moves == None:  # No legal moves on the board
                return "Random", [PASS]
            return "Random", available_moves



    def generate_moves(self, board: GoBoard, color: GO_COLOR) -> Union[
        tuple[str, list[Union[signedinteger[_32Bit], intc]]], list[Union[signedinteger[_32Bit], intc]]]:
        """
        Generate a list of moves based on the policy type
        """
        if self.get_policy() == "random":
            available_moves = self.random_simulation(board, color)
            if available_moves == None:  # No legal moves on the board
                return  [PASS]
            return [available_moves]

        elif self.get_policy() == "rule_based":
            available_moves = self.policy_simulation(board, color)
            if available_moves == None:
                return "Random", [PASS]
            return [available_moves]

def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board: GoBoard = GoBoard(DEFAULT_SIZE)
    con: GtpConnection = GtpConnection(Go0(), board)
    con.start_connection()
IMMEDIATE_WIN_WHITE = [[WHITE, WHITE, WHITE, WHITE, EMPTY], [WHITE, WHITE, WHITE, EMPTY, WHITE],
                       [WHITE, WHITE, EMPTY, WHITE, WHITE], [WHITE, EMPTY, WHITE, WHITE, WHITE],
                       [EMPTY, WHITE, WHITE, WHITE, WHITE]]

IMMEDIATE_WIN_BLACK = [[BLACK, BLACK, BLACK, BLACK, EMPTY], [BLACK, BLACK, BLACK, EMPTY, BLACK],
                       [BLACK, BLACK, EMPTY, BLACK, BLACK], [BLACK, EMPTY, BLACK, BLACK, BLACK],
                       [EMPTY, BLACK, BLACK, BLACK, BLACK]]

WHITE_CAPTURE = [[WHITE, BLACK, BLACK, EMPTY],
                 [EMPTY, BLACK, BLACK, WHITE]]


BLACK_CAPTURE = [[BLACK, WHITE, WHITE, EMPTY],
                 [EMPTY, WHITE, WHITE, BLACK]]

OPEN_FOUR_WHITE = [[EMPTY, WHITE, WHITE, WHITE, EMPTY, EMPTY],
                   [EMPTY, WHITE, WHITE, EMPTY, WHITE, EMPTY],
                   [EMPTY, WHITE, EMPTY, WHITE, WHITE, EMPTY],
                   [EMPTY, EMPTY, WHITE, WHITE, WHITE, EMPTY]]

OPEN_FOUR_BLACK = [[EMPTY, BLACK, BLACK, BLACK, EMPTY, EMPTY],
                   [EMPTY, BLACK, BLACK, EMPTY, BLACK, EMPTY],
                   [EMPTY, BLACK, EMPTY, BLACK, BLACK, EMPTY],
                   [EMPTY, EMPTY, BLACK, BLACK, BLACK, EMPTY]]

PROTECT_CAPTURE_BLACK = [[EMPTY,BLACK,BLACK,WHITE],[WHITE,BLACK,BLACK,EMPTY]]
if __name__ == "__main__":
    run()
