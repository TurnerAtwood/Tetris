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
	[[1,1,1,1]],
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
		self.index = index
		self.x = width//2
		self.y = 0
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

	def __repr__(self):
		out = [[' ' for j in range(5)] for i in range(4)]
		for i in range(len(self.grid)):
			for j in range(self.width):
				if self.grid[i][j]:
					out[i][j+1] = FULL_CHR
		out = "\n".join(["".join(i) for i in out])
		return out
		


class Tetris_Engine():

	def __init__(self, height=20, width=10):
		self.height = height
		self.width = width
		self.empty_line = [' ' for i in range(self.width)]
		self.board = [deepcopy(self.empty_line) for i in range(self.height)]
		self.cleared = 0

		self.bag = Piece_Bag()
		self.active_piece = self.bag.next()
		self.reset_coords()
		self.next_piece = self.bag.next()
		self.hold_piece = None
		self.can_hold = True

	### BOARD ###
	# Draw the active piece onto the board (if valid)

	def draw_piece(self, x, y, ghost=False):
		if not self.position_valid(x, y, self.active_piece):
			return False

		if ghost:
			sym = GHOST_CHR
		else:
			sym = FULL_CHR

		new_board = deepcopy(self.board)
		for i in range(len(self.active_piece.grid)):
			for j in range(len(self.active_piece.grid[i])):
				if self.active_piece.grid[i][j] == 1:
					new_board[y+i][x+j] = sym
		return new_board

	# Return a new board with the dropped piece
	def drop_piece(self,ghost=False):
		new_board = self.board
		for i in range(self.height):
			if not self.position_valid(self.x, self.y+i, self.active_piece):
				break
			new_board = self.draw_piece(self.x, self.y+i, ghost)
		if new_board:
			return new_board
		raise Exception 


	def clear_full_lines(self):
		for index in range(self.height):
			if self.board[index] == FULL_LINE:
				del(self.board[index])
				self.board.insert(0, deepcopy(EMPTY_LINE))
				self.cleared += 1

	# IOoB Error --> Clearly not valid
	def position_valid(self, x, y, piece):
		# Check left/right
		if x < 0 or x > self.width - piece.width:
			return False

		# Check Height
		if y < 0 or y > self.height - len(piece.grid):
			return False

		for i in range(len(piece.grid)):
			for j in range(len(piece.grid[i])):
				if piece.grid[i][j] == 0:
					continue
				if self.board[y+i][x+j] == FULL_CHR:
					return False
		return True

	# Draw the board + ghost + active piece
	# UPDATE THIS 
	def draw_full_board(self):
		ghost_board = self.drop_piece(ghost=True)
		piece_board = self.draw_piece(self.x, self.y)
		for i in range(self.height):
			for j in range(self.width):
				if piece_board[i][j] != ' ':
					ghost_board[i][j] = piece_board[i][j]
		return ghost_board

	### BOARD ###

	### PIECE ###

	def move_piece_left(self):
		if self.position_valid(self.x - 1, self.y, self.active_piece):
			self.x -= 1

	def move_piece_right(self):
		if self.position_valid(self.x + 1, self.y, self.active_piece):
			self.x += 1

	def move_piece_down(self):
		if self.position_valid(self.x, self.y+1, self.active_piece):
			self.y += 1


	# NOTE - Very weird behavior when colliding
	def rotate_piece(self):
		active_piece_copy = deepcopy(self.active_piece)
		active_piece_copy.rotate()
		for i in range(active_piece_copy.width):
			if self.position_valid(self.x+i, self.y, active_piece_copy):
				self.active_piece = active_piece_copy
				self.x += i
				break
			if self.position_valid(self.x-i, self.y, active_piece_copy):
				self.active_piece = active_piece_copy
				self.x -= i
				break

	def get_new_piece(self):
		self.active_piece = self.next_piece
		self.next_piece = self.bag.next()
		self.reset_coords()

	def reset_coords(self):
		self.x = self.width//2
		self.y = 0

	def hard_drop(self):
		self.can_hold = True
		self.board = self.drop_piece()
		self.get_new_piece()
		self.clear_full_lines()

	def hold(self):
		if not self.can_hold:
			return
		self.can_hold = False

		self.active_piece = piece(self.active_piece.index)
		if self.hold_piece == None:
			self.hold_piece = self.active_piece
			self.get_new_piece()
		else:
			self.hold_piece, self.active_piece = self.active_piece, self.hold_piece
		self.reset_coords()

	### PIECE ###

def print_screen(win, board):
	# Print row by row
	for i in range(height):
		win.addstr(i+1,0, "".join([" "] + board[i]))
	win.box()
	win.refresh()

def main(stdscr):
	curses.curs_set(False)
	stdscr.clear()
	key = ''

	game = Tetris_Engine()

	board_win = curses.newwin(height+2, width+2, 0, 0)
	stdscr.refresh()

	next_piece_win = curses.newwin(6,6,1,12)
	hold_piece_win = curses.newwin(6,6,8,12)


	while(True):
		out_board = game.draw_full_board()
		print_screen(board_win, out_board)

		next_piece_win.addstr(1,0, str(game.next_piece))
		next_piece_win.box()
		next_piece_win.refresh()

		hold_piece_win.addstr(1,0, str(game.hold_piece))
		hold_piece_win.box()
		hold_piece_win.refresh()

		stdscr.addstr(0,0,str(game.cleared))

		key = stdscr.getch()
		if key == curses.KEY_UP:
			game.rotate_piece()
		elif key == curses.KEY_DOWN:
			game.move_piece_down()
		elif key == curses.KEY_RIGHT:
			game.move_piece_right()
		elif key == curses.KEY_LEFT:
			game.move_piece_left()
		elif key == ord(' '):
			game.hard_drop()
		elif key == ord('c'):
			game.hold()
		elif key == ord('q'):
			break
		

if __name__ == "__main__":
	curses.wrapper(main)