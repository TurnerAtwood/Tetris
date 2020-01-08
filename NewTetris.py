from Tetris_Engine import Tetris_Engine,height,width

import pynput

from time import sleep
from copy import deepcopy
from queue import deque
from random import shuffle
import curses

KEYS = dict()

def print_screen(win, board):
	# Print row by row
	for i in range(height):
		win.addstr(i+1,0, "".join([" "] + board[i]))
	win.box()
	win.refresh()

""" KEYBOARD CONTROLLER """

# Callback for the listener
def on_press(key):
	global KEYS
	try:
		key = key.char
	except AttributeError:
		key = str(key)

	# What to do if key in KEYS?
	if not key in KEYS:
		KEYS[key] = 0

def on_release(key):
	global KEYS
	try:
		key = key.char
	except AttributeError:
		key = str(key)

	if key in KEYS:
		del(KEYS[key])


class Tetris_Keyboard():
	def __init__(self, engine):
		self.engine = engine

		self.listener = None
		self.start_listener()

	def start_listener(self):
		if self.listener != None:
			raise RuntimeError("You don't need more than one listener!")
		self.listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
		self.listener.start()

	def __del__(self):
		if not self.listener == None:
			self.listener.stop()
			self.listener.join()
			self.listener = None

	# Reads key and makes calls to the engine
	def tick(self):
		global KEYS

		self.engine.tick()

		if 'q' in KEYS:
			return False

		for key in KEYS:
			KEYS[key] += 1
			if (KEYS[key]%5 != 1):
				continue


			if key == 'Key.up':
				self.engine.rotate_piece()
			elif key == 'Key.down':
				self.engine.move_piece_down()
			elif key == 'Key.right':
				self.engine.move_piece_right()
			elif key == 'Key.left':
				self.engine.move_piece_left()
			elif key == 'Key.space':
				self.engine.hard_drop()
			elif key == ord('c'):
				self.engine.hold()
		return True


""" KEYBOARD CONTROLLER """

def main(stdscr):
	
	game = Tetris_Engine()
	keyboard = Tetris_Keyboard(game)

	curses.curs_set(False)
	curses.noecho()
	stdscr.clear()

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

		keep_going = keyboard.tick()
		if not keep_going:
			break
		sleep(1/60.0)

	print("DYING")
	del(keyboard)


if __name__ == "__main__":
	curses.wrapper(main)
