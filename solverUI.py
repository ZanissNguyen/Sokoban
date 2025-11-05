import pygame
from solver import *

#some const
step_delay = 500  # 0.5 seconds between steps

#pygame init, init texture, button
pygame.init()
running = True

# function
# drawMap, Replay
def drawUI(map):
    # offset x for drawing multiple maps side by side
    # display map using pygame 
    # without pygame:
    for y, row in enumerate(map):
        for x, c in enumerate(row):
            if c == tile_char['wall']:  # wall
                screen.blit(wall, (x * tile_size, y * tile_size))
            elif c == tile_char['player_on_goal']:  # player_on_goal
                screen.blit(playerInGoal, (x * tile_size, y * tile_size))
            elif c == tile_char['player']:  # player
                screen.blit(player, (x * tile_size, y * tile_size))
            elif c == tile_char['box_on_goal']:  # box_on_goal
                screen.blit(boxInGoal, (x * tile_size, y * tile_size))
            elif c == tile_char['box']:  # box
                screen.blit(box, (x * tile_size, y * tile_size))
            elif c == tile_char['goal']:  # goal
                screen.blit(goal, (x * tile_size, y * tile_size))
            else:  # available_move (.) hoặc các ký tự khác
                screen.blit(tiles, (x * tile_size, y * tile_size))

    pygame.display.update()
    pygame.time.delay(step_delay)

def replay_path_UI(init_state, path):
    # replay path step by step
    # return list of map and drawing them having delay
    result = [init_state]
    drawUI(init_state.map)
    state = init_state
    for dir in path:
        state = state.move(dir)
        print(dir)
        drawUI(state.map)
        result.append(state)

    print("Replay finished. final path: ", path)

if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print("Usage: python solverUI.py <testcase_id> <method>")
        sys.exit(1)

    tc_id = int(sys.argv[1])
    method = sys.argv[2]
    print(f"Running testcase {tc_id} using {method}")

    init_map = load_testcase(tc_id)
    
    height = len(init_map)
    width = len(init_map[0])
    overhigh = 9999
    overwide = 9999
    tile_size = 60
    if (width > 32):
        overwide = 1920/width
    if (height > 18):
        overhigh = 1080/height
    tile_size = min(tile_size, overhigh, overwide)
    
    init_boxes, init_walls, init_player, init_goal = loadInfoFromMap(init_map)
    init_state = SokobanState(init_map, init_boxes, init_walls, init_player, init_goal, [])

    wall = pygame.transform.scale(pygame.image.load('assets/wall.bmp'), (tile_size, tile_size))
    tiles = pygame.transform.scale(pygame.image.load('assets/tiles.bmp'), (tile_size, tile_size))
    player = pygame.transform.scale(pygame.image.load('assets/player.bmp'), (tile_size,tile_size))
    box = pygame.transform.scale(pygame.image.load('assets/crate.bmp'), (tile_size,tile_size))
    goal = pygame.transform.scale(pygame.image.load('assets/goal.bmp'), (tile_size, tile_size))
    playerInGoal = pygame.transform.scale(pygame.image.load('assets/playerInGoal.bmp'), (tile_size,tile_size))
    boxInGoal = pygame.transform.scale(pygame.image.load('assets/boxInGoal.bmp'), (tile_size,tile_size))

    screen = pygame.display.set_mode((tile_size*width, tile_size*height))
    pygame.display.set_caption("Sokoban Solver")
    pygame.display.update()

    drawUI(init_map)
    result = solver(tc_id, method)
    replay_path_UI(init_state, result)
        
    event_list = pygame.event.get()
    
    while True:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    replay_path_UI(init_state, result)

            if event.type == pygame.QUIT:
                pygame.quit()
