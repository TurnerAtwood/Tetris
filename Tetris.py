from time import sleep
from enum import Enum
from copy import deepcopy
from queue import deque
from random import shuffle
import curses

"""
PIECE_INDEX = [
	('I',[[1],[1],[1],[1]]),
	('J',[[1,0,0],[1,1,1]]),
	('L',[[0,0,1],[1,1,1]]),
	('O',[[1,1],[1,1]]),
	('S',[[0,1,1],[1,1,0]]),
	('T',[[0,1,0],[1,1,1]]),
	('Z',[[1,1,0],[0,1,1]])]
"""

PIECE_INDEX = [
	[[1],[1],[1],[1]],
	[[1,0,0],[1,1,1]],
	[[0,0,1],[1,1,1]],
	[[1,1],[1,1]],
	[[0,1,1],[1,1,0]],
	[[0,1,0],[1,1,1]],
	[[1,1,0],[0,1,1]]]

NUM_PIECES = len(PIECE_INDEX)

height = 20
width = 10
FULL_CHR = chr(int('2588',16))
GHOST_CHR = chr(735)
# FULL_CHR = '*'
FULL_LINE  = [FULL_CHR for i in range(width)]
EMPTY_LINE = [' ' for i in range(width)]

SORTED_BAG = [i%NUM_PIECES for i in range(NUM_PIECES)]

class Piece_Bag():
	def __init__(self):
		self.bag = deque()
		self.fill_bag()

	def fill_bag(self):
		clean_bag = deepcopy(SORTED_BAG)
		shuffle(clean_bag)
		self.bag.extend(clean_bag)

	def next(self):
		if len(self.bag) < 7:
			self.fill_bag()
		new_piece_index = self.bag.popleft()
		new_piece = piece(new_piece_index)
		return new_piece

class piece():
	def __init__(self, index):
		self.x = width//2
		self.grid = PIECE_INDEX[index]
		self.width = len(self.grid[0])
		self.move(0)

	# Rotate clockwise about the top-left corner
	def rotate(self):
		new_width = len(self.grid)
		new_grid = [[0 for i in range(new_width)] for i in range(self.width)]

		# Flip across main diag
		for i in range(len(self.grid)):
			for j in range(self.width):
				if self.grid[i][j]:
					new_grid[j][i] = 1

		self.grid = new_grid
		new_grid = [[0 for i in range(new_width)] for i in range(self.width)]

		# Flip across y-axis
		for i in range(len(new_grid)):
			for j in range(new_width):
				if self.grid[i][j]:
					new_grid[i][new_width-1-j] = 1

		self.grid = new_grid
		self.width = new_width
		self.move(0)

	# Move left/right and keep in bounds
	def move(self, dist):
		self.x += dist
		self.x = max(0,self.x)
		self.x = min(width - self.width, self.x)

	def center(self):
		self.x = width//2
		self.move(0)

class Tetris_Engine():

	def __init__(self, height=20, width=10):
		self.height = height
		self.width = width
		self.empty_line = [' ' for i in range(self.width)]
		self.board = [deepcopy(self.empty_line) for i in range(self.height)]
		self.cleared = 0

		self.bag = Piece_Bag()
		self.active_piece = self.bag.next()
		self.next_piece = self.bag.next()
		self.hold_piece = None

	### BOARD ###
	def draw_piece(self,depth,ghost=False):
		if not ghost:
			sym = FULL_CHR
		else:
			sym = GHOST_CHR


		new_board = deepcopy(self.board)
		for i in range(len(self.active_piece.grid)):
			for j in range(len(self.active_piece.grid[i])):
				if self.active_piece.grid[i][j] == 0:
					continue
				y = depth + i
				x = self.active_piece.x + j

				# Maybe not the best way to do this
				if new_board[y][x] == FULL_CHR:
					raise RuntimeError

				new_board[y][x] = sym
		return new_board

	# Return a new board with the dropped piece
	def drop_piece(self,ghost=False):
		# new_board = self.board
		# for i in range(self.height):
		for i in range(height):
			try:
				new_board = self.draw_piece(i, ghost)
			except Exception as e:
				pass
		return new_board


	def clear_full_lines(self):
		for index in range(self.height):
			if self.board[index] == FULL_LINE:
				del(self.board[index])
				self.board.insert(0, deepcopy(EMPTY_LINE))
				self.cleared += 1
	### BOARD ###

	### PIECE ###

	def move_piece_left(self):
		self.active_piece.move(-1)

	def move_piece_right(self):
		self.active_piece.move(1)

	def rotate_piece(self):
		self.active_piece.rotate()

	def hold_piece(self):
		self.active_piece
		if self.hold_piece == None:
			self.hold_piece = self.active_piece
			self.get_new_piece()
		else:
			self.active_piece, self.hold_piece = self.hold_piece, self.active_piece

	def get_new_piece(self):
		self.active_piece = self.next_piece
		self.next_piece = self.bag.next()

	def hard_drop(self):
		self.board = self.drop_piece()
		self.get_new_piece()
		self.clear_full_lines()


	### PIECE ###

def print_screen(win, board):
	# Print row by row
	for i in range(height):
		win.addstr(i,0, "".join([" "] + board[i]))
	win.box()
	win.refresh()

def main(stdscr):
	curses.curs_set(False)
	stdscr.clear()
	key = ''

	game = Tetris_Engine()

	board_win = curses.newwin(height+1, width+2, 0, 0)
	stdscr.refresh()

	while(True):
		out_board = game.drop_piece(ghost=True)
		print_screen(board_win, out_board)

		stdscr.addstr(0,0,str(key))
		key = stdscr.getch()
		if key == curses.KEY_UP or key == curses.KEY_DOWN:
			game.rotate_piece()
		elif key == curses.KEY_RIGHT:
			game.move_piece_right()
		elif key == curses.KEY_LEFT:
			game.move_piece_left()
		elif key == ord(' '):
			game.hard_drop()
		if key == ord('q'):
			break
		

if __name__ == "__main__":
	curses.wrapper(main)