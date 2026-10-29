"""Launch the supplied Project 3 keyboard game from any working directory.

Examples:
    python3 play_gui.py
    python3 play_gui.py --layout smallHunt --fixed-seed
    python3 play_gui.py --layout bigHunt --show-ghosts

The demo uses demoInference.py; Q1-Q4 remain separately tested inference tasks.
Based on the supplied Berkeley Pacman framework: http://ai.berkeley.edu.
"""
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Play Project 3 Ghostbusters with arrow keys or WASD.')
    parser.add_argument('--layout', choices=('oneHunt', 'smallHunt', 'openHunt', 'bigHunt'), default='oneHunt')
    parser.add_argument('--frame-time', type=float, default=0.15, help='Seconds per frame (positive).')
    parser.add_argument('--ghosts', type=int, default=4, help='Maximum number of ghosts (1-4).')
    parser.add_argument('--zoom', type=float, default=1.0)
    parser.add_argument('--fixed-seed', action='store_true')
    parser.add_argument('--show-ghosts', action='store_true', help='Reveal ghosts for a teaching demonstration.')
    parser.add_argument('--close-on-finish', action='store_true',
                        help='Close automatically instead of keeping the final board visible.')
    options = parser.parse_args()
    if options.frame_time <= 0 or options.zoom <= 0 or not 1 <= options.ghosts <= 4:
        parser.error('Use a positive frame time and zoom, and 1-4 ghosts.')
    # The starter loads layouts and agents relative to the working directory.
    os.chdir(Path(__file__).resolve().parent)
    try:
        import tkinter
    except ImportError as error:
        raise SystemExit('This game needs a Python installation with Tk support. Use the Python.org macOS installer.') from error
    import busters
    args = ['-l', options.layout, '-t', str(options.frame_time),
            '-k', str(options.ghosts), '-z', str(options.zoom)]
    if options.fixed_seed:
        args.append('-f')
    if options.show_ghosts:
        args.append('-s')
    print('Arrow keys or WASD: move. Q: stop. Close the game window to exit.')
    print('Hunt the invisible ghosts using the colored cells and noisy distance readings.')
    game = busters.readCommand(args)
    if not options.close_on_finish:
        import graphicsUtils
        display = game['display']
        original_finish = display.finish

        def finish_after_click():
            # Keep the final board visible, matching the Project 2 launcher.
            graphicsUtils._leftclick_loc = None
            graphicsUtils._rightclick_loc = None
            graphicsUtils._ctrl_leftclick_loc = None
            print('Game over. Click the Pac-Man window to close it.')
            graphicsUtils.wait_for_click()
            original_finish()

        display.finish = finish_after_click
    busters.runGames(**game)


if __name__ == '__main__':
    main()
