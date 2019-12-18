from time import sleep
from enum import Enum
from copy import deepcopy
from queue import deque
from random import shuffle
import curses

PIECE_INDEX = [
	('I',[[1,1,1,1]]),
	('J',[[1,0,0],[1,1,1]]),
	('L',[[0,0,1],[1,1,1]]),
	('O',[[1,1],[1,1]]),
	('S',[[0,1,1],[1,1,0]]),
	('T',[[0,1,0],[1,1,1]]),
	('Z',[[1,1,0],[0,1,1]])]
NUM_PIECES = len(PIECE_INDEX)

height = 20
width = 10
FULL_LINE  = ['*' for i in range(width)]
EMPTY_LINE = ['.' for i in range(width)]

SORTED_DOUBLE_BAG = [i%NUM_PIECES for i in range(2*NUM_PIECES)]

class double_bag():
	def __init__(self):
		self.bag = deque()
		self.fill_bag()

	def fill_bag(self):
		clean_bag = deepcopy(SORTED_DOUBLE_BAG)
		shuffle(clean_bag)
		self.bag.extend(clean_bag)

	def next(self):
		if len(self.bag) < 7:
			self.fill_bag()
		return self.bag.popleft()

class piece():

	def __init__(self, index):
		self.x = 0
		self.name, self.grid = PIECE_INDEX[index]
		self.width = len(self.grid[0])

	def get_width(self):
		w = 0
		for line in self.grid:
			w = max(w, len(line))
		return w

	# Rotate clockwise about the top-left corner
	# DEBUG - Doesn't act natural on right edge
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

# Throw exception on collision
def draw_piece(board,piece,depth,ghost=False):
	if not ghost:
		sym = '*'
	else:
		sym = 'X'


	new_board = deepcopy(board)
	for i in range(len(piece.grid)):
		for j in range(len(piece.grid[i])):
			if piece.grid[i][j] == 0:
				continue
			y = depth + i
			x = piece.x + j

			# Maybe not the best way to do this
			if new_board[y][x] == "*":
				raise RuntimeError

			new_board[y][x] = sym
	return new_board

# Return a new board with the dropped piece
def drop_piece(board,piece,ghost=False):
	for i in range(height):
		try:
			new_board = draw_piece(board, piece, i, ghost)
		except:
			break
	return new_board

# Testing Curses

def print_screen(stdscr, board):
	# Print row by row
	for i in range(height):
		stdscr.addstr(curses.LINES-height+i,0, "".join(board[i]))
	stdscr.refresh()


# Edit the board with full lines removed
#  Return how many lines where cleared
def clear_full_lines(board):
	cleared = 0
	for index in range(height):
		if board[index] == FULL_LINE:
			del(board[index])
			board.insert(0, deepcopy(EMPTY_LINE))
			cleared += 1
	return cleared

def main(stdscr):
	curses.curs_set(False)
	stdscr.clear()
	key = ''

	bag = double_bag()
	game_piece = piece(bag.next())

	board = [deepcopy(EMPTY_LINE) for i in range(height)]
	score = 0
	while(True):
		out_board = drop_piece(board, game_piece, ghost=True)
		print_screen(stdscr, out_board)
		stdscr.refresh()

		key = stdscr.getch()
		stdscr.addstr(0,0,str(key))
		if key == curses.KEY_UP or key == curses.KEY_DOWN:
			game_piece.rotate()
		elif key == curses.KEY_RIGHT:
			game_piece.move(1)
		elif key == curses.KEY_LEFT:
			game_piece.move(-1)
		elif key == ord(' '):
			board = drop_piece(board, game_piece)
			game_piece = piece(bag.next())
		if key == ord('q'):
			break
		score = clear_full_lines(board)

if __name__ == "__main__":
	curses.wrapper(main)