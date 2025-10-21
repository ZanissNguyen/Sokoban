import sys
import collections
import numpy as np
import heapq
import time
from scipy.optimize import linear_sum_assignment

class PriorityQueue:
    """Define a PriorityQueue data structure that will be used"""
    def  __init__(self):
        self.Heap = []
        self.Count = 0

    def push(self, item, priority):
        entry = (priority, self.Count, item)
        heapq.heappush(self.Heap, entry)
        self.Count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.Heap)
        return item

    def isEmpty(self):
        return len(self.Heap) == 0

"""Load puzzles and define the rules of sokoban"""

def transferToGameState(layout):
    """Transfer the layout of initial puzzle"""
    layout = [x.replace('\n','') for x in layout]
    layout = [','.join(layout[i]) for i in range(len(layout))]
    layout = [x.split(',') for x in layout]
    maxColsNum = max([len(x) for x in layout])
    for irow in range(len(layout)):
        for icol in range(len(layout[irow])):
            if layout[irow][icol] == ' ': layout[irow][icol] = 0   # free space
            elif layout[irow][icol] == '#': layout[irow][icol] = 1 # wall
            elif layout[irow][icol] == '&': layout[irow][icol] = 2 # player
            elif layout[irow][icol] == 'B': layout[irow][icol] = 3 # box
            elif layout[irow][icol] == '.': layout[irow][icol] = 4 # goal
            elif layout[irow][icol] == 'X': layout[irow][icol] = 5 # box on goal
        colsNum = len(layout[irow])
        if colsNum < maxColsNum:
            layout[irow].extend([0 for _ in range(maxColsNum-colsNum)])
    return np.array(layout)

def PosOfPlayer(gameState):
    """Return the position of agent"""
    return tuple(np.argwhere(gameState == 2)[0]) # e.g. (2, 2)

def PosOfBoxes(gameState):
    """Return the positions of boxes"""
    return tuple(tuple(x) for x in np.argwhere((gameState == 3) | (gameState == 5))) # e.g. ((2, 3), (3, 4), (4, 4), (6, 1), (6, 4), (6, 5))

def PosOfWalls(gameState):
    """Return the positions of walls"""
    return tuple(tuple(x) for x in np.argwhere(gameState == 1)) # e.g. like those above

def PosOfGoals(gameState):
    """Return the positions of goals"""
    return tuple(tuple(x) for x in np.argwhere((gameState == 4) | (gameState == 5))) # e.g. like those above


def isEndState(posBox, posGoals):
    return sorted(posBox) == sorted(posGoals)


def isLegalAction(action, posPlayer, posBox, posWalls):
    xPlayer, yPlayer = posPlayer
    if action[-1].isupper():  # the move was a push
        x1, y1 = xPlayer + 2 * action[0], yPlayer + 2 * action[1]
    else:
        x1, y1 = xPlayer + action[0], yPlayer + action[1]
    return (x1, y1) not in posBox + posWalls


def legalActions(posPlayer, posBox, posWalls):
    """Return all legal actions for the agent in the current game state"""
    allActions = [[-1, 0, 'u', 'U'], [1, 0, 'd', 'D'], [0, -1, 'l', 'L'], [0, 1, 'r', 'R']]
    xPlayer, yPlayer = posPlayer
    legalActions = []
    for action in allActions:
        x1, y1 = xPlayer + action[0], yPlayer + action[1]
        if (x1, y1) in posBox:  # the move was a push
            action.pop(2)  # drop the little letter
        else:
            action.pop(3)  # drop the upper letter
        if isLegalAction(action, posPlayer, posBox, posWalls):
            legalActions.append(action)
        else:
            continue
    return tuple(tuple(x) for x in legalActions)  # e.g. ((0, -1, 'l'), (0, 1, 'R'))
def updateState(posPlayer, posBox, action):
    """Return updated game state after an action is taken"""
    xPlayer, yPlayer = posPlayer # the previous position of player
    newPosPlayer = [xPlayer + action[0], yPlayer + action[1]] # the current position of player
    posBox = [list(x) for x in posBox]
    if action[-1].isupper(): # if pushing, update the position of box
        posBox.remove(newPosPlayer)
        posBox.append([xPlayer + 2 * action[0], yPlayer + 2 * action[1]])
    posBox = tuple(tuple(x) for x in posBox)
    newPosPlayer = tuple(newPosPlayer)
    return newPosPlayer, posBox


