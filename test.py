# test_map = [
#     "#### ####",
#     "#  ###  #",
#     "# $ * $ #",
#     "#   +   #",
#     "### .$###",
#     "  # . #  ",
#     "  #####  "
# ]
# test_map = [
#     "########",
#     "#@   $.#",
#     "########"
#
#  ]
# test_map = [
#     "#######",
#     "#     #",
#     "# $# ##",
#     "#    .#",
#     "# @# ##",
#     "#######"
# ]
# test_map = [
#     "#################",
#     "#  #  #  #  #   #",
#     "#.$   #  #.$    #",
#     "#  #.$ .$   #   #",
#     "# @#  #  #  #   #",
#     "#################",
# ]
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
                print("case 1")
                return True
            # if is_edge_deadlock(x, y, self.walls, self.goal):
            #     print("case 2")
            #     return True
            if is_block_2x2_deadlock(x, y, self.boxes, self.walls, self.goal):
                print("case 3   ")
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

def BrFS(init_state, goal):
    # implement Breadth-First Search algorithm
    # return path (up, down, left, right) from start to goal
    # if no path, return None
    queue = [init_state]
    visited = set()
    visited.add(init_state)

    while len(queue) != 0:
        explored = queue.pop(0).explore_neighbors()
        for state in explored:
            print("Path: ", state.path)
            state.draw()
        for state in explored:
            if state.is_deadlock():
                print("Path: ", state.path, " is deadlock")
                continue

            if state in visited:
                continue
            
            if state.is_win(goal):
                return state.path, 
            
            queue.append(state)
            visited.add(state)

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
    init_state.draw()

    print(BrFS(init_state, init_goal))
    # for state in init_state.explore_neighbors():   
    #     state.draw()

    pass