from psutil import Process
import sys, time, psutil, os
import numpy as np
from scipy.optimize import linear_sum_assignment
import heapq

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
    if (x, y) in goals: 
        return False
    left_wall = (x-1, y) in walls
    right_wall = (x+1, y) in walls
    up_wall = (x, y-1) in walls
    down_wall = (x, y+1) in walls
    return (left_wall or right_wall) and (up_wall or down_wall)

def is_edge_deadlock(x, y, walls, goals):
    if (x, y) in goals:
        return False

    # --- Vertical wall check ---
    if (x-1, y) in walls or (x+1, y) in walls:
        # Box is against a vertical wall, scan entire column
        same_col_goals = any(gx == x for gx, gy in goals)
        if not same_col_goals:
            return True

    # --- Horizontal wall check ---
    if (x, y-1) in walls or (x, y+1) in walls:
        # Box is against a horizontal wall, scan entire row
        same_row_goals = any(gy == y for gx, gy in goals)
        if not same_row_goals:
            return True

    return False

def is_block_2x2_deadlock(x, y, boxes, walls, goals):
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

# state define
# map - 2D array of chars
# boxes - list of (x,y) positions
# player - (x,y) position
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
        # Sort boxes so order doesn't matter
        return hash((self.player, tuple(sorted(self.boxes))))

    def to_str(self):
        pass

    def is_win(self, goal):
        # check if all boxes are on goals
        return set(goal).issubset(set(self.boxes))

    def is_deadlock(self):
        for (x, y) in self.boxes:
            if is_corner_deadlock(x, y, self.walls, self.goal):
                return True
            # tạm thời bị disable
            # if is_edge_deadlock(x, y, self.walls, self.goal):
            #     return True
            if is_block_2x2_deadlock(x, y, self.boxes, self.walls, self.goal):
                return True
        return False

    def explore_neighbors(self):
        # explore neighbors of current state
        # return a list of valid states
        # player go up, down, left, right
        # if hit wall, ignore
        # if hit box, check if box can be pushed

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
            # print("Invalid direction")
            return None # invalid direction, ignore
        
        if (self.walls.__contains__(new_player)):
            # print("Hit wall")
            return None # hit wall, ignore
        
        if (new_boxes.__contains__(new_player)):
            if (direction == "up"):
                new_box = (new_player[0], new_player[1] - 1)
            elif (direction == "down"):
                new_box = (new_player[0], new_player[1] + 1)
            elif (direction == "left"):
                new_box = (new_player[0] - 1, new_player[1])
            elif (direction == "right"):
                new_box = (new_player[0] + 1, new_player[1])

            # print(self.walls)
            # print(new_box)
            # print(boxes)
            if (self.walls.__contains__(new_box) or new_boxes.__contains__(new_box)):
                # print("Box stuck")
                return None # box stuck, ignore
            else:
                new_boxes.remove(new_player)
                new_boxes.append(new_box)
                
                # print("Move box")
                # update map
                new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))

                return State(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])
        
        # print("Move player")
        new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))
        
        return State(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])
    
# goal - list of (x,y) positions

tile_char = {
    '#': 'wall',
    ' ': 'floor',
    '.': 'goal',
    '$': 'box',
    '*': 'box_on_goal',
    '@': 'player',
    '+': 'player_on_goal'
}

direction = ['up', 'down', 'left', 'right']

def load_testcase(tc):
    # return map, start, goal from testcases/tc_<id>.txt
    # parse it to global variables

    # load file and parse it
    # first line: width height
    # following lines: map

    pass

