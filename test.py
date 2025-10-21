import numpy as np
from scipy.optimize import linear_sum_assignment
import heapq
import time
import psutil
import os
import gc  # Garbage collector
import tracemalloc  # Python memory profiler (more accurate!)

# test_map = [
#     "#### ####",
#     "#  ###  #",
#     "# $ * $ #",
#     "#   +   #",
#     "### .$###",
#     "  # . #  ",
#     "  #####  "
# ]
# Test cases - uncomment the one you want to test

# Very simple test case
# test_map = [
#     "########",
#     "#@   $.#",
#     "########"
# ]

# Simple test case
# test_map = [
#     "#######",
#     "#     #",
#     "# $# ##",
#     "#    .#",
#     "# @# ##",
#     "#######"
# ]

# Medium test case
# test_map = [
#     "#### ####",
#     "#  ###  #",
#     "# $ * $ #",
#     "#   +   #",
#     "### .$###",
#     "  # . #  ",
#     "  #####  "
# ]

# Medium-Hard test case (default)
test_map = [
    "   #### ",
    "####  # ",
    "#  $  ##",
    "# #$#  #",
    "#@ $   #",
    "#.###  #",
    "#.#### #",
    "#.     #",
    "########"
]

# Hard test case
# test_map = [
#     "#################",
#     "#  #  #  #  #   #",
#     "#.$   #  #.$    #",
#     "#  #.$ .$   #   #",
#     "# @#  #  #  #   #",
#     "#################",
# ]

map_width = len(test_map[0])
map_height = len(test_map)

direction = ['up', 'down', 'left', 'right']

