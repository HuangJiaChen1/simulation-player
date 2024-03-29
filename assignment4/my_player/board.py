"""
board.py
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from typing import List, Tuple

from board_base import (
    board_array_size,
    coord_to_point,
    is_black_white,
    is_black_white_empty,
    opponent,
    where1d,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    MAXSIZE,
    NO_POINT,
    PASS,
    GO_COLOR,
    GO_POINT,
)


"""
The GoBoard class implements a board and basic functions to play
moves, check the end of the game, and count the acore at the end.
The class also contains basic utility functions for writing a Go player.
For many more utility functions, see the GoBoardUtil class in board_util.py.

The board is stored as a one-dimensional array of GO_POINT in self.board.
See coord_to_point for explanations of the array encoding.
"""
class GoBoard(object):
    def __init__(self, size: int) -> None:
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)
        self.calculate_rows_cols_diags()
        self.black_captures = 0
        self.white_captures = 0
        self.played_moves = 0

    def add_two_captures(self, color: GO_COLOR) -> None:
        if color == BLACK:
            self.black_captures += 2
        elif color == WHITE:
            self.white_captures += 2
    def get_captures(self, color: GO_COLOR) -> None:
        if color == BLACK:
            return self.black_captures
        elif color == WHITE:
            return self.white_captures
    
    def calculate_rows_cols_diags(self) -> None:
        if self.size < 5:
            return
        # precalculate all rows, cols, and diags for 5-in-a-row detection
        self.rows = []
        self.cols = []
        for i in range(1, self.size + 1):
            current_row = []
            start = self.row_start(i)
            for pt in range(start, start + self.size):
                current_row.append(pt)
            self.rows.append(current_row)
            
            start = self.row_start(1) + i - 1
            current_col = []
            for pt in range(start, self.row_start(self.size) + i, self.NS):
                current_col.append(pt)
            self.cols.append(current_col)
        
        self.diags = []
        # diag towards SE, starting from first row (1,1) moving right to (1,n)
        start = self.row_start(1)
        for i in range(start, start + self.size):
            diag_SE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_SE.append(pt)
                pt += self.NS + 1
            if len(diag_SE) >= 4:
                self.diags.append(diag_SE)
        # diag towards SE and NE, starting from (2,1) downwards to (n,1)
        for i in range(start + self.NS, self.row_start(self.size) + 1, self.NS):
            diag_SE = []
            diag_NE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_SE.append(pt)
                pt += self.NS + 1
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_NE.append(pt)
                pt += -1 * self.NS + 1
            if len(diag_SE) >= 4:
                self.diags.append(diag_SE)
            if len(diag_NE) >= 4:
                self.diags.append(diag_NE)
        # diag towards NE, starting from (n,2) moving right to (n,n)
        start = self.row_start(self.size) + 1
        for i in range(start, start + self.size):
            diag_NE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_NE.append(pt)
                pt += -1 * self.NS + 1
            if len(diag_NE) >=4:
                self.diags.append(diag_NE)
        assert len(self.rows) == self.size
        assert len(self.cols) == self.size
        # assert len(self.diags) == (2 * (self.size - 5) + 1) * 2

    def reset(self, size: int) -> None:
        """
        Creates a start state, an empty board with given size.
        """
        self.size: int = size
        self.NS: int = size + 1
        self.WE: int = 1
        self.ko_recapture: GO_POINT = NO_POINT
        self.last_move: GO_POINT = NO_POINT
        self.last2_move: GO_POINT = NO_POINT
        self.current_player: GO_COLOR = BLACK
        self.maxpoint: int = board_array_size(size)
        self.board: np.ndarray[GO_POINT] = np.full(self.maxpoint, BORDER, dtype=GO_POINT)
        self._initialize_empty_points(self.board)
        self.calculate_rows_cols_diags()
        self.black_captures = 0
        self.white_captures = 0

    def copy(self) -> 'GoBoard':
        b = GoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.last_move = self.last_move
        b.last2_move = self.last2_move
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def get_color(self, point: GO_POINT) -> GO_COLOR:
        return self.board[point]

    def pt(self, row: int, col: int) -> GO_POINT:
        return coord_to_point(row, col, self.size)

    def _is_legal_check_simple_cases(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check the simple cases of illegal moves.
        Some "really bad" arguments will just trigger an assertion.
        If this function returns False: move is definitely illegal
        If this function returns True: still need to check more
        complicated cases such as suicide.
        """
        assert is_black_white(color)
        if point == PASS:
            return True
        # Could just return False for out-of-bounds, 
        # but it is better to know if this is called with an illegal point
        assert self.pt(1, 1) <= point <= self.pt(self.size, self.size)
        assert is_black_white_empty(self.board[point])
        if self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
        return True

    def is_legal(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check whether it is legal for color to play on point
        This method tries to play the move on a temporary copy of the board.
        This prevents the board from being modified by the move
        """
        if point == PASS:
            return True
        board_copy: GoBoard = self.copy()
        can_play_move = board_copy.play_move(point, color)
        return can_play_move

    def end_of_game(self) -> bool:
        if self.last_move == PASS and self.last2_move == PASS:
            return -1
        if self.detect_five_in_a_row() != EMPTY:
            return opponent(self.current_player)
        if self.black_captures >= 10 or self.white_captures >= 10:
            return opponent(self.current_player)
        if self.get_empty_points().size == 0:
            return True
        return False

    def get_empty_points(self) -> np.ndarray:
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def row_start(self, row: int) -> int:
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1

    def _initialize_empty_points(self, board_array: np.ndarray) -> None:
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start: int = self.row_start(row)
            board_array[start : start + self.size] = EMPTY

    def is_eye(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge  # 0 at edge, 1 in center

    def _is_surrounded(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        check whether empty point is surrounded by stones of color
        (or BORDER) neighbors
        """
        for nb in self._neighbors(point):
            nb_color = self.board[nb]
            if nb_color != BORDER and nb_color != color:
                return False
        return True

    def _has_liberty(self, block: np.ndarray) -> bool:
        """
        Check if the given block has any liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            empty_nbs = self.neighbors_of_color(stone, EMPTY)
            if empty_nbs:
                return True
        return False

    def _block_of(self, stone: GO_POINT) -> np.ndarray:
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        color: GO_COLOR = self.get_color(stone)
        assert is_black_white(color)
        return self.connected_component(stone)

    def connected_component(self, point: GO_POINT) -> np.ndarray:
        """
        Find the connected component of the given point.
        """
        marker = np.full(self.maxpoint, False, dtype=np.bool_)
        pointstack = [point]
        color: GO_COLOR = self.get_color(point)
        assert is_black_white_empty(color)
        marker[point] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _detect_and_process_capture(self, nb_point: GO_POINT) -> GO_POINT:
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
        and returns NO_POINT otherwise.
        This result is used in play_move to check for possible ko
        """
        single_capture: GO_POINT = NO_POINT
        opp_block = self._block_of(nb_point)
        if not self._has_liberty(opp_block):
            captures = list(where1d(opp_block))
            self.board[captures] = EMPTY
            if len(captures) == 1:
                single_capture = nb_point
        return single_capture
    
    def play_move(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Tries to play a move of color on the point.
        Returns whether or not the point was empty.
        """
        if self.board[point] != EMPTY:
            return False
        self.board[point] = color
        self.current_player = opponent(color)
        self.last2_move = self.last_move
        self.last_move = point
        O = opponent(color)
        offsets = [1, -1, self.NS, -self.NS, self.NS+1, -(self.NS+1), self.NS-1, -self.NS+1]
        for offset in offsets:
            if self.board[point+offset] == O and self.board[point+(offset*2)] == O and self.board[point+(offset*3)] == color:
                self.board[point+offset] = EMPTY
                self.board[point+(offset*2)] = EMPTY
                if color == BLACK:
                    self.black_captures += 2
                else:
                    self.white_captures += 2
        return True
    
    def neighbors_of_color(self, point: GO_POINT, color: GO_COLOR) -> List:
        """ List of neighbors of point of given color """
        nbc: List[GO_POINT] = []
        for nb in self._neighbors(point):
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc

    def _neighbors(self, point: GO_POINT) -> List:
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point: GO_POINT) -> List:
        """ List of all four diagonal neighbors of point """
        return [point - self.NS - 1,
                point - self.NS + 1,
                point + self.NS - 1,
                point + self.NS + 1]

    def last_board_moves(self) -> List:
        """
        Get the list of last_move and second last move.
        Only include moves on the board (not NO_POINT, not PASS).
        """
        board_moves: List[GO_POINT] = []
        if self.last_move != NO_POINT and self.last_move != PASS:
            board_moves.append(self.last_move)
        if self.last2_move != NO_POINT and self.last2_move != PASS:
            board_moves.append(self.last2_move)
        return board_moves

    def detect_five_in_a_row(self) -> GO_COLOR:
        """
        Returns BLACK or WHITE if any five in a row is detected for the color
        EMPTY otherwise.
        """
        for r in self.rows:
            result = self.has_five_in_list(r)
            if result != EMPTY:
                return result
        for c in self.cols:
            result = self.has_five_in_list(c)
            if result != EMPTY:
                return result
        for d in self.diags:
            result = self.has_five_in_list(d)
            if result != EMPTY:
                return result
        return EMPTY

    def has_five_in_list(self, list) -> GO_COLOR:
        """
        Returns BLACK or WHITE if any five in a rows exist in the list.
        EMPTY otherwise.
        """
        prev = BORDER
        counter = 1
        for stone in list:
            if self.get_color(stone) == prev:
                counter += 1
            else:
                counter = 1
                prev = self.get_color(stone)
            if counter == 5 and prev != EMPTY:
                return prev
        return EMPTY

    def win_search(self,color):
        win_moves = []
        stones = []
        stone = []
        for r in self.rows:
            for i in r:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for c in self.cols:
            for i in c:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for d in self.diags:
            for i in d:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []

        if color == WHITE:
            result = search_patterns(IMMEDIATE_WIN_WHITE,stones)
            for i in range(len(result)):
                pattern = result[i][0]
                ind = result[i][2]
                winr = result[i][1]

                winc = pattern.index(EMPTY)+ind
                boards = []
                for board in self.rows + self.cols + self.diags:
                    boards.append(board)
                win_move = boards[winr][winc]
                win_moves.append(win_move)

        elif color == BLACK:
            result = search_patterns(IMMEDIATE_WIN_BLACK, stones)
            for i in range(len(result)):
                pattern = result[i][0]
                ind = result[i][2]
                winr = result[i][1]
                winc = pattern.index(EMPTY)+ ind

                boards = []
                for board in self.rows+self.cols+self.diags:
                    boards.append(board)
                win_move = boards[winr][winc]
                win_moves.append(win_move)


            if self.black_captures == 8:
                # move = self.get_empty_points()
                # win_moves.append(move)
                pass

        return win_moves

    def block_win(self,color):
        stones = []
        stone = []
        block_moves = []
        color = opponent(color)
        for r in self.rows:
            for i in r:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for c in self.cols:
            for i in c:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for d in self.diags:
            for i in d:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        # print(stones)
        if color == WHITE:
            result = search_patterns(IMMEDIATE_WIN_WHITE,stones)
            # print(result)
            for i in range(len(result)):
                pattern = result[i][0]
                ind = result[i][2]
                winr = result[i][1]
                # print(winr)
                winc = pattern.index(EMPTY)+ind
                # print(winc)
                boards = []
                for board in self.rows + self.cols + self.diags:
                    boards.append(board)
                win_move = boards[winr][winc]
                block_moves.append(win_move)
                length = len(self.win_search(WHITE))
                capture_moves = self.capture(BLACK)
                # print(f"capture_moves:{capture_moves}")
                for j in capture_moves:
                    cboard = self.copy()
                    cboard.play_move(j, BLACK)
                    # print(self.win_search(BLACK))
                    if len(cboard.win_search(WHITE)) != length:
                        block_moves.append(j)
            if self.white_captures == 8:
                move = self.capture(WHITE)
                for i in move:
                    block_moves.append(i)


        elif color == BLACK:
            result = search_patterns(IMMEDIATE_WIN_BLACK, stones)
            pattern = []
            for i in range(len(result)):
                pattern = result[i][0]
                winr = result[i][1]
                winc = pattern.index(EMPTY)
                boards = []
                for board in self.rows+self.cols+self.diags:
                    boards.append(board)

                win_move = boards[winr][winc]
                block_moves.append(win_move)
            length = len(self.win_search(BLACK))
            capture_moves = self.capture(WHITE)
            # print(f"capture_moves:{capture_moves}")
            for j in capture_moves:
                cboard = self.copy()
                cboard.play_move(j,WHITE)
                # print(self.win_search(BLACK))
                if len(cboard.win_search(BLACK)) != length:
                    block_moves.append(j)
            if self.black_captures == 8:
                move = self.capture(BLACK)
                for i in move:
                    block_moves.append(i)

        return block_moves

    '''
    DEBUG THIS
    '''
    def open_four(self,color):
        stones = []
        stone = []
        open4_moves =[]
        for r in self.rows:
            for i in r:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for c in self.cols:
            for i in c:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for d in self.diags:
            for i in d:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        if color == WHITE:
            result = search_patterns(OPEN_FOUR_WHITE,stones)
            for i in range(len(result)):
                pattern = result[i][0]
                realind = -1
                if pattern == OPEN_FOUR_WHITE[0]:
                    realind = 4
                elif pattern == OPEN_FOUR_WHITE[1]:
                    realind = 3
                elif pattern == OPEN_FOUR_WHITE[2]:
                    realind = 2
                elif pattern == OPEN_FOUR_WHITE[3]:
                    realind = 1
                ind = result[i][2]
                winr = result[i][1]
                winc = realind + ind
                boards = []
                for board in self.rows + self.cols + self.diags:
                    boards.append(board)
                win_move = boards[winr][winc]
                open4_moves.append(win_move)
        elif color == BLACK:
            result = search_patterns(OPEN_FOUR_BLACK, stones)
            for i in range(len(result)):
                pattern = result[i][0]
                realind = -1
                if pattern == OPEN_FOUR_BLACK[0]:
                    realind = 4
                elif pattern == OPEN_FOUR_BLACK[1]:
                    realind = 3
                elif pattern == OPEN_FOUR_BLACK[2]:
                    realind = 2
                elif pattern == OPEN_FOUR_BLACK[3]:
                    realind = 1
                ind = result[i][2]
                winr = result[i][1]
                winc = realind + ind
                boards = []
                for board in self.rows+self.cols+self.diags:
                    boards.append(board)
                win_move = boards[winr][winc]
                open4_moves.append(win_move)
                # print(open4_moves)
        return open4_moves

    '''
    DEBUG
    '''
    def capture(self,color):
        stones = []
        stone = []
        capture_move = []
        for r in self.rows:
            for i in r:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for c in self.cols:
            for i in c:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for d in self.diags:
            for i in d:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        #print(stones)
        if color == WHITE:
            result = search_patterns(WHITE_CAPTURE, stones)
            for i in range(len(result)):
                pattern = result[i][0]
                ind = result[i][2]
                winr = result[i][1]
                # print(winr)
                winc = pattern.index(EMPTY) + ind
                # print(winc)
                boards = []
                for board in self.rows + self.cols + self.diags:
                    boards.append(board)
                win_move = boards[winr][winc]
                capture_move.append(win_move)
                # o4_moves = self.open_four(WHITE)
                # block_moves.append(o4_moves)
                # print(capture_move)


        elif color == BLACK:
            result = search_patterns(BLACK_CAPTURE, stones)
            # print(result)
            for i in range(len(result)):
                pattern = result[i][0]
                ind = result[i][2]
                winr = result[i][1]
                # print(winr)
                winc = pattern.index(EMPTY) + ind
                # print(winc)
                boards = []
                for board in self.rows + self.cols + self.diags:
                    boards.append(board)
                # print(boards)
                win_move = boards[winr][winc]
                capture_move.append(win_move)
                # o4_moves = self.open_four(BLACK)
                # block_moves.append(o4_moves)
                # print(capture_move)

        return capture_move

    def protect(self,color):
        stones = []
        stone = []
        protect_moves = []
        for r in self.rows:
            for i in r:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for c in self.cols:
            for i in c:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        for d in self.diags:
            for i in d:
                stone.append(self.get_color(i))
            stones.append(stone)
            stone = []
        if color == BLACK:
            result = search_patterns(PROTECT_CAPTURE_BLACK, stones)
            for i in range(len(result)):
                pattern = result[i][0]
                ind = result[i][2]
                winr = result[i][1]
                winc = pattern.index(EMPTY) + ind
                boards = []
                for board in self.rows + self.cols + self.diags:
                    boards.append(board)
                # print(boards)
                win_move = boards[winr][winc]
                protect_moves.append(win_move)
        return protect_moves
def build_lps(pattern):
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1

    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1

    return lps

def kmp_search(pattern, text, row_index):
    n = len(text)
    m = len(pattern)
    lps = build_lps(pattern)

    i = j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1

            if j == m:
                start_index = i - j
                return pattern, row_index, start_index
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return None

def search_patterns(array_A, array_B):
    results = []

    for row_index_B, text in enumerate(array_B):
        for row_index_A, pattern in enumerate(array_A):
            result = kmp_search(pattern, text, row_index_B)
            if result:
                results.append(result)

    return results
# Define patterns and the offsets in order to retrieve the empty square later on.
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