"""Implement all approcahes"""
def isFailed(posBox, posWalls, posGoals):
    rotatePattern = [[0, 1, 2, 3, 4, 5, 6, 7, 8],
                     [2, 5, 8, 1, 4, 7, 0, 3, 6],
                     [0, 1, 2, 3, 4, 5, 6, 7, 8][::-1],
                     [2, 5, 8, 1, 4, 7, 0, 3, 6][::-1]]
    flipPattern = [[2, 1, 0, 5, 4, 3, 8, 7, 6],
                   [0, 3, 6, 1, 4, 7, 2, 5, 8],
                   [2, 1, 0, 5, 4, 3, 8, 7, 6][::-1],
                   [0, 3, 6, 1, 4, 7, 2, 5, 8][::-1]]
    allPattern = rotatePattern + flipPattern

    for box in posBox:
        if box not in posGoals:
            board = [(box[0] - 1, box[1] - 1), (box[0] - 1, box[1]), (box[0] - 1, box[1] + 1),
                     (box[0], box[1] - 1), (box[0], box[1]), (box[0], box[1] + 1),
                     (box[0] + 1, box[1] - 1), (box[0] + 1, box[1]), (box[0] + 1, box[1] + 1)]
            for pattern in allPattern:
                newBoard = [board[i] for i in pattern]
                if newBoard[1] in posWalls and newBoard[5] in posWalls:
                    return True
                elif newBoard[1] in posBox and newBoard[2] in posWalls and newBoard[5] in posWalls:
                    return True
                elif newBoard[1] in posBox and newBoard[2] in posWalls and newBoard[5] in posBox:
                    return True
                elif newBoard[1] in posBox and newBoard[2] in posBox and newBoard[5] in posBox:
                    return True
                elif newBoard[1] in posBox and newBoard[6] in posBox and newBoard[2] in posWalls and newBoard[
                    3] in posWalls and newBoard[8] in posWalls:
                    return True
    return False

def breadthFirstSearch(gamestate):
    posGoals = PosOfGoals(gamestate)
    posWalls = PosOfWalls(gamestate)
    beginBox = PosOfBoxes(gamestate)
    beginPlayer = PosOfPlayer(gamestate)

    startState = (beginPlayer, beginBox)  # e.g. ((2, 2), ((2, 3), (3, 4), (4, 4), (6, 1), (6, 4), (6, 5)))
    frontier = collections.deque([[startState]])  # store states
    actions = collections.deque([[0]])  # store actions
    exploredSet = set()
    solution = ""
    while frontier:
        node = frontier.popleft()
        node_action = actions.popleft()
        if isEndState(node[-1][-1], posGoals):
            solution = str(','.join(node_action[1:]).replace(',', ''))
            break
        if node[-1] not in exploredSet:
            exploredSet.add(node[-1])
            for action in legalActions(node[-1][0], node[-1][1], posWalls):
                newPosPlayer, newPosBox = updateState(node[-1][0], node[-1][1], action)
                if isFailed(newPosBox, posWalls, posGoals):
                    continue
                frontier.append(node + [(newPosPlayer, newPosBox)])
                actions.append(node_action + [action[-1]])
    return solution

def heuristic(posPlayer, posBox, posGoals):
    distance = 0
    completes = set(posGoals) & set(posBox)
    sortposBox = list(set(posBox).difference(completes))
    sortposGoals = list(set(posGoals).difference(completes))
    for i in range(len(sortposBox)):
        distance += (abs(sortposBox[i][0] - sortposGoals[i][0])) + (abs(sortposBox[i][1] - sortposGoals[i][1]))
    return distance

def hungarianHeuristic(posPlayer, posBox, posGoals):
    """
    Hungarian Algorithm heuristic for optimal box-goal assignment
    
    Args:
        posPlayer: tuple (row, col) - player position (not used in calculation)
        posBox: tuple of tuples - positions of boxes
        posGoals: tuple of tuples - positions of goals
    
    Returns:
        int: optimal cost (sum of Manhattan distances for optimal assignment)
    """
    # Find boxes that are not yet on goals
    completedBoxes = set(posBox) & set(posGoals)
    remainingBoxes = list(set(posBox) - completedBoxes)
    remainingGoals = list(set(posGoals) - completedBoxes)
    
    # If all boxes are on goals, heuristic = 0
    if not remainingBoxes:
        return 0
    
    # Create cost matrix: cost[i][j] = Manhattan distance from box i to goal j
    costMatrix = np.array([[
        abs(box[0] - goal[0]) + abs(box[1] - goal[1])
        for goal in remainingGoals
    ] for box in remainingBoxes])
    
    # Solve assignment problem using Hungarian Algorithm
    rowIndices, colIndices = linear_sum_assignment(costMatrix)
    
    # Return sum of optimal assignment costs
    return int(costMatrix[rowIndices, colIndices].sum())

