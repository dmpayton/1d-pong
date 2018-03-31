import gc
import machine
import neopixel
import time

import random

gc.collect()

class Pinout(object):
    D0 = 16
    D1 = 5
    D2 = 4
    D3 = 0
    D4 = 2
    D5 = 14
    D6 = 12
    D7 = 13
    D8 = 15
    D9 = 3
    D10 = 1


class Color:
    b = 32

    BLACK = (0, 0, 0)
    WHITE = (b, b, b)

    RED = (b, 0, 0)
    GREEN = (0, b, 0)
    BLUE = (0, 0, b)

    YELLOW = (b, b, 0)
    PURPLE = (b, 0, b)
    CYAN = (0, b, b)

    ORANGE = (b, int(b/2), 0)

    @classmethod
    def random(cls):
        return random.choice((cls.RED, cls.GREEN, cls.BLUE, cls.YELLOW, cls.PURPLE, cls.CYAN, cls.ORANGE))


class NeoPixel(neopixel.NeoPixel):
    def clear(self):
        for x in range(self.n):
            self[x] = (0, 0, 0)


class Player(object):
    colors = (Color.PURPLE, Color.BLUE, Color.CYAN, Color.GREEN, Color.YELLOW, Color.ORANGE, Color.RED, Color.WHITE)

    max_score = 8

    def __init__(self, score_pin, paddle_pin, zone, game):
        self.zone = zone
        self.game = game
        self.np = NeoPixel(score_pin, self.max_score)
        self.paddle = paddle_pin
        # self.paddle.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.handle_paddle)

        self.score = 0

    def set_score(self, score):
        self._score = score
        self.game.render_queue.add(self)

    def get_score(self):
        return self._score

    score = property(get_score, set_score)

    def active(self):
        return not self.paddle.value()

    def render(self):
        self.np.clear()
        for x in range(self.score):
            self.np[x] = self.colors[x]
        self.np.write()


class Ball(object):
    HEADING_LEFT = -1
    HEADING_RIGHT = 1

    def __init__(self, game):
        self.game = game
        self.position = 0
        self.heading = self.HEADING_RIGHT
        self.moving = False
        self.game.render_queue.add(self)
        self.color = Color.WHITE

    def set_position(self, position):
        self._position = position
        self.game.render_queue.add(self)

    def get_position(self):
        return self._position

    position = property(get_position, set_position)

    def move(self):
        if not self.moving:
            return
        self.position = min(max(self.position + self.heading, 0), self.game.np.n - 1)

    def colorize(self):
        self.color = Color.random()
        if self.color == Color.BLACK:
            self.colorize()

    def render(self):
        if self.moving:
            previous = min(max(self.position - self.heading, 0), self.game.np.n - 1)
            self.game.np[previous] = Color.BLACK
        self.game.np[self.position] = self.color
        self.game.np.write()


class GameState(object):
    def __init__(self, game):
        self.game = game
        gc.collect()

    def tick(self):
        pass


class StateWaiting(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.game.ball.moving = False


    def tick(self):
        if self.game.current_player.active():
            self.game.ball.moving = True
            self.game.state = StatePlaying(self.game)

class StatePlaying(GameState):
    def tick(self):
        game = self.game
        ball = game.ball
        if ball.position in game.player1.zone:
            if game.player1.active():
                ball.heading = game.ball.HEADING_RIGHT
                # ball.colorize()
            elif ball.position == 0:
                game.player2.score += 1
                if game.player2.score == Player.max_score:
                    game.state = StateGameOver(game)
                else:
                    ball.position = game.np.n - 1
                    game.current_player = game.player2
                    game.state = StateWaiting(game)
                game.np.clear()

        elif ball.position in game.player2.zone:
            if game.player2.active():
                ball.heading = game.ball.HEADING_LEFT
                # ball.colorize()
            elif ball.position == game.np.n - 1:
                game.player1.score += 1
                if game.player1.score == Player.max_score:
                    game.state = StateGameOver(game)
                else:
                    ball.position = 0
                    game.current_player = game.player1
                    game.state = StateWaiting(game)
                game.np.clear()

        if ball.moving:
            ball.move()


class StateGameOver(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.counter = 0
        if game.player1.score == Player.max_score:
            self.winner = game.player1
            self.loser = game.player2
        else:
            self.winner = game.player2
            self.loser = game.player1

        self.loser.score = 0

    def tick(self):
        self.counter += 1
        if self.counter == 5:
            self.winner.score = 0 if self.winner.score else Player.max_score
            self.counter = 0
        self.game.render_queue.add(self)

    def render(self):
        self.game.np[random.randint(0, self.game.np.n - 1)] = random.choice((Color.random(), Color.BLACK))
        self.game.np.write()


class Pong(object):
    endzone = 2

    def __init__(self):
        self.np = NeoPixel(machine.Pin(Pinout.D4), 144)
        self.render_queue = set()

        self.player1 = Player(
            score_pin=machine.Pin(Pinout.D1),
            paddle_pin=machine.Pin(Pinout.D2, machine.Pin.IN, machine.Pin.PULL_UP),
            zone=list(range(0, self.endzone)),
            game=self,
        )

        self.player2 = Player(
            score_pin=machine.Pin(Pinout.D7),
            paddle_pin=machine.Pin(Pinout.D6, machine.Pin.IN, machine.Pin.PULL_UP),
            zone=list(range(self.np.n - self.endzone, self.np.n)),
            game=self,
        )

        self.ball = Ball(self)
        self.current_player = self.player1
        self.state = StateWaiting(self)

    def loop(self):
        while True:
            self.state.tick()
            self.render()

    def render(self):
        for obj in self.render_queue:
            obj.render()
        self.update_queue = set()

if __name__ == '__main__':
    game = Pong()
    game.loop()