def BrFS(init_state, goal):
    # implement Breadth-First Search algorithm
    # return path (up, down, left, right) from start to goal
    # if no path, return None
    generated_node = 0
    expand_node = 0
    revisited_node = 0
    start_time = time.time()
    max_memory_usage = 0
    baseline_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

    queue = [init_state]
    visited = set()
    visited.add(init_state)

    while len(queue) != 0:
        # Đo memory hiện tại
        current_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024) - baseline_memory
        max_memory_usage = max(max_memory_usage, current_memory)

        # explore node (state) found
        explored = queue.pop(0).explore_neighbors()
        expand_node += 1
        for state in explored:
            generated_node += 1
            if state.is_deadlock():
                continue

            if state in visited:
                revisited_node += 1
                continue
            
            if state.is_win(goal):
                end_time = time.time()
                result = {
                    'is_solved': True,
                    'path': state.path,
                    'expand_node': expand_node, 
                    'generated_node': generated_node, 
                    'revisited_node': revisited_node,
                    'time_taken': end_time - start_time,    
                    'memory_used': max_memory_usage    
                }
                return result
            
            queue.append(state)
            visited.add(state)

    # no solution
    # return flag, path, explored_nodes, time_taken, memory_used
    result = {
        'is_solved': False, 
        'path': [], 
        'expand_node': 0,
        'generated_node': 0,
        'revisited_node': 0,
        'time_taken': 0,
        'memory_used': 0
    }
    return result

def A_star(init_state, goal):
    """
    Implement A* algorithm with Hungarian Algorithm heuristic
    
    Args:
        result: dict to store results
        init_state: State object with initial game state
        goal: list of goal positions
    """
    generated_node = 0
    expand_node = 0
    revisited_node = 0
    start_time = time.time()
    max_memory_usage = 0
    baseline_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

    # Priority queue: (f_cost, counter, state)
    counter = 0
    heap = []
    heapq.heappush(heap, (A_star_h(init_state, init_state, goal), counter, init_state))
    
    visited = {}
    visited[init_state] = 0  # g_cost
    
    while heap:
        # Measure current memory
        current_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024) - baseline_memory
        max_memory_usage = max(max_memory_usage, current_memory)
        
        f_cost, _, current_state = heapq.heappop(heap)
        expand_node += 1
        
        # Check if goal state
        if current_state.is_win(goal):
            end_time = time.time()
            result = {
                'is_solved': True,
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': max_memory_usage
            }
            return result
        
        # Get current g_cost
        g_cost = visited[current_state]
        
        # Explore neighbors
        for neighbor in current_state.explore_neighbors():
            generated_node += 1
            
            # Skip deadlocks
            if neighbor.is_deadlock():
                continue
            
            # Calculate new g_cost (number of moves)
            new_g_cost = g_cost + 1
            
            # Check if already visited with better cost
            if neighbor in visited:
                revisited_node += 1
                if visited[neighbor] <= new_g_cost:
                    continue
            
            # Update visited
            visited[neighbor] = new_g_cost
            
            # Calculate h_cost using Hungarian Algorithm
            h_cost = A_star_h(neighbor, init_state, goal)
            
            # f_cost = g_cost + h_cost
            new_f_cost = new_g_cost + h_cost
            
            # Add to heap
            counter += 1
            heapq.heappush(heap, (new_f_cost, counter, neighbor))
    
    # No solution found
    end_time = time.time()
    result = {
        'is_solved': False,
        'path': [],
        'expand_node': expand_node,
        'generated_node': generated_node,
        'revisited_node': revisited_node,
        'time_taken': end_time - start_time,
        'memory_used': max_memory_usage
    }
    return result

def A_star_h(current_state, init_state, goal):
    """
    Calculate h(n) using Hungarian Algorithm for optimal box-goal assignment
    
    Args:
        current_state: State object with current boxes positions
        init_state: State object (not used, kept for signature compatibility)
        goal: list of goal positions
    
    Returns:
        int: heuristic value (optimal assignment cost)
    """
    boxes = current_state.boxes
    goals = goal
    
    # Find boxes not yet on goals
    completed_boxes = set(boxes) & set(goals)
    remaining_boxes = list(set(boxes) - completed_boxes)
    remaining_goals = list(set(goals) - completed_boxes)
    
    # If all boxes on goals, h = 0
    if not remaining_boxes:
        return 0
    
    # Create cost matrix: Manhattan distances
    cost_matrix = np.array([[
        abs(box[0] - goal_pos[0]) + abs(box[1] - goal_pos[1])
        for goal_pos in remaining_goals
    ] for box in remaining_boxes])
    
    # Solve assignment problem using Hungarian Algorithm
    row_indices, col_indices = linear_sum_assignment(cost_matrix)
    
    # Return sum of optimal assignment
    return int(cost_matrix[row_indices, col_indices].sum())

