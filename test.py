test_map = [
    "####-####",
    "#  ###  #",
    "# $ * $ #",
    "#   +   #",
    "### .$###",
    "--# . #--",
    "--#####--"
]

map_width = len(test_map[0])
map_height = len(test_map)

boxes_positions = []
goal_positions = []
player_position = (0,0)
walls = []

def draw(map):
    for row in map:
        print(row)
    print("\n")

def move(direction, map, player, boxes):
    if (direction == "up"):
        new_player = (player[0], player[1] - 1)
    elif (direction == "down"):
        new_player = (player[0], player[1] + 1)
    elif (direction == "left"):
        new_player = (player[0] - 1, player[1])
    elif (direction == "right"):
        new_player = (player[0] + 1, player[1])
    else:    
        print("Invalid direction")
        return map, player, boxes # invalid direction
    
    if (walls.__contains__(new_player)):
        print("Hit wall")
        return map, player, boxes # hit wall, ignore
    
    if (boxes.__contains__(new_player)):
        if (direction == "up"):
            new_box = (new_player[0], new_player[1] - 1)
        elif (direction == "down"):
            new_box = (new_player[0], new_player[1] + 1)
        elif (direction == "left"):
            new_box = (new_player[0] - 1, new_player[1])
        elif (direction == "right"):
            new_box = (new_player[0] + 1, new_player[1])

        print(walls)
        print(new_box)
        print(boxes)
        if (walls.__contains__(new_box) or boxes.__contains__(new_box)):
            print("Box stuck")
            return map, player, boxes # box stuck wall or another box, ignore
        else:
            boxes.remove(new_player)
            boxes.append(new_box)
            
            print("Move box")
            # update map
            # check if new player is on goal\
            if (map[new_player[1]][new_player[0]] == '.'): 
                map[new_player[1]] = map[new_player[1]][:new_player[0]] + '+' + map[new_player[1]][new_player[0]+1:]
                map[player[1]] = map[player[1]][:player[0]] + ' ' + map[player[1]][player[0]+1:]
            else:
                map[new_player[1]] = map[new_player[1]][:new_player[0]] + '@' + map[new_player[1]][new_player[0]+1:]
                if (map[player[1]][player[0]] == '+'):
                    map[player[1]] = map[player[1]][:player[0]] + '.' + map[player[1]][player[0]+1:]
                else:
                    map[player[1]] = map[player[1]][:player[0]] + ' ' + map[player[1]][player[0]+1:]

            if (map[new_box[1]][new_box[0]] == '.'):
                map[new_box[1]] = map[new_box[1]][:new_box[0]] + '*' + map[new_box[1]][new_box[0]+1:]
            else:
                map[new_box[1]] = map[new_box[1]][:new_box[0]] + '$' + map[new_box[1]][new_box[0]+1:]
                
            player = new_player
            return map, player, boxes # move box
    
    print("Move player")
    if (map[new_player[1]][new_player[0]] == '.'): 
        map[new_player[1]] = map[new_player[1]][:new_player[0]] + '+' + map[new_player[1]][new_player[0]+1:]
    else:
        map[new_player[1]] = map[new_player[1]][:new_player[0]] + '@' + map[new_player[1]][new_player[0]+1:]
    
    if (map[player[1]][player[0]] == '+'):
        map[player[1]] = map[player[1]][:player[0]] + '.' + map[player[1]][player[0]+1:]
    else:
        map[player[1]] = map[player[1]][:player[0]] + ' ' + map[player[1]][player[0]+1:]

    return map, new_player, boxes

if __name__ == "__main__":
    for y, row in enumerate(test_map):
        for x, c in enumerate(row):
            if (c == '$' or c == '*'):
                boxes_positions.append((x, y))
            if (c == '.' or c == '*' or c == '+'):
                goal_positions.append((x, y))
            if (c == '@' or c == '+'):
                player_position = (x, y)
            if (c == '#'): 
                walls.append((x,y))

    print("Map size: ", map_width, "x", map_height)
    print("Player position: ", player_position)
    print("Boxes positions: ", boxes_positions)
    print("Goal positions: ", goal_positions)
    print("Walls positions: ", walls)

    print("Initital Map:")
    draw(test_map)

    test_map, player_position, boxes_position = move("down", test_map, player_position, boxes_positions)
    print("Player position: ", player_position)
    print("Boxes positions: ", boxes_positions)
    draw(test_map)
    pass