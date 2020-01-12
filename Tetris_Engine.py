from time import sleep
from copy import deepcopy
from queue import deque
from random import shuffle

PIECE_INDEX = [
	[[1,1,1,1]],
	[[2,0,0],[2,2,2]],
	[[0,0,3],[3,3,3]],
	[[4,4],[4,4]],
	[[0,5,5],[5,5,0]],
	[[0,6,0],[6,6,6]],
	[[7,7,0],[0,7,7]]]

NUM_PIECES = len(PIECE_INDEX)

class Piece_Bag():
	def __init__(self):
		self.bag = deque()
		self.fill_bag()

	def fill_bag(self):
		clean_bag = list(range(NUM_PIECES))
		shuffle(clean_bag)
		self.bag.extend(clean_bag)

	def next(self):
		if len(self.bag) < NUM_PIECES:
			self.fill_bag()
		new_piece_index = self.bag.popleft()
		new_piece = piece(new_piece_index)
		return new_piece

class piece():
	def __init__(self, index):
		self.index = index
		self.grid = PIECE_INDEX[index]
		self.width = len(self.grid[0])

	# Rotate clockwise
	def rotate(self):
		new_width = len(self.grid)
		new_grid = [[0 for i in range(new_width)] for i in range(self.width)]

		# Flip across main diag
		for i in range(len(self.grid)):
			for j in range(self.width):
				if self.grid[i][j]:
					new_grid[j][i] = self.index + 1

		self.grid = new_grid
		new_grid = [[0 for i in range(new_width)] for i in range(self.width)]

		# Flip across y-axis
		for i in range(len(new_grid)):
			for j in range(new_width):
				if self.grid[i][j]:
					new_grid[i][new_width-1-j] = self.index + 1

		self.grid = new_grid
		self.width = new_width

# DEBUG - What shold happen when  the player loses?
class Tetris_Engine():

	def __init__(self, height=20, width=10):
		self.height = height
		self.width = width
		self.empty_line = [0 for i in range(self.width)]
		self.board = [deepcopy(self.empty_line) for i in range(self.height)]
		self.cleared = 0

		self.bag = Piece_Bag()
		self.reset_coords()
		self.active_piece = self.bag.next()
		self.next_piece = self.bag.next()
		self.hold_piece = None
		self.can_hold = True

		# The piece will drop every 30 ticks (made for 60 TPS)
		self.drop_interval = 30
		self.ticks_elapsed = 0
		self.paused = False

	### BOARD ###

	# Draw the active piece onto the board (if valid)
	def draw_piece(self, x, y, ghost=False):
		if not self.position_valid(x, y, self.active_piece):
			return False

		new_board = deepcopy(self.board)
		for i in range(len(self.active_piece.grid)):
			for j in range(len(self.active_piece.grid[i])):
				if self.active_piece.grid[i][j]:
					new_board[y+i][x+j] = self.active_piece.grid[i][j]
					if ghost:
						new_board[y+i][x+j] += 10
		return new_board

	# Return a new board with the dropped piece
	# DEBUG - What if the current position is invalid?
	def drop_piece(self,ghost=False):
		new_board = self.board
		for i in range(self.height):
			if not self.position_valid(self.x, self.y+i, self.active_piece):
				break
			new_board = self.draw_piece(self.x, self.y+i, ghost)
		return new_board

	def clear_full_lines(self):
		for index in range(self.height):
			line = self.board[index]
			if 0 not in line:
				del(self.board[index])
				self.board.insert(0, deepcopy(self.empty_line))
				self.cleared += 1

	def position_valid(self, x, y, piece):
		# Check width bounds
		if x < 0 or x > self.width - piece.width:
			return False

		# Check height bounds
		if y < 0 or y > self.height - len(piece.grid):
			return False

		# Check only the solid parts of the piece against the current board
		for i in range(len(piece.grid)):
			for j in range(len(piece.grid[i])):
				if piece.grid[i][j] and self.board[y+i][x+j]:
					return False
		return True

	# Draw the board + ghost + active piece
	def draw_full_board(self):
		ghost_board = self.drop_piece(ghost=True)
		piece_board = self.draw_piece(self.x, self.y)

		# Draw the piece board over the ghost board
		for i in range(self.height):
			for j in range(self.width):
				if piece_board[i][j]:
					ghost_board[i][j] = piece_board[i][j]
		return ghost_board

	### BOARD ###

	### PIECE ###

	def move_piece_left(self):
		if self.paused or not self.position_valid(self.x - 1, self.y, self.active_piece):
			return False	

		self.x -= 1
		return True

	def move_piece_right(self):
		if self.paused or not self.position_valid(self.x + 1, self.y, self.active_piece):
			return False
		
		self.x += 1
		return True

	def move_piece_down(self):
		if self.paused or not self.position_valid(self.x, self.y+1, self.active_piece):
			return False
		
		self.y += 1
		return True


	# NOTE - Very weird behavior when colliding
	# DEBUG - This COULD result in teleporting through blocks
	def rotate_piece(self):
		if self.paused:
			return False
		active_piece_copy = deepcopy(self.active_piece)
		active_piece_copy.rotate()
		
		# Try nearby positions if needed (sometimes no change will be made)
		acceptable_distance = max(self.active_piece.width, len(self.active_piece.grid))
		for i in range(acceptable_distance):
			# Up
			if self.position_valid(self.x, self.y-i, active_piece_copy):
				self.active_piece = active_piece_copy
				self.y -= i
				return True
			# Right
			if self.position_valid(self.x+i, self.y, active_piece_copy):
				self.active_piece = active_piece_copy
				self.x += i
				return True
			# Left
			if self.position_valid(self.x-i, self.y, active_piece_copy):
				self.active_piece = active_piece_copy
				self.x -= i
				return True
		return False

	def get_new_piece(self):
		self.active_piece = self.next_piece
		self.next_piece = self.bag.next()
		self.reset_coords()
		self.ticks_elapsed = 0

	def reset_coords(self):
		self.x = self.width//2
		self.y = 0

	def hard_drop(self):
		if self.paused:
			return False

		self.can_hold = True
		self.board = self.drop_piece()
		self.get_new_piece()
		self.clear_full_lines()

	def hold(self):
		if self.paused or not self.can_hold:
			return False
		self.can_hold = False

		self.active_piece = piece(self.active_piece.index)
		if self.hold_piece == None:
			self.hold_piece = self.active_piece
			self.get_new_piece()
		else:
			self.hold_piece, self.active_piece = self.active_piece, self.hold_piece
		self.reset_coords()
		return True

	### PIECE ###

	### GAMEPLAY ###
	
	# DEBUG - Maybe add in a delay to give the player a chance to move at the bottom
	def tick(self):
		if self.paused:
			return False

		self.ticks_elapsed += 1
		if self.ticks_elapsed >= self.drop_interval:
			self.ticks_elapsed = 0
			if not self.move_piece_down():
				self.hard_drop()
		return True
	
	def pause_toggle(self):
		self.paused = not self.paused

	### GAMEPLAY ###