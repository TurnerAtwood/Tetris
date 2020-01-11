from Tetris_Engine import Tetris_Engine,height,width

import pynput

from time import sleep
from copy import deepcopy
from queue import deque
from random import shuffle
import curses

# GAME CONSTANTS
FPS = 60.0


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

	stdscr.nodelay(True)

	while(True):
		out_board = game.draw_full_board()
		print_screen(board_win, out_board)

		next_piece_win.addstr(1,0, str(game.next_piece))
		next_piece_win.box()
		next_piece_win.refresh()

		hold_piece_win.addstr(1,0, str(game.hold_piece))
		hold_piece_win.box()
		hold_piece_win.refresh()

		key = stdscr.getch()
		stdscr.addstr(0,0,str(game.cleared))


		game.tick()
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
		sleep(1/FPS)


if __name__ == "__main__":
	curses.wrapper(main)