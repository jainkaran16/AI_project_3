"""Integration tests for the supplied game, separate from Q1-Q4 grading.

Test drivers see ghost positions or initial routes solely to exercise the engine;
they are not player inference algorithms and are not used by the GUI launcher.
"""
from collections import deque
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import busters
import bustersAgents
import bustersGhostAgents
from game import Actions, Agent, Directions
import ghostAgents
import layout


def route_action(state, targets):
    start = state.getPacmanPosition()
    queue = deque([(start, Directions.STOP)])
    seen = {start}
    walls = state.getWalls()
    while queue:
        pos, first = queue.popleft()
        if pos in targets:
            return first
        for action in (Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST):
            dx, dy = Actions.directionToVector(action)
            nxt = (int(pos[0]+dx), int(pos[1]+dy))
            if 0 <= nxt[0] < walls.width and 0 <= nxt[1] < walls.height and not walls[nxt[0]][nxt[1]] and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, action if pos == start else first))
    raise AssertionError('A living ghost is unreachable.')


class CheckingDisplay(bustersAgents.NullGraphics):
    def __init__(self): self.frames, self.belief_updates, self.finished = 0, 0, False
    def update(self, data):
        self.frames += 1
        for i, distance in enumerate(data.ghostDistances, 1):
            if distance is None:
                assert data.agentStates[i].getPosition() == (2*i-1, 1)
            else:
                assert distance >= 0
    def updateDistributions(self, beliefs):
        self.belief_updates += 1
        for distribution in beliefs:
            assert abs(sum(distribution.values()) - 1) < 1e-12 or not distribution
    def finish(self): self.finished = True


class KeyboardRouteDriver(bustersAgents.BustersKeyboardAgent):
    """Feed a fixed initial-ghost route through the real keyboard agent."""
    def registerInitialState(self, state):
        self.targets = [state.getGhostPosition(i) for i in range(1, state.getNumAgents())]
        super().registerInitialState(state)
    def chooseAction(self, state):
        while self.targets and state.getPacmanPosition() == self.targets[0]: self.targets.pop(0)
        desired = route_action(state, {self.targets[0]}) if self.targets else Directions.STOP
        key = {Directions.NORTH:'w', Directions.SOUTH:'s', Directions.EAST:'d', Directions.WEST:'a', Directions.STOP:'q'}[desired]
        with patch('graphicsUtils.keys_waiting', return_value=[key]), patch('graphicsUtils.keys_pressed', return_value=[]):
            return super().chooseAction(state)


class VisibleGhostTestDriver(Agent):
    def getAction(self, state):
        targets = {state.getGhostPosition(i) for i in range(1, state.getNumAgents()) if state.getLivingGhosts()[i]}
        return route_action(state, targets)


class GameIntegrationTests(unittest.TestCase):
    def check_game(self, name, stationary):
        board = layout.getLayout(str(Path(__file__).resolve().parents[1]/'layouts'/f'{name}.lay'))
        self.assertIsNotNone(board)
        count = board.getNumGhosts()
        ghost_type = bustersGhostAgents.StationaryGhost if stationary else ghostAgents.RandomGhost
        ghosts = [ghost_type(i) for i in range(1,count+1)]
        player = KeyboardRouteDriver(ghostAgents=ghosts) if stationary else VisibleGhostTestDriver()
        display = CheckingDisplay()
        random.seed(537)
        games = busters.runGames(board, player, ghosts, display, 1, maxMoves=3000)
        game = games[0]
        self.assertTrue(game.state.isWin(), f'{name}: did not capture all ghosts')
        self.assertFalse(any(game.state.getLivingGhosts()))
        self.assertTrue(display.finished)
        self.assertGreater(display.frames, 0)
        self.assertTrue(any(index == 0 and action != Directions.STOP for index, action in game.moveHistory))
        if stationary: self.assertGreater(display.belief_updates,0)
        for i in range(1,count+1): self.assertEqual(game.state.getGhostPosition(i),(2*i-1,1))
        return game.state.numMoves

    def test_all_layouts_keyboard_path_capture_and_shading(self):
        results = {}
        for name in ['oneHunt','smallHunt','openHunt','bigHunt']:
            with self.subTest(layout=name): results[name] = self.check_game(name,True)
        print('Keyboard pipeline / stationary ghosts, winning move counts:',results)

    def test_all_layouts_random_ghosts_full_game(self):
        results = {}
        for name in ['oneHunt','smallHunt','openHunt','bigHunt']:
            with self.subTest(layout=name): results[name] = self.check_game(name,False)
        print('Engine / random ghosts, winning move counts:',results)


if __name__ == '__main__':
    unittest.main(verbosity=2)
