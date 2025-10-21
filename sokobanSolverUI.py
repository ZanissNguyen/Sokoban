import pygame
import numpy as np
from optionBox import *
from sokoban import *
import time

def isLegalGameAct(action, posPlayer, posBox, posWalls):
    """Check if the given action is legal"""
    xPlayer, yPlayer = posPlayer
    x1, y1 = xPlayer + action[0], yPlayer + action[1]
    if(x1, y1) in posBox :
        if(x1 + action[0], y1 + action[1]) not in posBox + posWalls:
            return True
    return (x1, y1) not in posBox + posWalls

def updateGameState(posPlayer, posBox, action):
    """Return updated game state after an action is taken"""
    xPlayer, yPlayer = posPlayer # the previous position of player
    newPosPlayer = [xPlayer + action[0], yPlayer + action[1]] # the current position of player
    posBox = [list(x) for x in posBox]
    if newPosPlayer in posBox:
        posBox.remove(newPosPlayer)
        posBox.append([xPlayer + 2*action[0], yPlayer + 2*action[1]])
    posBox = tuple(tuple(x) for x in posBox)
    newPosPlayer = tuple(newPosPlayer)
    return newPosPlayer, posBox

def loadGameState(gamelevel):
    with open(f"sokobanLevels/level{gamelevel + 1}.txt","r") as f:
        layout = f.readlines()
    gamestate = transferToGameState(layout)
    return gamestate

#load default game state
with open("sokobanLevels/level1.txt","r") as f:
    layout = f.readlines()

gamestate = transferToGameState(layout)
height = gamestate.shape[0]
width = gamestate.shape[1]
posWalls = PosOfWalls(gamestate)
playerPosition = PosOfPlayer(gamestate)
boxesPosition = PosOfBoxes(gamestate)
goalPosition = PosOfGoals(gamestate)

pygame.init()
screen = pygame.display.set_mode((1800, 1000))
pygame.display.set_caption("Sokoban Solver - A* Hungarian Algorithm")
running = True

#load image
wall = pygame.transform.scale(pygame.image.load('sokobanAssets/wall.bmp').convert(), (60, 60))
tiles = pygame.transform.scale(pygame.image.load('sokobanAssets/tiles.bmp').convert(), (60, 60))
player = pygame.transform.scale(pygame.image.load('sokobanAssets/player.bmp').convert(), (60,60))
box = pygame.transform.scale(pygame.image.load('sokobanAssets/crate.bmp').convert(), (60,60))
goal = pygame.transform.scale(pygame.image.load('sokobanAssets/goal.bmp').convert(), (60, 60))
playerInGoal = pygame.transform.scale(pygame.image.load('sokobanAssets/playerInGoal.bmp'), (60,60))
boxInGoal = pygame.transform.scale(pygame.image.load('sokobanAssets/boxInGoal.bmp'), (60,60))

dy = 900 - 30*width - 60
dx = 20

pygame.font.init()
button_font = pygame.font.Font(None, 40)
text_font = pygame.font.Font(None, 50)
title_font = pygame.font.Font(None, 60)

# Button positions
dbutton = 1100

# Solver button
solve_button_rect = pygame.Rect(dbutton - 100, 700, 120, 50)

# Play button (replaces Next)
play_button_rect = pygame.Rect(dbutton + 60, 700, 100, 50)

# Restart button
restart_button_rect = pygame.Rect(dbutton - 120, 770, 120, 50)

# Exit button
exit_button_rect = pygame.Rect(dbutton + 60, 770, 100, 50)

# Colors
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
COLOR_GREEN = pygame.Color('green')
COLOR_RED = pygame.Color('red')
COLOR_ORANGE = pygame.Color('orange')

current_button_color = COLOR_INACTIVE

# Button texts
solve_button_text = button_font.render("Solve", True, pygame.Color('white'))
solve_text_rect = solve_button_text.get_rect(center=solve_button_rect.center)

play_button_text = button_font.render("Play", True, pygame.Color('white'))
play_text_rect = play_button_text.get_rect(center=play_button_rect.center)

