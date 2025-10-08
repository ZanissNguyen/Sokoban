import pygame
import threading

pygame.init()

# state define
# map - 2D array of chars
# boxes - list of (x,y) positions
# player - (x,y) position
# goal - list of (x,y) positions
map = []
player = (0, 0)
boxes = set()
goal = set()

game_state = ["choose_testcase", "solving", "solved"]

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

def is_win(map):
    # check if all boxes are on goals
    return goal.issubset(boxes)

def is_deadlock(map):
    # check if any box is in a deadlock position
    pass

def explore_neighbors(map):
    # explore neighbors of current state
    # return a list of valid states
    # player go up, down, left, right
    # if hit wall, ignore
    # if hit box, check if box can be pushed
    pass

def load_testcase(tc):
    # return map, start, goal from testcases/tc_<id>.txt
    # parse it to global variables

    # load file and parse it
    # first line: width height
    # following lines: map

    pass

def BrFS(map, start, goal):
    # implement Breadth-First Search algorithm
    # return path (up, down, left, right) from start to goal
    # if no path, return None

    # return flag, path, explored_nodes, time_taken, memory_used
    return True, True, [], 0, 0, 0

def A_star(map, start, goal):
    # implement A* algorithm

    # return solved flag, path, explored_nodes, time_taken, memory_used
    return True, True, [], 0, 0, 0

def A_star_h(map, start, goal):
    # calculate h(n)
    pass

def A_star_g(map, start, goal):
    # calculate g(n)
    pass

def draw(map, offset_x = 0):
    # offset x for drawing multiple maps side by side
    # display map using pygame 

    pygame.display.update()
    pass

def replay_path(start_map, path):
    # replay path step by step
    # return list of map
    return []

if __name__ == "__main__":

    running = True
    pygame.display.set_caption("Sokoban Solver")

    state = game_state[0]
    testcase = 0
    starting_map = []

    while running:

        # check for game_state
        if state == "choose_testcase":
        #     display testcase selection screen
        #     event handle
            pass
        elif state == "solving":
        #     # run BrFS and A* in separate threads
            brfs_done = False
            astar_done = False    
            brfs_path = []
            astar_path = []
            brfs_thread = threading.Thread(target=lambda: BrFS(starting_map, player, goal))
            astar_thread = threading.Thread(target=lambda: A_star(starting_map, player
            , goal))
            brfs_thread.start()  
            astar_thread.start()
            brfs_thread.join()
            astar_thread.join()
            state = game_state[2]

            # draw
            if brfs_done:
                # Animate BrFS path step by step
                brfs_map = replay_path(starting_map, brfs_path)
                for m in brfs_map:
                    draw(map, 0)
            if astar_done:
                # Animate A* path step by step
                astar_map = replay_path(starting_map, astar_path)
                for m in astar_map:
                    draw(map, 0) #offset = window_width / 2

            # if both completed display button analysis
        elif state == "solved":
            # display both status: is solve, some evaluation information
            pass

        # for event in pygame.event.get():
        #     if event.type == pygame.QUIT:
        #         running = False
        
        pass
