"""
Test file for improved deadlock detection
This file is used to test and validate deadlock improvements
without affecting the main test.py
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
import heapq
import time
import tracemalloc
import gc

# Test cases for deadlock validation
test_cases = {
    "simple": [
        "#######",
        "#     #",
        "# $# ##",
        "#    .#",
        "# @# ##",
        "#######"
    ],
    "medium": [
        "#### ####",
        "#  ###  #",
        "# $ * $ #",
        "#   +   #",
        "### .$###",
        "  # . #  ",
        "  #####  "
    ]
    # ],
    # "complex": [
    #     "#########",
    #     "#####   #",
    #     "## $ $  #",
    #     "##.# #. #",
    #     "## $@$  #",
    #     "##.# #. #",
    #     "#       #",
    #     "#   #   #",
    #     "#########"
    # ]
}

direction = ['up', 'down', 'left', 'right']

def render_map(walls, boxes, player, goal, map_width, map_height):
    map_template = [[' ' for _ in range(map_width)] for _ in range(map_height)]
    new_map = [list(row) for row in map_template]
    for (x, y) in walls: 
        new_map[y][x] = '#'
    for (x, y) in goal: new_map[y][x] = '.'
    for (x, y) in boxes:
        new_map[y][x] = '*' if (x, y) in goal else '$'
    px, py = player
    new_map[py][px] = '+' if (px, py) in goal else '@'
    return [''.join(row) for row in new_map]

def is_corner_deadlock(x, y, walls, goals):
    """Perfect implementation - no changes needed"""
    if (x, y) in goals: 
        return False
    left_wall = (x-1, y) in walls
    right_wall = (x+1, y) in walls
    up_wall = (x, y-1) in walls
    down_wall = (x, y+1) in walls
    return (left_wall or right_wall) and (up_wall or down_wall)

def is_edge_deadlock_improved(x, y, walls, goals):
    """
    IMPROVED Edge deadlock detection - CONSERVATIVE VERSION
    
    Only detect edge deadlock when box is TRULY trapped:
    - Box must be against a wall along entire corridor length
    - NO openings/exits from the corridor  
    - NO goals in the corridor
    
    This is more conservative to avoid false positives.
    
    Returns True if deadlock detected, False otherwise.
    """
    if (x, y) in goals:
        return False
    
    left_wall = (x - 1, y) in walls
    right_wall = (x + 1, y) in walls
    up_wall = (x, y - 1) in walls
    down_wall = (x, y + 1) in walls
    
    # Check if this is a corner (handled by corner_deadlock)
    if (left_wall and right_wall) or (up_wall and down_wall):
        return False  # Corner, not edge
    
    # Helper: Check vertical corridor with NO escapes
    def is_vertical_corridor_fully_blocked(x, y, walls, goals):
        """
        Returns True only if:
        1. Box is against vertical wall along ENTIRE corridor
        2. No horizontal exits available 
        3. No goals in corridor
        """
        # Determine which side has wall
        wall_on_left = (x - 1, y) in walls
        wall_on_right = (x + 1, y) in walls
        
        if not (wall_on_left or wall_on_right):
            return False  # No vertical wall
        
        # Scan up to find boundary
        y_top = y
        while (x, y_top - 1) not in walls:
            y_top -= 1
            # Check if wall continues along corridor
            if wall_on_left and (x - 1, y_top) not in walls:
                return False  # Opening on left
            if wall_on_right and (x + 1, y_top) not in walls:
                return False  # Opening on right
        
        # Scan down to find boundary
        y_bottom = y
        while (x, y_bottom + 1) not in walls:
            y_bottom += 1
            # Check if wall continues along corridor
            if wall_on_left and (x - 1, y_bottom) not in walls:
                return False  # Opening on left
            if wall_on_right and (x + 1, y_bottom) not in walls:
                return False  # Opening on right
        
        # Check if any goal in corridor
        for yy in range(y_top, y_bottom + 1):
            if (x, yy) in goals:
                return False
        
        # Truly blocked corridor with no goals
        return True
    
    # Helper: Check horizontal corridor with NO escapes
    def is_horizontal_corridor_fully_blocked(x, y, walls, goals):
        """
        Returns True only if:
        1. Box is against horizontal wall along ENTIRE corridor
        2. No vertical exits available
        3. No goals in corridor
        """
        # Determine which side has wall
        wall_on_top = (x, y - 1) in walls
        wall_on_bottom = (x, y + 1) in walls
        
        if not (wall_on_top or wall_on_bottom):
            return False  # No horizontal wall
        
        # Scan left to find boundary
        x_left = x
        while (x_left - 1, y) not in walls:
            x_left -= 1
            # Check if wall continues along corridor
            if wall_on_top and (x_left, y - 1) not in walls:
                return False  # Opening on top
            if wall_on_bottom and (x_left, y + 1) not in walls:
                return False  # Opening on bottom
        
        # Scan right to find boundary
        x_right = x
        while (x_right + 1, y) not in walls:
            x_right += 1
            # Check if wall continues along corridor
            if wall_on_top and (x_right, y - 1) not in walls:
                return False  # Opening on top
            if wall_on_bottom and (x_right, y + 1) not in walls:
                return False  # Opening on bottom
        
        # Check if any goal in corridor
        for xx in range(x_left, x_right + 1):
            if (xx, y) in goals:
                return False
        
        # Truly blocked corridor with no goals
        return True
    
    # Vertical edge: wall on left OR right (but not both)
    if (left_wall or right_wall) and not (left_wall and right_wall):
        if is_vertical_corridor_fully_blocked(x, y, walls, goals):
            return True
    
    # Horizontal edge: wall on top OR bottom (but not both)  
    if (up_wall or down_wall) and not (up_wall and down_wall):
        if is_horizontal_corridor_fully_blocked(x, y, walls, goals):
            return True
    
    return False

def is_block_2x2_deadlock(x, y, boxes, walls, goals):
    """Perfect implementation - no changes needed"""
    if (x, y) in goals:
        return False

    # 4 possible 2x2 squares containing (x, y)
    offsets = [(0, 0), (-1, 0), (0, -1), (-1, -1)]
    for dx, dy in offsets:
        square = [
            (x + dx, y + dy),
            (x + dx + 1, y + dy),
            (x + dx, y + dy + 1),
            (x + dx + 1, y + dy + 1)
        ]
        if all(pos in walls or pos in boxes for pos in square):
            # check if any goal inside → if yes, it's not deadlock
            if not any(pos in goals for pos in square):
                return True
    return False

class State:
    def __init__(self, map, boxes, walls, player, goal, path):
        self.map = map
        self.boxes = boxes
        self.walls = walls
        self.player = player
        self.goal = goal
        self.path = path

    def __eq__(self, other):
        return isinstance(other, State) and self.player == other.player and set(self.boxes) == set(other.boxes)

    def __hash__(self):
        return hash((self.player, tuple(sorted(self.boxes))))

    def is_win(self, goal):
        return set(goal).issubset(set(self.boxes))

    def is_deadlock(self, use_edge=True):
        """
        Deadlock detection with option to enable/disable edge detection
        """
        for (x, y) in self.boxes:
            if is_corner_deadlock(x, y, self.walls, self.goal):
                return True
            
            if use_edge:
                if is_edge_deadlock_improved(x, y, self.walls, self.goal):
                    return True
            
            if is_block_2x2_deadlock(x, y, self.boxes, self.walls, self.goal):
                return True
        return False

    def explore_neighbors(self):
        neighbors = []
        for dir in direction:
            new_state = self.move(dir)
            if new_state is not None:
                neighbors.append(new_state)
        return neighbors

    def move(self, direction):
        new_boxes = self.boxes.copy()  
        new_player = self.player

        if (direction == "up"):
            new_player = (new_player[0], new_player[1] - 1)
        elif (direction == "down"):
            new_player = (new_player[0], new_player[1] + 1)
        elif (direction == "left"):
            new_player = (new_player[0] - 1, new_player[1])
        elif (direction == "right"):
            new_player = (new_player[0] + 1, new_player[1])
        else:    
            return None
        
        if (self.walls.__contains__(new_player)):
            return None
        
        if (new_boxes.__contains__(new_player)):
            if (direction == "up"):
                new_box = (new_player[0], new_player[1] - 1)
            elif (direction == "down"):
                new_box = (new_player[0], new_player[1] + 1)
            elif (direction == "left"):
                new_box = (new_player[0] - 1, new_player[1])
            elif (direction == "right"):
                new_box = (new_player[0] + 1, new_player[1])

            if (self.walls.__contains__(new_box) or new_boxes.__contains__(new_box)):
                return None
            else:
                new_boxes.remove(new_player)
                new_boxes.append(new_box)
                new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))
                return State(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])
        
        new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))
        return State(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])

def test_bfs(init_state, goal, use_edge_deadlock=True):
    """BFS with option to enable/disable edge deadlock"""
    gc.collect()
    gc.collect()
    gc.collect()
    tracemalloc.start()
    
    start_time = time.time()
    generated_node = 0
    expand_node = 0
    revisited_node = 0
    
    queue = [init_state]
    visited = set()
    visited.add(init_state)

    while len(queue) != 0:
        current_state = queue.pop(0)
        expand_node += 1
        
        if current_state.is_win(goal):
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return {
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': peak / (1024 * 1024)
            }
        
        neighbors = current_state.explore_neighbors()
        
        for state in neighbors:
            generated_node += 1
            
            if state in visited:
                revisited_node += 1
                continue
            
            if state.is_deadlock(use_edge=use_edge_deadlock):
                continue
            
            queue.append(state)
            visited.add(state)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        'path': None,
        'expand_node': expand_node,
        'generated_node': generated_node,
        'revisited_node': revisited_node,
        'time_taken': end_time - start_time,
        'memory_used': peak / (1024 * 1024)
    }

if __name__ == "__main__":
    print("="*70)
    print("DEADLOCK DETECTION IMPROVEMENT TESTS")
    print("="*70)
    
    for test_name, test_map in test_cases.items():
        print(f"\n{'='*70}")
        print(f"Testing: {test_name.upper()}")
        print(f"{'='*70}")
        
        # Parse map
        init_boxes = []
        init_walls = []
        init_player = (0,0)
        init_goal = []
        for y, row in enumerate(test_map):
            for x, c in enumerate(row):
                if (c == '$' or c == '*'):
                    init_boxes.append((x, y))
                if (c == '.' or c == '*' or c == '+'):
                    init_goal.append((x, y))
                if (c == '@' or c == '+'):
                    init_player = (x, y)
                if (c == '#'): 
                    init_walls.append((x,y))
        
        init_state = State(test_map, init_boxes, init_walls, init_player, init_goal, [])
        
        # Print map
        for row in test_map:
            print(row)
        print()
        
        # Test WITHOUT edge deadlock
        print("Test 1: WITHOUT edge deadlock detection")
        print("-" * 70)
        result_no_edge = test_bfs(init_state, init_goal, use_edge_deadlock=False)
        
        if result_no_edge['path']:
            print(f"[SUCCESS] Solution found!")
            print(f"  Path length: {len(result_no_edge['path'])}")
            print(f"  Expanded: {result_no_edge['expand_node']}, Generated: {result_no_edge['generated_node']}")
            print(f"  Time: {result_no_edge['time_taken']:.4f}s, Memory: {result_no_edge['memory_used']:.2f}MB")
        else:
            print(f"[FAILED] No solution found")
            print(f"  Expanded: {result_no_edge['expand_node']}, Generated: {result_no_edge['generated_node']}")
        
        print()
        
        # Test WITH improved edge deadlock
        print("Test 2: WITH improved edge deadlock detection")
        print("-" * 70)
        result_with_edge = test_bfs(init_state, init_goal, use_edge_deadlock=True)
        
        if result_with_edge['path']:
            print(f"[SUCCESS] Solution found!")
            print(f"  Path length: {len(result_with_edge['path'])}")
            print(f"  Expanded: {result_with_edge['expand_node']}, Generated: {result_with_edge['generated_node']}")
            print(f"  Time: {result_with_edge['time_taken']:.4f}s, Memory: {result_with_edge['memory_used']:.2f}MB")
            
            # Compare with no-edge version
            if result_no_edge['path']:
                saved_nodes = result_no_edge['expand_node'] - result_with_edge['expand_node']
                speedup = result_no_edge['time_taken'] / result_with_edge['time_taken']
                print(f"\n  IMPROVEMENT:")
                print(f"    - Saved {saved_nodes} node expansions ({saved_nodes/result_no_edge['expand_node']*100:.1f}%)")
                print(f"    - Speedup: {speedup:.2f}x")
        else:
            print(f"[FAILED] No solution found (edge deadlock too aggressive!)")
            print(f"  Expanded: {result_with_edge['expand_node']}, Generated: {result_with_edge['generated_node']}")
        
        print()
    
    print("="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)
