import pygame
import random
import neat
import os
from copy import deepcopy

pygame.init()
WIDTHGAME = 1000
HEIGHTGAME = 800
WIDTHSCORE = 200

win = pygame.display.set_mode((WIDTHGAME+WIDTHSCORE, HEIGHTGAME))
font = pygame.font.Font(pygame.font.get_default_font(), 24)
pygame.display.set_caption("Tetris")
COLOR = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "RED": (255, 0, 0),
    "BLUE": (0, 0, 255),
    "GREEN": (0, 255, 0),
    "ORANGE": (255, 153, 51),
    "YELLOW": (255, 255, 51),
    "PINK": (255, 153, 204),
    "CYAN": (0, 255, 255)}


class Board:
    def __init__(self) -> None:
        self.board = [['-' for i in range(10)]for i in range(20)]
        self.height = [20 for _ in range(10)]
        self.holes = 0  # low = good
        self.height_penalty = 0  # low = good
        self.touch_wall = 0  # high = bad
        self.bumpyness = 0  # low = good

    def update_outline(self):
        self.height_penalty = 0
        self.holes = 0
        self.bumpyness = 0
        self.touch_wall = 0
        for i in range(len(self.height)):
            for y in range(len(self.board)):
                if self.board[y][i] != '-':
                    if y < self.height[i]:
                        self.height[i] = y
                    self.height_penalty += (20-y)
                if i == 9 and self.board[y][i] != '-':
                    self.touch_wall += 1
            for x in range(len(self.board)-self.height[i]):
                if self.board[self.height[i]+x][i] == '-':
                    self.holes += 1
        for i in range(len(self.height)-1):
            self.bumpyness += abs(self.height[i]-self.height[i+1])

    def draw(self, win, height, width, scale):
        for y in range(len(self.board)):
            for x in range(len(self.board[y])):
                if self.board[y][x] == 'r':
                    color = COLOR['RED']
                elif self.board[y][x] == 'g':
                    color = COLOR['GREEN']
                elif self.board[y][x] == 'b':
                    color = COLOR['BLUE']
                elif self.board[y][x] == 'w':
                    color = COLOR['WHITE']
                elif self.board[y][x] == 'o':
                    color = COLOR['ORANGE']
                elif self.board[y][x] == 'y':
                    color = COLOR['YELLOW']
                elif self.board[y][x] == 'p':
                    color = COLOR['PINK']
                elif self.board[y][x] == 'c':
                    color = COLOR['CYAN']
                else:
                    color = COLOR['BLACK']
                pygame.draw.rect(win, color, (width+(x*scale),
                                 height+(y*scale), scale, scale))