def render_map(walls, boxes, player, goal, map_width, map_height):
    map_template = [[' ' for _ in range(map_width)] for _ in range(map_height)]
    # print("template:")
    # for row in map_template:
    #     print(''.join(row))
    # print("end template")
    new_map = [list(row) for row in map_template]
    # for row in new_map:
    #     print(''.join(row))
    # print("end new init")
    # print("walls:", walls)
    for (x, y) in walls: 
        # print(x,y)
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
    Edge deadlock improved:
    - If box is adjacent to a vertical wall (left or right),
      check the contiguous vertical segment (up/down) until walls.
      If no goal exists in that vertical span -> deadlock.
    - If box is adjacent to a horizontal wall (up or down),
      check contiguous horizontal span (left/right) until walls.
      If no goal exists in that horizontal span -> deadlock.
    Returns True if detected edge deadlock, False otherwise.
    """
    # If this pos is a goal, it's not a deadlock.
    if (x, y) in goals:
        return False

    # Helper: scan along column x from y up and down until hit wall,
    # return True if we find any goal in that span.
    def column_has_goal(x, y, walls, goals):
        # scan up
        yy = y
        while (x, yy - 1) not in walls:
            yy -= 1
            if (x, yy) in goals:
                return True
        # scan down
        yy = y
        while (x, yy + 1) not in walls:
            yy += 1
            if (x, yy) in goals:
                return True
        # also check current cell (already did earlier), but safe to check
        return False

    # Helper: scan along row y from x left and right until hit wall,
    # return True if any goal in that span.
    def row_has_goal(x, y, walls, goals):
        # scan left
        xx = x
        while (xx - 1, y) not in walls:
            xx -= 1
            if (xx, y) in goals:
                return True
        # scan right
        xx = x
        while (xx + 1, y) not in walls:
            xx += 1
            if (xx, y) in goals:
                return True
        return False

    # Vertical adjacency: cannot move left/right => movement limited to column
    if ((x - 1, y) in walls) or ((x + 1, y) in walls):
        # if there is NO goal in the contiguous vertical segment -> deadlock
        if not column_has_goal(x, y, walls, goals):
            return True

    # Horizontal adjacency: cannot move up/down => movement limited to row
    if ((x, y - 1) in walls) or ((x, y + 1) in walls):
        # if there is NO goal in the contiguous horizontal segment -> deadlock
        if not row_has_goal(x, y, walls, goals):
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
                # print("case 1: corner deadlock")
                return True
            # if is_edge_deadlock(x, y, self.walls, self.goal):
            #     print("case 2: edge deadlock")
            #     return True
            if is_block_2x2_deadlock(x, y, self.boxes, self.walls, self.goal):
                # print("case 3: 2x2 block deadlock")
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
        
        # print(self.walls)
        # print(new_boxes)
        # print(new_player)

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
                # print("Box stuck")
                return None # box stuck, ignore
            else:
                new_boxes.remove(new_player)
                new_boxes.append(new_box)
                
                # print("Test render map:")
                new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))
                # for row in test_map:
                #     print(row)

                # print("Move box")
                # update map
                # check if new player is on goal\
                # if (self.map[new_player[1]][new_player[0]] == '.'): 
                #     new_map[new_player[1]] = new_map[new_player[1]][:new_player[0]] + '+' + new_map[new_player[1]][new_player[0]+1:]
                #     new_map[self.player[1]] = new_map[self.player[1]][:self.player[0]] + ' ' + new_map[self.player[1]][self.player[0]+1:]
                # else:
                #     new_map[new_player[1]] = new_map[new_player[1]][:new_player[0]] + '@' + new_map[new_player[1]][new_player[0]+1:]
                #     if (new_map[self.player[1]][self.player[0]] == '+'):
                #         new_map[self.player[1]] = new_map[self.player[1]][:self.player[0]] + '.' + new_map[self.player[1]][self.player[0]+1:]
                #     else:
                #         new_map[self.player[1]] = new_map[self.player[1]][:self.player[0]] + ' ' + new_map[self.player[1]][self.player[0]+1:]

                # if (new_map[new_box[1]][new_box[0]] == '.'):
                #     new_map[new_box[1]] = new_map[new_box[1]][:new_box[0]] + '*' + new_map[new_box[1]][new_box[0]+1:]
                # else:
                #     new_map[new_box[1]] = new_map[new_box[1]][:new_box[0]] + '$' + new_map[new_box[1]][new_box[0]+1:]

                return State(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])
        
        # print("Move player")
        # print("Test render map:")
        # test_map = render_map(self.walls, new_boxes, new_player, self.goal,
        #                         len(self.map[0]), len(self.map))
        # for row in test_map:
        #     print(row)

        # if (new_map[new_player[1]][new_player[0]] == '.'): 
        #     new_map[new_player[1]] = new_map[new_player[1]][:new_player[0]] + '+' + new_map[new_player[1]][new_player[0]+1:]
        # else:
        #     new_map[new_player[1]] = new_map[new_player[1]][:new_player[0]] + '@' + new_map[new_player[1]][new_player[0]+1:]
        
        # if (new_map[self.player[1]][self.player[0]] == '+'):
        #     new_map[self.player[1]] = new_map[self.player[1]][:self.player[0]] + '.' + new_map[self.player[1]][self.player[0]+1:]
        # else:
        #     new_map[self.player[1]] = new_map[self.player[1]][:self.player[0]] + ' ' + new_map[self.player[1]][self.player[0]+1:]

        new_map = render_map(self.walls, new_boxes, new_player, self.goal,
                                len(self.map[0]), len(self.map))

        return State(new_map, new_boxes, self.walls, new_player, self.goal, self.path + [direction])

    def draw(self):
        for row in self.map:
            print(row)
        print("\n")

def BrFS_tracemalloc(init_state, goal):
    """
    BFS with tracemalloc for MORE ACCURATE and STABLE memory measurement
    tracemalloc tracks Python object memory directly, not process memory
    This gives more consistent results across runs!
    """
    # Force garbage collection multiple times
    gc.collect()
    gc.collect()
    gc.collect()
    
    # Start tracemalloc
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
        
        # Check if current state is goal
        if current_state.is_win(goal):
            end_time = time.time()
            
            # Get peak memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            return {
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': peak / (1024 * 1024)  # Convert to MB
            }
        
        # Explore neighbors
        neighbors = current_state.explore_neighbors()
        
        for state in neighbors:
            generated_node += 1
            
            # Skip if already visited
            if state in visited:
                revisited_node += 1
                continue
            
            # Skip if deadlock
            if state.is_deadlock():
                continue
            
            # Add to queue and visited
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

def BrFS(init_state, goal):
    # implement Breadth-First Search algorithm
    # return path (up, down, left, right) from start to goal
    # if no path, return None
    
    # Force garbage collection before starting to get clean baseline
    gc.collect()
    
    start_time = time.time()
    generated_node = 0
    expand_node = 0
    revisited_node = 0
    
    # Get baseline memory (RSS - Resident Set Size in bytes)
    process = psutil.Process(os.getpid())
    baseline_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    max_memory_usage = 0
    
    queue = [init_state]
    visited = set()
    visited.add(init_state)

    while len(queue) != 0:
        # Measure current memory usage
        current_memory = process.memory_info().rss / (1024 * 1024) - baseline_memory
        max_memory_usage = max(max_memory_usage, current_memory)
        
        current_state = queue.pop(0)
        expand_node += 1
        
        # Check if current state is goal
        if current_state.is_win(goal):
            end_time = time.time()
            return {
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': max_memory_usage
            }
        
        # Explore neighbors
        neighbors = current_state.explore_neighbors()
        
        for state in neighbors:
            generated_node += 1
            
            # Skip if already visited
            if state in visited:
                revisited_node += 1
                continue
            
            # Skip if deadlock
            if state.is_deadlock():
                # print("Deadlock detected at:", state.path)
                continue
            
            # Add to queue and visited
            queue.append(state)
            visited.add(state)
            
            # Optional: print progress (comment out for faster execution)
            # print(f"Exploring path length: {len(state.path)}")
    
    end_time = time.time()
    return {
        'path': None,
        'expand_node': expand_node,
        'generated_node': generated_node,
        'revisited_node': revisited_node,
        'time_taken': end_time - start_time,
        'memory_used': max_memory_usage
    }  # No solution found

def A_star_tracemalloc(init_state, goal):
    """
    A* with tracemalloc for MORE ACCURATE and STABLE memory measurement
    tracemalloc tracks Python object memory directly, not process memory
    This gives more consistent results across runs!
    """
    # Force garbage collection multiple times
    gc.collect()
    gc.collect()
    gc.collect()
    
    # Start tracemalloc
    tracemalloc.start()
    
    start_time = time.time()
    generated_node = 0
    expand_node = 0
    revisited_node = 0

    # Priority queue: (f_cost, counter, state)
    counter = 0
    heap = []
    
    # Calculate initial h_cost
    h_cost = A_star_h(init_state, goal)
    heapq.heappush(heap, (h_cost, counter, init_state))
    
    visited = {}
    visited[init_state] = 0  # g_cost
    
    while heap:
        f_cost, _, current_state = heapq.heappop(heap)
        expand_node += 1
        
        # Check if goal state
        if current_state.is_win(goal):
            end_time = time.time()
            
            # Get peak memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            return {
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': peak / (1024 * 1024)  # Convert to MB
            }
        
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
            h_cost = A_star_h(neighbor, goal)
            
            # f_cost = g_cost + h_cost
            new_f_cost = new_g_cost + h_cost
            
            # Add to heap
            counter += 1
            heapq.heappush(heap, (new_f_cost, counter, neighbor))
    
    # No solution found
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

def A_star(init_state, goal):
    """
    Implement A* algorithm with Hungarian Algorithm heuristic
    
    Args:
        init_state: State object with initial game state
        goal: list of goal positions
    
    Returns:
        dict: solution with path and statistics
    """
    # Force garbage collection before starting to get clean baseline
    gc.collect()
    
    start_time = time.time()
    generated_node = 0
    expand_node = 0
    revisited_node = 0
    
    # Get baseline memory (RSS - Resident Set Size in bytes)
    process = psutil.Process(os.getpid())
    baseline_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    max_memory_usage = 0

    # Priority queue: (f_cost, counter, state)
    counter = 0
    heap = []
    
    # Calculate initial h_cost
    h_cost = A_star_h(init_state, goal)
    heapq.heappush(heap, (h_cost, counter, init_state))
    
    visited = {}
    visited[init_state] = 0  # g_cost
    
    while heap:
        # Measure current memory usage
        current_memory = process.memory_info().rss / (1024 * 1024) - baseline_memory
        max_memory_usage = max(max_memory_usage, current_memory)
        
        f_cost, _, current_state = heapq.heappop(heap)
        expand_node += 1
        
        # Check if goal state
        if current_state.is_win(goal):
            end_time = time.time()
            return {
                'path': current_state.path,
                'expand_node': expand_node,
                'generated_node': generated_node,
                'revisited_node': revisited_node,
                'time_taken': end_time - start_time,
                'memory_used': max_memory_usage
            }
        
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
            h_cost = A_star_h(neighbor, goal)
            
            # f_cost = g_cost + h_cost
            new_f_cost = new_g_cost + h_cost
            
            # Add to heap
            counter += 1
            heapq.heappush(heap, (new_f_cost, counter, neighbor))
    
    # No solution found
    end_time = time.time()
    return {
        'path': None,
        'expand_node': expand_node,
        'generated_node': generated_node,
        'revisited_node': revisited_node,
        'time_taken': end_time - start_time,
        'memory_used': max_memory_usage
    }

def A_star_h(current_state, goal):
    """
    Calculate h(n) using Hungarian Algorithm for optimal box-goal assignment
    
    Args:
        current_state: State object with current boxes positions
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

