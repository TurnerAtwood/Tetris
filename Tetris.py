from Tetris_Engine import Tetris_Engine

from time import sleep
import curses
import pynput

FULL_CHR = chr(int('2588',16))
HEIGHT = 20
WIDTH = 10

# This global is modified by the listener callbacks
#  The keyboard updates its active keys based on PASSED every tick
PRESSED = set()

def print_screen(win, board):
	height = len(board)
	width = len(board[0])
	for i in range(height):

		for j in range(width):
			value = board[i][j]
			attr = curses.color_pair(value%10)
			if not value:
				sym = " "
			elif value < 10:
				sym = FULL_CHR
			else:
				attr = attr | curses.A_TOP
				sym = "X"

			win.addstr(i+1, j+1, sym, attr)

	win.refresh()

def format_piece(piece):
	result = [[0 for j in range(4)] for i in range(4)]
	if piece == None:
		return result

	for i in range(len(piece.grid)):
		for j in range(piece.width):
			result[i][j] = piece.grid[i][j]
	return result

""" KEYBOARD CONTROLLER """

# Callbacks for the listener
def on_press(key):
	global PRESSED
	try:
		key = key.char
	except AttributeError:
		key = str(key)

	PRESSED.add(key)

def on_release(key):
	global PRESSED
	try:
		key = key.char
	except AttributeError:
		key = str(key)

	if key in PRESSED:
		PRESSED.remove(key)


class Tetris_Keyboard():
	def __init__(self, engine):
		self.engine = engine

		self.keys = dict()
		self.listener = None
		self.start_listener()

	def start_listener(self):
		if self.listener != None:
			raise RuntimeError("You don't need more than one listener!")
		self.listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
		self.listener.start()

	def stop_listener(self):
		if not self.listener == None:
			self.listener.stop()
			self.listener.join()
			self.listener = None

	def __del__(self):
		self.stop_listener()

	# Updates active keys and makes relevant calls to the engine
	def tick(self):
		# Add all newly pressed keys to our active key dict
		for key in PRESSED:
			if key not in self.keys:
				self.keys[key] = 0

		# Quit if 'p' is pressed or if the game ends
		keep_going = self.engine.tick() and not 'q' in PRESSED
		if not keep_going:
			return False

		# Remove all keys that have been released
		remove = {i for i in self.keys if i not in PRESSED}
		for key in remove:
			del(self.keys[key])

		# Take relevant actions for all active keys
		for key in self.keys:
			self.keys[key] += 1

			if key == 'Key.up' or key == 'x':
				if self.keys[key]%12 == 1:
					self.engine.rotate_piece()
			elif key == 'z':
				if self.keys[key]%12 == 1:
					self.engine.rotate_piece(clockwise = False)
			elif key == 'Key.down':
				if self.keys[key] == 1 or (self.keys[key] > 7 and self.keys[key]%3 == 1):
					self.engine.move_piece_down()
			elif key == 'Key.right':
				if self.keys[key] == 1 or (self.keys[key] > 7 and self.keys[key]%2 == 1):
					self.engine.move_piece_right()
			elif key == 'Key.left':
				if self.keys[key] == 1 or (self.keys[key] > 7 and self.keys[key]%2 == 1):
					self.engine.move_piece_left()
			elif key == 'Key.space':
				if self.keys[key] == 1 or (self.keys[key] > 12 and self.keys[key]%2 == 1):
					self.engine.hard_drop()
			elif key == 'c':
				if self.keys[key] == 1:
					self.engine.hold()
			elif key == 'p':
				if self.keys[key] == 1:
					self.engine.pause_toggle()
		return True


""" KEYBOARD CONTROLLER """

def main(stdscr):
	game = Tetris_Engine()
	keyboard = Tetris_Keyboard(game)

	curses.curs_set(False)
	stdscr.nodelay(True)
	stdscr.clear()

	# COLOR PALATES FOR PIECES
	curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(7, curses.COLOR_RED, curses.COLOR_BLACK)

	# Initialize windows
	board_win = curses.newwin(HEIGHT+2, WIDTH+2, 2, 0)
	board_win.box()
	stdscr.addstr(3,12, "Next:")
	next_piece_win = curses.newwin(6,6,4,12)
	next_piece_win.box()
	stdscr.addstr(11,12, "Hold:")
	hold_piece_win = curses.newwin(6,6,12,12)
	hold_piece_win.box()

	while(True):
		# Have curses eat the inputs
		stdscr.getch()

		print_screen(board_win, game.draw_full_board())
		print_screen(next_piece_win, format_piece(game.next_piece))
		print_screen(hold_piece_win, format_piece(game.hold_piece))

		stdscr.addstr(0, 0, "Cleared: " + str(game.cleared))
		time_ms = int(game.time_elapsed()*100)
		stdscr.addstr(1, 0, "Time: " + f"{time_ms//6000:02d}:{(time_ms//100)%60:02d}:{time_ms%100:02d}")

		keep_going = keyboard.tick()
		if not keep_going:
			break
		sleep(1/60.0)

	stdscr.getch()
	del(keyboard)

if __name__ == "__main__":
	curses.wrapper(main)
