import time
from copy import deepcopy
from queue import deque
from random import shuffle, randint

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

class Tetris_Engine():

	def __init__(self, height=20, width=10, game_mode=0):
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
		self.time_at_last_unpause = time.time()
		self.total_time_past_segments = 0

		# Rubber is the grace period (in ticks) for the active block hitting the bottom
		self.rubber = 5

		# Game mode variables
		# (0, Sprint), (1, Marathon), (2, Cheese Race)
		self.game_mode = game_mode
		self.original_drop_interval = self.drop_interval
		self.cheese_line = [8 for i in range(self.width)]
		self.cheese_height = 8
		self.cheese_left = 20
		if game_mode == 2:
			self.cheese_init()

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
		new_board = False
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
				self.cleared += 1

				# Normal line replacement (blank line at the top)
				if self.game_mode != 2 or self.cheese_left == 0 or index < self.height - self.cheese_height:
					self.board.insert(0, deepcopy(self.empty_line))

					# Cheese height needs to go to zero when there is none left on the board
					if self.game_mode == 2 and self.cheese_left == 0:
						self.cheese_height = min(self.cheese_height, self.height - index - 1)
				
				# Cheese race line replacement (new cheese at the bottom)
				else:
					self.board.insert(-1, self.make_cheese_line())
					# Cheese left is zero when we are done putting it on the board
					self.cheese_left = max(0, self.cheese_left - 1)
					

		# MARATHON SPEEDUP (speed up every 10 lines)
		if (self.game_mode == 1):
			if (self.cleared < 120):
				self.drop_interval = max(4, self.original_drop_interval - 3 * (self.cleared//10))
			elif (self.cleared < 150):
				self.drop_interval = 3
			else:
				self.drop_interval = 2

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
		if not ghost_board or not piece_board:
			return self.board

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
	def rotate_piece(self, clockwise=True):
		if self.paused:
			return False
		active_piece_copy = deepcopy(self.active_piece)
		active_piece_copy.rotate()
		if not clockwise:
			active_piece_copy.rotate()
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
			return True

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
	
	def tick(self):
		# The active piece can only be invalid on spawn, so this is game over
		if not self.position_valid(self.x, self.y, self.active_piece):
			return False

		# Sprint ends at 40 lines
		if self.game_mode == 0 and self.cleared >= 40:
			return False

		# Cheese race ends when the cheese_height hits 0
		if self.cheese_height == 0:
			return False

		if self.paused:
			return True

		self.ticks_elapsed += 1
		if self.ticks_elapsed >= self.drop_interval:
			if self.move_piece_down():
				self.ticks_elapsed = 0
			elif self.ticks_elapsed >= self.drop_interval + self.rubber:
				self.hard_drop()
		return True
	
	def pause_toggle(self):
		current_time = time.time()
		if self.paused:
			self.time_at_last_unpause = current_time
		else:
			self.total_time_past_segments += (current_time - self.time_at_last_unpause)
		self.paused = not self.paused

	def time_elapsed(self):
		if self.paused:
			return self.total_time_past_segments
		else:
			current_time = time.time()
			return self.total_time_past_segments + (current_time - self.time_at_last_unpause)

	# Fill the (empty) board with cheese up to the cheese
	def cheese_init(self):
		for i in range(-1,-1*self.cheese_height-1, -1):
			if self.cheese_left > 0:
				self.board[i] = self.make_cheese_line()
				self.cheese_left -= 1
			else:
				break

	# Return a line with one (1) random empty spot
	def make_cheese_line(self):
		cheese_line = [1 for i in range(self.width)]
		blank_spot = randint(0, self.width-1)
		cheese_line[blank_spot] = 0
		return cheese_line

	### GAMEPLAY ###