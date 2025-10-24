import sys, time, os
from datetime import datetime
import numpy as np
from scipy.optimize import linear_sum_assignment
import heapq
import tracemalloc
import gc

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
class SokobanState:
    def __init__(self, map, boxes, walls, player, goal, path):
        self.map = map
        self.boxes = boxes
        self.walls = walls
        self.player = player
        self.goal = goal
        self.path = path

    def __eq__(self, other):
        return isinstance(other, SokobanState) and self.player == other.player and set(self.boxes) == set(other.boxes)

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
            # Edge deadlock - ENABLED with conservative improved version
            # Only detects truly blocked corridors with no escape routes
            if is_edge_deadlock(x, y, self.walls, self.goal):
                return True
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

                return SokobanState(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])
        
        # print("Move player")
        new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))
        
        return SokobanState(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])
    
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
    gc.collect()
    gc.collect()
    gc.collect()
    tracemalloc.start()

    # implement Breadth-First Search algorithm
    # return path (up, down, left, right) from start to goal
    # if no path, return None
    generated_node = 0
    expand_node = 0
    revisited_node = 0
    start_time = time.time()

    queue = [init_state]
    visited = set()
    visited.add(init_state)

    while len(queue) != 0:
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
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                end_time = time.time()
                result = {
                    'is_solved': True,
                    'path': state.path,
                    'expand_node': expand_node, 
                    'generated_node': generated_node, 
                    'revisited_node': revisited_node,
                    'time_taken': end_time - start_time,    
                    'memory_used': peak / (1024 * 1024)    
                }
                return result
            
            queue.append(state)
            visited.add(state)

    # no solution
    # return flag, path, explored_nodes, time_taken, memory_used
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        'is_solved': False,
        'path': [],
        'expand_node': expand_node,
        'generated_node': generated_node,
        'revisited_node': revisited_node,
        'time_taken': end_time - start_time,
        'memory_used': peak / (1024 * 1024)
    }
    return result

def A_star(init_state, goal):
    gc.collect()
    gc.collect()
    gc.collect()
    tracemalloc.start()
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

    # Priority queue: (f_cost, counter, state)
    counter = 0
    heap = []
    heapq.heappush(heap, (A_star_h(init_state, init_state, goal), counter, init_state))
    
    visited = {}
    visited[init_state] = 0  # g_cost
    
    while heap:       
        f_cost, _, current_state = heapq.heappop(heap)
        expand_node += 1
        
        # Check if goal state
        if current_state.is_win(goal):
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            result = {
                'is_solved': True,
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': peak / (1024 * 1024)
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
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        'is_solved': False,
        'path': [],
        'expand_node': expand_node,
        'generated_node': generated_node,
        'revisited_node': revisited_node,
        'time_taken': end_time - start_time,
        'memory_used': peak / (1024 * 1024)
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

def draw(map):
    # offset x for drawing multiple maps side by side
    # display map using pygame 
    # without pygame:
    for row in map:
        print(row)

def replay_path(init_state, path):
    # replay path step by step
    # return list of map and drawing them having delay
    result = [init_state]
    draw(init_state.map)
    state = init_state
    for dir in path:
        state = state.move(dir)
        print(dir)
        draw(state.map)
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
def solver(testcase, method, is_log=True, debug=True):
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
    init_state = SokobanState(init_map, init_boxes, init_walls, init_player, init_goal, [])

    if (method == 'BrFS'):
        result = BrFS(init_state, init_goal)
        if not result['is_solved']:
            print("No Solution")
            return None

        if (is_log):
            # export file
            stats = [
                result['expand_node'],
                result['generated_node'],
                result['revisited_node'],
                result['time_taken'],
                result['memory_used']
            ]
            create_log(testcase, method, result['path'], result['is_solved'], stats, "")
            print("export file")

        if (debug):
            # debug
            print(result['path'])
            replay_path(init_state, result['path'])
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
            stats = [
                result['expand_node'],
                result['generated_node'],
                result['revisited_node'],
                result['time_taken'],
                result['memory_used']
            ]
            create_log(testcase, method, result['path'], result['is_solved'], stats, "")
            print("export file")

        if (debug):
            # debug
            print(result['path'])
            replay_path(init_state, result['path'])
            print(f"Time: {result['time_taken']}s")
            print(f"Expanded Node: {result['expand_node']}")
            print(f"Generated Node: {result['generated_node']}")
            print(f"Revisited Node: {result['revisited_node']}")
            print(f"Max memory usage: {result['memory_used']}MB")

        return result['path']

        
def create_log(test_name, algorithm, path, is_solved, stats, level_info=""):
    """
    Tạo log chi tiết cho mỗi test case
    
    Args:
        test_name: Tên test case
        algorithm: Thuật toán sử dụng
        solution: Lời giải (list các action)
        stats: Thống kê performance
        level_info: Thông tin về level
    """
    try:
        # Tạo thư mục logs nếu chưa có
        os.makedirs("logs", exist_ok=True)
        
        # Tạo tên file log với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/{test_name}_{algorithm}_{timestamp}.txt"
        
        with open(log_filename, 'a', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"SOKOBAN SOLVER - DETAILED ANALYSIS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test Case: {test_name}\n")
            f.write(f"Thuật toán: {algorithm}\n")
            f.write(f"Thông tin Level: {level_info}\n")
            f.write("-" * 80 + "\n")
            
            # Thông tin lời giải
            if is_solved:
                f.write(f"TÌM THẤY LỜI GIẢI:\n")
                f.write(f"Số bước: {len(path)}\n")
                f.write(f"Đường đi: {' -> '.join(path)}\n")
            else:
                f.write(f"KHÔNG TÌM THẤY LỜI GIẢI\n")
                pass
            
            f.write("-" * 80 + "\n")
            
            # Thống kê chi tiết
            f.write("THỐNG KÊ HIỆU NĂNG:\n")
            f.write(f"• Nodes đã mở rộng: {stats[0]:,}\n")
            f.write(f"• Nodes đã tạo: {stats[1]:,}\n") 
            f.write(f"• Nodes truy cập lại: {stats[2]:,}\n")
            f.write(f"• Memory sử dụng: {stats[4]:.3f} MB\n")
            f.write(f"• Thời gian thực hiện: {stats[3]:.6f} giây\n")
            
            # Hiệu suất
            if stats[0] > 0:
                efficiency = len(path) / stats[0]
                f.write(f"• Hiệu suất (steps/nodes): {efficiency:.6f}\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
        
        print(f"Đã tạo log chi tiết: {log_filename}")
        
    except Exception as e:
        print(f"Lỗi khi tạo log: {e}")

if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print("Usage: python solver.py <testcase_id> <method>")
        sys.exit(1)

    tc_id = int(sys.argv[1])
    method = sys.argv[2]
    print(f"Running testcase {tc_id} using {method}")

    solver(tc_id, method)
        
    pass