class Block:
    def __init__(self) -> None:
        self.pos_x = 4
        self.pos_y = 0
        self.color = COLOR["RED"]
        self.state = 0
        self.type = None
        self.acronome = '-'
        self.piece = [
            [[0, -1], [0, 0], [0, 1], [0, 2]],
            [[-1, 0], [0, 0], [1, 0], [2, 0]],
            [[0, 2], [0, 1], [0, 0], [0, -1]],
            [[2, 0], [1, 0], [0, 0], [-1, 0]]]

    def get_dimension(self):
        outline = []
        for i, j in self.piece[self.state % 4]:
            outline.append((self.pos_x+i, self.pos_y+j))
        return outline

    def rotate_right(self):
        self.state -= 1

    def rotate_left(self):
        self.state += 1

    def move_right(self):
        for i, j in self.get_dimension():
            if i < 9:
                move = True
            else:
                move = False
                return
        if move:
            self.pos_x += 1

    def move_left(self):
        for i, j in self.get_dimension():
            if i > 0:
                move = True
            else:
                move = False
                return
        if move:
            self.pos_x -= 1

    def check_end(self, board) -> bool:
        dimension = self.get_dimension()
        for x, y in dimension:
            try:
                if y == 19:
                    return True
                elif board.board[y+1][x] != '-':
                    return True
            except:
                print(f'except 3 :{y} {x}')
                return True
        return False

    def wall_kick(self, board, left=True):
        if left:
            piece = self.piece[(self.state+1) % 4]
        else:
            piece = self.piece[(self.state-1) % 4]
        left_valid = True
        right_valid = True
        is_valid = True
        dimension = []
        for i, j in piece:
            dimension.append((self.pos_x+i, self.pos_y+j))
        for x, y in dimension:
            if x == 0:
                is_valid = False
            try:
                if board[y][x] != '-':
                    is_valid = False
            except IndexError:
                is_valid = False
        if is_valid:
            return True
        else:
            for x, y in dimension:
                if x == 0:
                    left_valid = False
                try:
                    if board[y][x-1] != '-':
                        left_valid = False
                except IndexError:
                    left_valid = False
                try:
                    if board[y][x+1] != '-':
                        right_valid = False
                except IndexError:
                    right_valid = False
            if left_valid:
                self.move_left()
                return True
            if right_valid:
                self.move_right()
                return True
            if (not left_valid) and (not right_valid) and (not is_valid):
                return

    def check_left(self, board) -> bool:
        dimension = self.get_dimension()
        for x, y in dimension:
            try:
                if x <= 0:
                    return True
                elif board.board[y][x-1] != '-':
                    return True
            except:
                print(f'except 2 :{y} {x}')
                return True
        return False

    def check_right(self, board) -> bool:
        dimension = self.get_dimension()
        for x, y in dimension:
            try:
                if x >= 9:
                    return True
                elif board.board[y][x+1] != '-':
                    return True
            except:
                print(f'except 1 :{y} {x}')
                return True
        return False

    def move_down(self):
        self.pos_y += 1

    def draw(self, win, height, width, scale):
        for i, j in self.piece[self.state % 4]:
            if 0 <= (self.pos_y+j) <= 19:
                pygame.draw.rect(win, self.color, (width+((self.pos_x+i)*scale),
                                                   height+((self.pos_y+j)*scale), scale, scale))

    def draw_next(self, win):
        for i, j in self.piece[self.state % 4]:
            pygame.draw.rect(win, self.color, ((500+75)+(i*20),
                                               (75)+(j*20), 20, 20))


class LineBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[-1, 0], [0, 0], [1, 0], [2, 0]],
            [[1, -1], [1, 0], [1, 1], [1, 2]],
            [[-1, 1], [0, 1], [1, 1], [2, 1]],
            [[0, -1], [0, 0], [0, 1], [0, 2]]]
        self.color = COLOR["RED"]
        self.type = 1
        self.acronome = 'r'


class SquareBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[0, 0], [0, 1], [1, 0], [1, 1]],
            [[0, 0], [0, 1], [1, 0], [1, 1]],
            [[0, 0], [0, 1], [1, 0], [1, 1]],
            [[0, 0], [0, 1], [1, 0], [1, 1]]]
        self.color = COLOR["YELLOW"]
        self.type = 2
        self.acronome = 'y'


class JBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[-1, 0], [0, 0], [1, 0], [1, 1]],
            [[1, -1], [0, -1], [0, 0], [0, 1]],
            [[-1, -1], [-1, 0], [0, 0], [1, 0]],
            [[-1, 1], [0, 1], [0, 0], [0, -1]], ]
        self.color = COLOR["BLUE"]
        self.type = 3
        self.acronome = 'b'


class LBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[-1, 1], [-1, 0], [0, 0], [1, 0]],
            [[-1, -1], [0, -1], [0, 0], [0, 1]],
            [[-1, 0], [0, 0], [1, 0], [1, -1]],
            [[0, -1], [0, 0], [0, 1], [1, 1]], ]
        self.color = COLOR["ORANGE"]
        self.type = 4
        self.acronome = 'o'


class SBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[-1, 0], [0, 0], [0, -1], [1, -1]],
            [[0, -1], [0, 0], [1, 0], [1, 1]],
            [[-1, 1], [0, 1], [0, 0], [1, 0]],
            [[-1, -1], [-1, 0], [0, 0], [0, 1]], ]
        self.color = COLOR["PINK"]
        self.type = 5
        self.acronome = 'p'


class ZBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[-1, -1], [0, -1], [0, 0], [1, 0]],
            [[1, -1], [1, 0], [0, 0], [0, 1]],
            [[-1, 0], [0, 0], [0, 1], [1, 1]],
            [[0, -1], [0, 0], [-1, 0], [-1, 1]], ]
        self.color = COLOR["GREEN"]
        self.type = 6
        self.acronome = 'g'


class TBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.piece = [
            [[-1, 0], [0, 0], [1, 0], [0, 1]],
            [[-1, 0], [0, -1], [0, 0], [0, 1]],
            [[-1, 0], [0, 0], [0, -1], [1, 0]],
            [[0, -1], [0, 0], [1, 0], [0, 1]], ]
        self.color = COLOR["CYAN"]
        self.type = 7
        self.acronome = 'c'


def draw(win, block, board, score, level, total_row, nextblock, GRID_SIZE):
    win.fill(COLOR["BLACK"])
    pygame.draw.line(win, COLOR["WHITE"],
                     (500, 0), (500, HEIGHTGAME))
    board.draw(win, 0, 0, GRID_SIZE)
    block.draw(win, 0, 0, GRID_SIZE)
    nextblock.draw_next(win)
    win.blit(font.render(str(score), True, (255, 255, 255)),
             dest=(500+(WIDTHSCORE//2), HEIGHTGAME//2))
    win.blit(font.render(f'level : {level}', True, (255, 255, 255)), dest=(
        500, (HEIGHTGAME//1.5)))
    win.blit(font.render(f'row : {total_row}', True, (255, 255, 255)), dest=(
        500, (HEIGHTGAME//1.1)))
    pygame.display.update()
    pygame.display.flip()


def game_over(win, block, board, score, level, total_row, nextblock, GRID_SIZE):
    win.fill(COLOR["BLACK"])
    pygame.draw.line(win, COLOR["WHITE"],
                     (500, 0), (500, HEIGHTGAME))
    board.draw(win, 0, 0, GRID_SIZE)
    block.draw(win, 0, 0, GRID_SIZE)
    nextblock.draw_next(win)
    win.blit(font.render(str(score), True, (255, 255, 255)),
             dest=(500+(WIDTHSCORE//2), HEIGHTGAME//2))
    win.blit(font.render(f'level : {level}', True, (255, 255, 255)), dest=(
        500, (HEIGHTGAME//1.5)))
    win.blit(font.render(f'row : {total_row}', True, (255, 255, 255)), dest=(
        500, (HEIGHTGAME//1.1)))
    win.blit(font.render(f'generation : {pop.generation+1}', True, (255, 255, 255)), dest=(
        500, (HEIGHTGAME//1.7)))
    win.blit(font.render(f'GAMEOVER SCORE : {score}', True, (255, 255, 255)), dest=(
        0, HEIGHTGAME//2))
    pygame.display.update()
    pygame.display.flip()


def main():
    Pieces = [LineBlock, SquareBlock, SBlock, LBlock,
              JBlock, ZBlock, TBlock]
    GRID_SIZE = 50
    clock = pygame.time.Clock()
    lv_time = [2000, 1790, 1583, 1375, 1166, 958, 750, 541, 333, 250, 208, 208,
               208, 166, 166, 166, 125, 125, 125, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 41]
    Running = True
    score = 0
    t1 = 0
    t2 = 0
    total_row = 0
    level = 1
    gameover = False
    board = Board()
    block = random.choice(Pieces)()
    nextblock = random.choice(Pieces)()
    while Running:
        clock.tick(24)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    if not block.check_left(board):
                        block.move_left()
                if event.key == pygame.K_d:
                    if not block.check_right(board):
                        block.move_right()
                if event.key == pygame.K_SPACE:
                    while not block.check_end(board):
                        block.move_down()
                        score += 2
                if event.key == pygame.K_LEFT:
                    rotate = block.wall_kick(board.board, left=True)
                    if rotate:
                        block.rotate_left()
                if event.key == pygame.K_RIGHT:
                    rotate = block.wall_kick(board.board, left=False)
                    if rotate:
                        block.rotate_right()
        key = pygame.key.get_pressed()
        if not gameover:
            if key[pygame.K_s]:
                if not block.check_end(board):
                    block.move_down()
                    score += 1
            # move down
            row_done = 0
            t1 = pygame.time.get_ticks()
            if t1 - t2 > lv_time[level]:
                if not block.check_end(board):
                    block.move_down()
                else:
                    for x, y in block.get_dimension():
                        board.board[y][x] = block.acronome
                    for n, i in enumerate(board.board):
                        if not '-' in i:
                            board.board.pop(n)
                            board.board.insert(0, ['-' for i in range(10)])
                            row_done += 1
                    block = nextblock
                    nextblock = random.choice(Pieces)()
                t2 = t1

            total_row += row_done
            if row_done == 1:
                score += 40 * (level + 1)
            elif row_done == 2:
                score += 100 * (level + 1)
            elif row_done == 3:
                score += 300 * (level + 1)
            elif row_done == 4:
                score += 1200 * (level + 1)

            if board.board[0][5] != '-' or board.board[0][4] != '-' or board.board[0][3] != '-':
                gameover = True

            level = total_row//10

        if gameover:
            game_over(win, block, board, score, level, total_row, nextblock)
            if key[pygame.K_SPACE]:
                score = 0
                t1 = 0
                t2 = 0
                total_row = 0
                level = 1
                gameover = False
                board = Board()
                block = random.choice(Pieces)()
                nextblock = random.choice(Pieces)()
        else:
            draw(win, block, board, score, level,
                 total_row, nextblock, GRID_SIZE)


def draw_ai(win, blocks, boards, scores, ge, finalpos, gridsize):
    font = pygame.font.Font(pygame.font.get_default_font(), 24)
    width = 200
    height = 400
    win.fill(COLOR["BLACK"])
    pygame.draw.line(win, COLOR["WHITE"], (1000, 0), (1000, HEIGHTGAME))

    for i in range(len(blocks)):
        if i < 5:
            boards[i].draw(win, 0, width*i, gridsize)

            for j in range(len(finalpos[i])):
                pygame.draw.rect(win, COLOR['WHITE'],
                                 ((width*i)+(finalpos[i][j][0]*gridsize), (0+(finalpos[i][j][1]*gridsize)), gridsize, gridsize))
            blocks[i].draw(win, 0, width*i, gridsize)

        else:
            boards[i].draw(win, height, width*(i-5), gridsize)

            for j in range(len(finalpos[i])):
                pygame.draw.rect(win, COLOR['WHITE'], ((
                    width*(i-5))+finalpos[i][j][0]*gridsize, height+finalpos[i][j][1]*gridsize, gridsize, gridsize))
            blocks[i].draw(win, height, width*(i-5), gridsize)

    pygame.draw.line(win, COLOR["WHITE"], (200, 0), (200, HEIGHTGAME))
    pygame.draw.line(win, COLOR["WHITE"], (400, 0), (400, HEIGHTGAME))
    pygame.draw.line(win, COLOR["WHITE"], (600, 0), (600, HEIGHTGAME))
    pygame.draw.line(win, COLOR["WHITE"], (800, 0), (800, HEIGHTGAME))
    pygame.draw.line(win, COLOR["WHITE"], (0, 400), (1000, 400))

    max_score = max(scores)
    win.blit(font.render(f'generation : {pop.generation+1}', True, COLOR["WHITE"]), dest=(
        width*5, (HEIGHTGAME//10)*6))
    win.blit(font.render(f'max score : {max_score}', True, COLOR["WHITE"]), dest=(
        width*5, (HEIGHTGAME//10)*7))
    win.blit(font.render(f'best at : {scores.index(max_score)}', True, COLOR["WHITE"]), dest=(
        width*5, (HEIGHTGAME//10)*8))

    for i in range(len(ge)):
        win.blit(font.render(f'{i}:{int(ge[i].fitness)}', True, COLOR["WHITE"] if ge[i].fitness > 0 else COLOR["RED"]), dest=(
            width*5, (HEIGHTGAME//10)*(0.5*i)))
    pygame.display.update()
    pygame.display.flip()


def check_possible(board: Board, block, move, index):
    temp_board = Board()
    temp_board.board = deepcopy(board.board)
    block.state = index
    # temp_board = test board
    #block = [[1,1],[1,1],[1,1][1,1]]
    #move = (x,y)
    while block.pos_x != move[0]:
        if block.pos_x > move[0]:
            if not block.check_left(temp_board):
                block.move_left()
        elif block.pos_x < move[0]:
            if not block.check_right(temp_board):
                block.move_right()
    while not block.check_end(temp_board):
        block.move_down()
    if move == (block.pos_x, block.pos_y):
        return True
    else:
        return False


def generate_best_moves(board: Board, block: Block):
    possible_move = []
    """
    [
        [(x,y),(x,y),(x,y)],
        [(x,y),(x,y),(x,y)],
        [(x,y),(x,y),(x,y)],
        [(x,y),(x,y),(x,y)]
    ]
    """
    for ro, rotation in enumerate(block.piece):
        possible_move.append([])
        for y in range(block.pos_y, len(board.board)):
            for x in range(len(board.board[y])):
                valid_pos = True
                for pos in rotation:
                    try:
                        if (pos[0]+x) < 0:
                            valid_pos = False
                        if board.board[(pos[1]+y)][(pos[0]+x)] != "-":
                            valid_pos = False
                    except IndexError as e:
                        valid_pos = False
                if valid_pos:
                    end = [False, False, False, False]
                    for i, pos in enumerate(rotation):
                        if pos[1]+y == 19:
                            end[i] = True
                        elif board.board[pos[1]+y+1][pos[0]+x] != '-':
                            end[i] = True
                    if any(end):
                        possible_move[ro].append([x, y])
    return possible_move


def auto_placement(genomes, config):
    Pieces = [LineBlock, SquareBlock, SBlock, LBlock,
              JBlock, ZBlock, TBlock]
    clock = pygame.time.Clock()
    lv_time2 = [500, 450, 400, 350, 350, 350, 300, 300, 300, 300, 300, 275,
                275, 275, 275, 250, 250, 200, 150, 150, 150, 100, 100, 100, 100, 83, 83, 83, 83, 41]
    Running = True
    t1 = 0
    ge = []
    t2 = []
    nets = []
    blocks = []
    boards = []
    nextblocks = []
    scores = []
    game_end = []
    levels = []
    finalpos = []
    total_rows = []
    for genome_id, genome in genomes:
        boards.append(Board())
        blocks.append(random.choice(Pieces)())
        finalpos.append([[0, 0], [0, 0], [0, 0], [0, 0]])
        nextblocks.append(random.choice(Pieces)())
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        t2.append(0)
        game_end.append(False)
        genome.fitness = 0
        scores.append(0)
        levels.append(0)
        total_rows.append(0)
        ge.append(genome)
    while Running:
        clock.tick(90)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Running = False
        for i, board in enumerate(boards):
            row_dones = 0
            if not game_end[i]:
                possible_moves = generate_best_moves(boards[i], blocks[i])
                boards[i].update_outline()
                l_ = boards[i].height[:]
                for x, y in blocks[i].get_dimension():
                    l_.append(x)
                    l_.append(y)
                print(l_)
                output = net.activate(l_)

                to_best = []
                for index, rotations in enumerate(possible_moves):
                    to_best.append([])
                    for move in rotations:  # each position in rotation
                        score_to_best = 0
                        temp_board = Board()
                        temp_board.board = deepcopy(boards[i].board)
                        outline = blocks[i].piece[index]
                        # check_possible(temp_board, deepcopy(
                        #     blocks[i]), deepcopy(move), index)
                        for kkk in range(len(outline)):
                            temp_board.board[outline[kkk][1]+move[1]
                                             ][outline[kkk][0]+move[0]] = blocks[i].acronome

                        rowclear = 0
                        for x in temp_board.board:
                            if not '-' in x:
                                rowclear += 1
                        temp_board.update_outline()
                        score_to_best += output[0] * rowclear
                        score_to_best -= abs(output[1] * 10 * temp_board.holes)
                        score_to_best += output[2] * temp_board.height_penalty
                        score_to_best += output[3] * temp_board.bumpyness
                        score_to_best += output[4] * temp_board.touch_wall
                        to_best[index].append(score_to_best)
                py = to_best.index(max(to_best))
                px = max(to_best).index(max(max(to_best)))
                for kkk in range(4):
                    finalpos[i][kkk][0] = blocks[i].piece[py][kkk][0] + \
                        possible_moves[py][px][0]
                    finalpos[i][kkk][1] = blocks[i].piece[py][kkk][1] + \
                        possible_moves[py][px][1]

                mm = [False, False]
                if blocks[i].state % 4 != py:
                    rotate = blocks[i].wall_kick(board.board, left=True)
                    if rotate:
                        blocks[i].rotate_left()
                else:
                    mm[0] = True
                if blocks[i].pos_x > possible_moves[py][px][0]:
                    if not blocks[i].check_left(boards[i]):
                        blocks[i].move_left()
                elif blocks[i].pos_x < possible_moves[py][px][0]:
                    if not blocks[i].check_right(boards[i]):
                        blocks[i].move_right()
                else:
                    mm[1] = True

                if all(mm):
                    if not blocks[i].check_end(boards[i]):
                        blocks[i].move_down()
                        scores[i] += 2

                t1 = pygame.time.get_ticks()
                if t1 - t2[i] > lv_time2[levels[i]]:
                    if not blocks[i].check_end(boards[i]):
                        blocks[i].move_down()
                    else:
                        for x, y in blocks[i].get_dimension():
                            boards[i].board[y][x] = blocks[i].acronome
                        for n, x in enumerate(boards[i].board):
                            if not '-' in x:
                                boards[i].board.pop(n)
                                boards[i].board.insert(
                                    0, ['-' for i in range(10)])
                                row_dones += 1
                        blocks[i] = nextblocks[i]
                        ge[i].fitness += 10
                        nextblocks[i] = random.choice(Pieces)()
                    t2[i] = t1
                total_rows[i] += row_dones
                if row_dones == 1:
                    scores[i] += 40 * (levels[i] + 1)
                    ge[i].fitness += 40 * (levels[i] + 1)
                elif row_dones == 2:
                    scores[i] += 100 * (levels[i] + 1)
                    ge[i].fitness += 100 * (levels[i] + 1)
                elif row_dones == 3:
                    scores[i] += 300 * (levels[i] + 1)
                    ge[i].fitness += 300 * (levels[i] + 1)
                elif row_dones == 4:
                    scores[i] += 1200 * (levels[i] + 1)
                    ge[i].fitness += 1200 * (levels[i] + 1)
                levels[i] = total_rows[i]//10

                if boards[i].board[0][5] != '-' or boards[i].board[0][4] != '-' or boards[i].board[0][3] != '-':
                    game_end[i] = True
        if all(game_end):
            print(game_end)
            break
        draw_ai(win, blocks, boards, scores, ge, finalpos, gridsize=20)


def run_ai():
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        'config.txt'
    )

    pop = neat.Population(config)
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.run(main_ai, 50)


if __name__ == "__main__":
    # main
    # main()
    # neat
    # run_ai()
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        'config.txt'
    )

    pop = neat.Population(config)
    pop.run(auto_placement, 50)