pause_button_text = button_font.render("Pause", True, pygame.Color('white'))
pause_text_rect = pause_button_text.get_rect(center=play_button_rect.center)

restart_button_text = button_font.render("Restart", True, pygame.Color('white'))
restart_text_rect = restart_button_text.get_rect(center=restart_button_rect.center)

exit_button_text = button_font.render("Exit", True, pygame.Color('white'))
exit_text_rect = exit_button_text.get_rect(center=exit_button_rect.center)

# Dropdowns
methodList = OptionBox(dbutton - 300, 700, 200, 50, current_button_color, pygame.Color('white'), button_font, ["BFS", "A* Hungarian"])
levelList = OptionBox(dbutton - 540, 700, 120, 50, current_button_color, pygame.Color('white'), button_font, ["level1", "level2", "level3", "level4", "level5"])

# Game state variables
solution = ""
nextAct = 0
method = 1  # Default to A* Hungarian
isSolved = False
isPlaying = False
isComplete = False

# Animation variables
last_step_time = 0
step_delay = 0.5  # 0.5 seconds between steps

# Success message variables
show_success_msg = False
success_msg_start_time = 0
solve_duration = 0.0
SUCCESS_MSG_DURATION = 5000

# Title
title_text = title_font.render("Sokoban Solver - A* Hungarian", True, (50, 50, 150))
title_rect = title_text.get_rect(center=(900, 50))

# Main game loop
clock = pygame.time.Clock()

