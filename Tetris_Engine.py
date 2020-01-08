from time import sleep
from copy import deepcopy
from queue import deque
from random import shuffle

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
		self.grid = PIECE_INDEX[index]
		self.width = len(self.grid[0])

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
		self.reset_coords()
		self.active_piece = self.bag.next()
		self.next_piece = self.bag.next()
		self.hold_piece = None
		self.can_hold = True

		# New drop mechanics
		self.interval = 30
		self.ticks_elapsed = 0

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
		if not self.position_valid(self.x - 1, self.y, self.active_piece):
			return False	

		self.x -= 1
		return True

	def move_piece_right(self):
		if not self.position_valid(self.x + 1, self.y, self.active_piece):
			return False
		
		self.x += 1
		return True

	def move_piece_down(self):
		if not self.position_valid(self.x, self.y+1, self.active_piece):
			return False
		
		self.y += 1
		return True


	# NOTE - Very weird behavior when colliding
	def rotate_piece(self):
		active_piece_copy = deepcopy(self.active_piece)
		active_piece_copy.rotate()
		acceptable_distance = max(self.active_piece.width, active_piece_copy.width)
		for i in range(acceptable_distance):
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

		self.ticks_elapsed = 0

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

	### GAMEPLAY ###
	
	def tick(self):
		self.ticks_elapsed += 1
		if self.ticks_elapsed >= self.interval:
			self.ticks_elapsed = 0
			if not self.move_piece_down():
				self.hard_drop()

	### GAMEPLAY ###