def cost(actions):
    """A cost function"""
    return len([x for x in actions if x.islower()])

def aStarSearch(gamestate):
    posGoals = PosOfGoals(gamestate)
    posWalls = PosOfWalls(gamestate)
    beginBox = PosOfBoxes(gamestate)
    beginPlayer = PosOfPlayer(gamestate)

    start_state = (beginPlayer, beginBox)
    frontier = PriorityQueue()
    frontier.push([start_state], heuristic(beginPlayer, beginBox, posGoals))
    exploredSet = set()
    actions = PriorityQueue()
    actions.push([0], heuristic(beginPlayer, start_state[1], posGoals))
    solution = ""
    while frontier:
        node = frontier.pop()
        node_action = actions.pop()
        if isEndState(node[-1][-1], posGoals):
            solution = str(','.join(node_action[1:]).replace(',', ''))
            break
        if node[-1] not in exploredSet:
            exploredSet.add(node[-1])
            Cost = cost(node_action[1:])
            for action in legalActions(node[-1][0], node[-1][1], posWalls):
                newPosPlayer, newPosBox = updateState(node[-1][0], node[-1][1], action)
                if isFailed(newPosBox, posWalls, posGoals):
                    continue
                Heuristic = heuristic(newPosPlayer, newPosBox, posGoals)
                frontier.push(node + [(newPosPlayer, newPosBox)], Heuristic + Cost)
                actions.push(node_action + [action[-1]], Heuristic + Cost)
    return solution

def aStarSearchHungarian(gamestate):
    """
    Enhanced A* Search with Hungarian Algorithm heuristic
    
    Args:
        gamestate: numpy array representing the game state
    
    Returns:
        solution: string of actions (e.g., "uRdL")
    """
    posGoals = PosOfGoals(gamestate)
    posWalls = PosOfWalls(gamestate)
    beginBox = PosOfBoxes(gamestate)
    beginPlayer = PosOfPlayer(gamestate)

    start_state = (beginPlayer, beginBox)
    frontier = PriorityQueue()
    frontier.push([start_state], hungarianHeuristic(beginPlayer, beginBox, posGoals))
    exploredSet = set()
    actions = PriorityQueue()
    actions.push([0], hungarianHeuristic(beginPlayer, start_state[1], posGoals))
    solution = ""
    
    while frontier:
        node = frontier.pop()
        node_action = actions.pop()
        
        # Check if goal state reached
        if isEndState(node[-1][-1], posGoals):
            solution = str(','.join(node_action[1:]).replace(',', ''))
            break
        
        # Skip if already explored
        if node[-1] not in exploredSet:
            exploredSet.add(node[-1])
            
            # Calculate g(n) = cost so far (number of pushes)
            Cost = cost(node_action[1:])
            
            # Expand all legal actions
            for action in legalActions(node[-1][0], node[-1][1], posWalls):
                newPosPlayer, newPosBox = updateState(node[-1][0], node[-1][1], action)
                
                # Skip failed states (deadlocks)
                if isFailed(newPosBox, posWalls, posGoals):
                    continue
                
                # Calculate h(n) using Hungarian Algorithm
                Heuristic = hungarianHeuristic(newPosPlayer, newPosBox, posGoals)
                
                # f(n) = g(n) + h(n)
                f_cost = Heuristic + Cost
                
                # Add to frontier
                frontier.push(node + [(newPosPlayer, newPosBox)], f_cost)
                actions.push(node_action + [action[-1]], f_cost)
    
    return solution

def sokobanSolver(gamestate, method):
    """
    Solve Sokoban puzzle using specified method
    
    Args:
        gamestate: numpy array representing game state
        method: 0=BFS, 1=A* Hungarian
    
    Returns:
        solution string
    """
    if method == 0:
        return breadthFirstSearch(gamestate)
    if method == 1:
        return aStarSearchHungarian(gamestate)
    return ""