while running:
    current_time = pygame.time.get_ticks()
    event_list = pygame.event.get()
    
    for event in event_list:
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Solve button
            if event.button == 1 and solve_button_rect.collidepoint(event.pos) and not isSolved:
                wait_text = text_font.render("Solving, please wait...", 1, (200, 0, 0))
                screen.blit(wait_text, (dbutton - 540, 840))
                pygame.display.flip()

                start_time = pygame.time.get_ticks()
                solution = sokobanSolver(gamestate, method)
                end_time = pygame.time.get_ticks()
                solve_duration = (end_time - start_time) / 1000.0

                nextAct = 0
                isSolved = True
                isPlaying = False
                isComplete = False
                show_success_msg = True
                success_msg_start_time = pygame.time.get_ticks()

            # Play/Pause button
            if event.button == 1 and play_button_rect.collidepoint(event.pos) and isSolved and not isComplete:
                isPlaying = not isPlaying
                last_step_time = current_time

            # Restart button
            if event.button == 1 and restart_button_rect.collidepoint(event.pos):
                # Reload current level
                level = levelList.selected
                gamestate = loadGameState(level)
                height = gamestate.shape[0]
                width = gamestate.shape[1]
                posWalls = PosOfWalls(gamestate)
                playerPosition = PosOfPlayer(gamestate)
                boxesPosition = PosOfBoxes(gamestate)
                goalPosition = PosOfGoals(gamestate)
                dy = 900 - 30 * width - 60
                dx = 20
                
                isSolved = False
                isPlaying = False
                isComplete = False
                solution = ""
                nextAct = 0
                show_success_msg = False

            # Exit button
            if event.button == 1 and exit_button_rect.collidepoint(event.pos):
                running = False

        # Keyboard controls
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                if isLegalGameAct((-1, 0), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (-1, 0))

            if event.key == pygame.K_DOWN:
                if isLegalGameAct((1, 0), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (1, 0))

            if event.key == pygame.K_LEFT:
                if isLegalGameAct((0, -1), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (0, -1))

            if event.key == pygame.K_RIGHT:
                if isLegalGameAct((0, 1), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (0, 1))

    # Handle method selection
    newMethod = methodList.update(event_list)
    if newMethod >= 0 and newMethod != method:
        method = newMethod
        isSolved = False
        isPlaying = False
        isComplete = False

    # Handle level selection
    level = levelList.update(event_list)
    if level >= 0:
        gamestate = loadGameState(level)
        height = gamestate.shape[0]
        width = gamestate.shape[1]
        posWalls = PosOfWalls(gamestate)
        playerPosition = PosOfPlayer(gamestate)
        boxesPosition = PosOfBoxes(gamestate)
        goalPosition = PosOfGoals(gamestate)
        dy = 900 - 30 * width - 60
        dx = 20
        isSolved = False
        isPlaying = False
        isComplete = False
        solution = ""
        nextAct = 0

    # Auto-play animation
    if isPlaying and solution and nextAct < len(solution):
        if current_time - last_step_time >= step_delay * 1000:
            if solution[nextAct] == 'u' or solution[nextAct] == 'U':
                if isLegalGameAct((-1, 0), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (-1, 0))
            elif solution[nextAct] == 'l' or solution[nextAct] == 'L':
                if isLegalGameAct((0, -1), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (0, -1))
            elif solution[nextAct] == 'r' or solution[nextAct] == 'R':
                if isLegalGameAct((0, 1), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (0, 1))
            elif solution[nextAct] == 'd' or solution[nextAct] == 'D':
                if isLegalGameAct((1, 0), playerPosition, boxesPosition, posWalls):
                    playerPosition, boxesPosition = updateGameState(playerPosition, boxesPosition, (1, 0))
            
            nextAct += 1
            last_step_time = current_time
            
            # Check if completed
            if nextAct >= len(solution):
                isPlaying = False
                isComplete = True

    # Drawing
    screen.fill((200, 200, 200))
    
    # Draw title
    screen.blit(title_text, title_rect)
    
    # Draw game board
    for x in range(height):
        for y in range(width):
            if (x, y) in posWalls:
                screen.blit(wall, (dy + y * 60, dx + x * 60))
            elif (x, y) == playerPosition:
                if (x, y) in goalPosition:
                    screen.blit(playerInGoal, (dy + y * 60, dx + x * 60))
                else:
                    screen.blit(player, (dy + y * 60, dx + x * 60))
            elif (x, y) in boxesPosition:
                if(x, y) in goalPosition:
                    screen.blit(boxInGoal, (dy + y * 60, dx + x * 60))
                else:
                    screen.blit(box, (dy + y * 60, dx + x * 60))
            elif (x, y) in goalPosition:
                screen.blit(goal, (dy + y * 60, dx + x * 60))
            else:
                screen.blit(tiles, (dy + y * 60, dx + x * 60))

    # Draw solve button
    solve_color = COLOR_INACTIVE if not isSolved else COLOR_GREEN
    pygame.draw.rect(screen, solve_color, solve_button_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), solve_button_rect, 2, border_radius=10)
    screen.blit(solve_button_text, solve_text_rect)

    # Draw play/pause button
    if isSolved and not isComplete:
        play_color = COLOR_GREEN if not isPlaying else COLOR_ORANGE
        pygame.draw.rect(screen, play_color, play_button_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), play_button_rect, 2, border_radius=10)
        if isPlaying:
            screen.blit(pause_button_text, pause_text_rect)
        else:
            screen.blit(play_button_text, play_text_rect)

    # Draw restart button
    pygame.draw.rect(screen, COLOR_INACTIVE, restart_button_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), restart_button_rect, 2, border_radius=10)
    screen.blit(restart_button_text, restart_text_rect)

    # Draw exit button
    pygame.draw.rect(screen, COLOR_RED, exit_button_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), exit_button_rect, 2, border_radius=10)
    screen.blit(exit_button_text, exit_text_rect)

    # Draw dropdowns
    methodList.draw(screen)
    levelList.draw(screen)

    # Status messages
    if show_success_msg and current_time - success_msg_start_time < SUCCESS_MSG_DURATION:
        msg_str = f"Solved in {solve_duration:.2f}s with {len(solution)} steps. Click Play to animate."
        success_text = text_font.render(msg_str, 1, (0, 150, 0))
        screen.blit(success_text, (dbutton - 770, 840))

    # Completion message
    if isComplete:
        complete_text = text_font.render("✓ COMPLETED! All boxes on goals.", 1, (0, 100, 200))
        screen.blit(complete_text, (dbutton - 600, 840))

    # Progress indicator
    if isSolved and solution:
        progress_text = button_font.render(f"Step: {nextAct}/{len(solution)}", 1, (50, 50, 50))
        screen.blit(progress_text, (dbutton + 200, 710))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