if __name__ == "__main__":

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
    
    print("Initial state:")
    init_state.draw()
    
    print("\n" + "="*50)
    print("Select algorithm:")
    print("1. BFS (Breadth-First Search)")
    print("2. A* (A-Star with Hungarian Algorithm)")
    print("3. Both (Compare)")
    print("4. Both with tracemalloc (More stable memory!)")
    print("="*50)
    
    choice = input("Enter your choice (1/2/3/4): ").strip()
    
    if choice == "1":
        print("\n" + "="*50)
        print("Solving using BFS...")
        print("="*50)
        result = BrFS(init_state, init_goal)
        
        if result['path']:
            print(f"\n[SUCCESS] Solution found!")
            print(f"Path length: {len(result['path'])}")
            print(f"Expanded nodes: {result['expand_node']}")
            print(f"Generated nodes: {result['generated_node']}")
            print(f"Revisited nodes: {result['revisited_node']}")
            print(f"Time taken: {result['time_taken']:.4f} seconds")
            print(f"Max memory usage: {result['memory_used']:.2f} MB")
            print(f"\nPath: {result['path']}")
        else:
            print("\n[FAILED] No solution found!")
    
    elif choice == "2":
        print("\n" + "="*50)
        print("Solving using A* with Hungarian Algorithm...")
        print("="*50)
        result = A_star(init_state, init_goal)
        
        if result['path']:
            print(f"\n[SUCCESS] Solution found!")
            print(f"Path length: {len(result['path'])}")
            print(f"Expanded nodes: {result['expand_node']}")
            print(f"Generated nodes: {result['generated_node']}")
            print(f"Revisited nodes: {result['revisited_node']}")
            print(f"Time taken: {result['time_taken']:.4f} seconds")
            print(f"Max memory usage: {result['memory_used']:.2f} MB")
            print(f"\nPath: {result['path']}")
        else:
            print("\n[FAILED] No solution found!")
    
    elif choice == "3":
        print("\n" + "="*50)
        print("Comparing BFS vs A* (Hungarian Algorithm)...")
        print("="*50)
        
        # Run BFS
        print("\nRunning BFS...")
        bfs_result = BrFS(init_state, init_goal)
        
        # Run A*
        print("Running A*...")
        astar_result = A_star(init_state, init_goal)
        
        # Display comparison
        print("\n" + "="*50)
        print("COMPARISON RESULTS")
        print("="*50)
        
        print("\n{:<25} {:<20} {:<20}".format("Metric", "BFS", "A* (Hungarian)"))
        print("-" * 65)
        
        if bfs_result['path']:
            bfs_path_len = len(bfs_result['path'])
        else:
            bfs_path_len = "N/A"
            
        if astar_result['path']:
            astar_path_len = len(astar_result['path'])
        else:
            astar_path_len = "N/A"
        
        print("{:<25} {:<20} {:<20}".format("Solution found:", 
                                             "YES" if bfs_result['path'] else "NO",
                                             "YES" if astar_result['path'] else "NO"))
        print("{:<25} {:<20} {:<20}".format("Path length:", 
                                             bfs_path_len, astar_path_len))
        print("{:<25} {:<20} {:<20}".format("Expanded nodes:", 
                                             bfs_result['expand_node'], 
                                             astar_result['expand_node']))
        print("{:<25} {:<20} {:<20}".format("Generated nodes:", 
                                             bfs_result['generated_node'], 
                                             astar_result['generated_node']))
        print("{:<25} {:<20} {:<20}".format("Revisited nodes:", 
                                             bfs_result['revisited_node'], 
                                             astar_result['revisited_node']))
        print("{:<25} {:<20.4f} {:<20.4f}".format("Time taken (s):", 
                                                    bfs_result['time_taken'], 
                                                    astar_result['time_taken']))
        print("{:<25} {:<20.2f} {:<20.2f}".format("Max memory (MB):", 
                                                    bfs_result['memory_used'], 
                                                    astar_result['memory_used']))
        
        # Calculate speedup
        if bfs_result['time_taken'] > 0 and astar_result['time_taken'] > 0:
            speedup = bfs_result['time_taken'] / astar_result['time_taken']
            print("\n" + "="*50)
            if speedup > 1:
                print(f"A* is {speedup:.2f}x faster than BFS")
            else:
                print(f"BFS is {1/speedup:.2f}x faster than A*")
            print("="*50)
        
        # Memory comparison
        if bfs_result['memory_used'] > 0 and astar_result['memory_used'] > 0:
            mem_ratio = bfs_result['memory_used'] / astar_result['memory_used']
            print("\n" + "="*50)
            if mem_ratio > 1:
                print(f"A* uses {mem_ratio:.2f}x less memory than BFS")
            else:
                print(f"BFS uses {1/mem_ratio:.2f}x less memory than A*")
            print("="*50)
    
    elif choice == "4":
        print("\n" + "="*50)
        print("Comparing BFS vs A* with tracemalloc...")
        print("(More accurate & stable memory measurement!)")
        print("="*50)
        
        # Run BFS with tracemalloc
        print("\nRunning BFS with tracemalloc...")
        bfs_result = BrFS_tracemalloc(init_state, init_goal)
        
        # Run A* with tracemalloc
        print("Running A* with tracemalloc...")
        astar_result = A_star_tracemalloc(init_state, init_goal)
        
        # Display comparison
        print("\n" + "="*50)
        print("COMPARISON RESULTS (tracemalloc)")
        print("="*50)
        
        print("\n{:<25} {:<20} {:<20}".format("Metric", "BFS", "A* (Hungarian)"))
        print("-" * 65)
        
        if bfs_result['path']:
            bfs_path_len = len(bfs_result['path'])
        else:
            bfs_path_len = "N/A"
            
        if astar_result['path']:
            astar_path_len = len(astar_result['path'])
        else:
            astar_path_len = "N/A"
        
        print("{:<25} {:<20} {:<20}".format("Solution found:", 
                                             "YES" if bfs_result['path'] else "NO",
                                             "YES" if astar_result['path'] else "NO"))
        print("{:<25} {:<20} {:<20}".format("Path length:", 
                                             bfs_path_len, astar_path_len))
        print("{:<25} {:<20} {:<20}".format("Expanded nodes:", 
                                             bfs_result['expand_node'], 
                                             astar_result['expand_node']))
        print("{:<25} {:<20} {:<20}".format("Generated nodes:", 
                                             bfs_result['generated_node'], 
                                             astar_result['generated_node']))
        print("{:<25} {:<20} {:<20}".format("Revisited nodes:", 
                                             bfs_result['revisited_node'], 
                                             astar_result['revisited_node']))
        print("{:<25} {:<20.4f} {:<20.4f}".format("Time taken (s):", 
                                                    bfs_result['time_taken'], 
                                                    astar_result['time_taken']))
        print("{:<25} {:<20.2f} {:<20.2f}".format("Peak memory (MB):", 
                                                    bfs_result['memory_used'], 
                                                    astar_result['memory_used']))
        
        # Calculate speedup
        if bfs_result['time_taken'] > 0 and astar_result['time_taken'] > 0:
            speedup = bfs_result['time_taken'] / astar_result['time_taken']
            print("\n" + "="*50)
            if speedup > 1:
                print(f"A* is {speedup:.2f}x faster than BFS")
            else:
                print(f"BFS is {1/speedup:.2f}x faster than A*")
            print("="*50)
        
        # Memory comparison
        if bfs_result['memory_used'] > 0 and astar_result['memory_used'] > 0:
            mem_ratio = bfs_result['memory_used'] / astar_result['memory_used']
            print("\n" + "="*50)
            if mem_ratio > 1:
                print(f"A* uses {mem_ratio:.2f}x less memory than BFS")
            else:
                print(f"BFS uses {1/mem_ratio:.2f}x less memory than A*")
            print("="*50)
        
    
    else:
        print("Invalid choice!")

    pass