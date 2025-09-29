
import pygame

pygame.init()

game_state = ["choose_testcase", "solving", "solved"]

def load_testcase(tc):
    # return map, start, goal from testcases/tc_<id>.txt
    pass

def BrFS(map, start, goal):
    # implement Breadth-First Search algorithm
    pass

def A_star(map, start, goal):
    # implement A* algorithm
    pass

def A_star_h(map, start, goal):
    # calculate h(n)
    pass

def A_star_g(map, start, goal):
    # calculate g(n)
    pass

def draw(map):
    # draw
    pygame.display.update()
    pass 

if __name__ == "__main__":

    running = True
    pygame.display.set_caption("Sokoban Solver")

    state = game_state[0]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw(map)
        pass