def A_star_g(current_state, init_state, goal):
    """
    Calculate g(n) - cost from start to current state
    
    Args:
        current_state: State object with current state
        init_state: State object (not used, kept for signature compatibility) 
        goal: list of goal positions (not used, kept for signature compatibility)
    
    Returns:
        int: number of moves from start to current state
    """
    return len(current_state.path)

def draw(map, UI):
    # offset x for drawing multiple maps side by side
    # display map using pygame 
    # without pygame:
    if not UI:
        for row in map:
            print(row)

    # pygame.display.update()
    # pygame.time.delay(100)
    pass

def replay_path(init_state, path, UI):
    # replay path step by step
    # return list of map and drawing them having delay
    result = [init_state]
    draw(init_state.map, UI)
    state = init_state
    for dir in path:
        state = state.move(dir)
        print(dir)
        draw(state.map, UI)
        result.append(state)

    return result

def loadInfoFromMap(map):
    boxes = []
    walls = []
    player = (0,0)
    goal = []
    for y, row in enumerate(map):
        for x, c in enumerate(row):
            if (c == '$' or c == '*'):
                boxes.append((x, y))
            if (c == '.' or c == '*' or c == '+'):
                goal.append((x, y))
            if (c == '@' or c == '+'):
                player = (x, y)
            if (c == '#'): 
                walls.append((x,y))    
    return boxes, walls, player, goal

# via UI pygame collect testcase, method 
def solver(testcase, method, is_log=True, debug=True, UI=False):
    # init_map = load_testcase(testcase)
    # if not init_map:
    #     print(f"No testcase {tc_id}")
    #     sys.exit(1)
    init_map = [
        "#### ####",
        "#  ###  #",
        "# $ * $ #",
        "#   +   #",
        "### .$###",
        "  # . #  ",
        "  #####  "
    ]
    init_boxes, init_walls, init_player, init_goal = loadInfoFromMap(init_map)
    init_state = State(init_map, init_boxes, init_walls, init_player, init_goal, [])

    if (method == 'BrFS'):
        result = BrFS(init_state, init_goal)
        if not result['is_solved']:
            print("No Solution")
            return None

        if (is_log):
            # export file
            print("export file")

        if (debug):
            # debug
            print(result['path'])
            replay_path(init_state, result['path'], UI)
            print(f"Time: {result['time_taken']}s")
            print(f"Expanded Node: {result['expand_node']}")
            print(f"Generated Node: {result['generated_node']}")
            print(f"Revisited Node: {result['revisited_node']}")
            print(f"Max memory usage: {result['memory_used']}MB")

        return result['path']
    
    if (method == 'A_star'):
        result = A_star(init_state, init_goal)
        if not result['is_solved']:
            print("No Solution")
            return None

        if (is_log):
            # export file
            print("export file")

        if (debug):
            # debug
            print(result['path'])
            replay_path(init_state, result['path'], UI)
            print(f"Time: {result['time_taken']}s")
            print(f"Expanded Node: {result['expand_node']}")
            print(f"Generated Node: {result['generated_node']}")
            print(f"Revisited Node: {result['revisited_node']}")
            print(f"Max memory usage: {result['memory_used']}MB")

        return result['path']

if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print("Usage: python solver.py <testcase_id> <method>")
        sys.exit(1)

    tc_id = int(sys.argv[1])
    method = sys.argv[2]
    print(f"Running testcase {tc_id} using {method}")

    solver(tc_id, method)
        
    pass
