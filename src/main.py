import machine
import nodepixel
import time


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
    b = 1

    BLACK = (0, 0, 0)
    WHITE = (b, b, b)

    RED = (b, 0, 0)
    GREEN = (0, b, 0)
    BLUE = (0, 0, b)

    YELLOW = (b, b, 0)
    PURPLE = (b, 0, b)
    CYAN = (0, b, b)

    ORANGE = (b, int(b/2), 0)


class Player(object):
    colors = (
        Color.PURPLE,
        Color.BLUE,
        Color.CYAN,
        Color.GREEN,
        Color.YELLOW,
        Color.ORANGE,
        Color.RED,
        Color.WHITE,
    )

    max_score = 8

    def __init__(self, score_pin, paddle_pin, zone, game):
        self.zone = zone
        self.game = game
        self.np = nodepixel.NeoPixel(score_pin, self.max_score)
        self.paddle = paddle_pin

        self.score = 0

    def set_score(self, score):
        if score > self.max_score:
            return
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

    def render(self):
        if self.moving:
            previous = min(max(self.position - self.heading, 0), self.game.np.n - 1)
            self.game.np[previous] = Color.BLACK
        self.game.np[self.position] = Color.WHITE
        self.game.np.write()


class Pong(object):
    endzone = 2

    def __init__(self):
        self.np = nodepixel.NeoPixel(machine.Pin(Pinout.D4), 144)
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
        self.state = self.state_waiting

    def state_waiting(self):
        if self.current_player.active():
            self.ball.moving = True
            self.state = self.state_playing

    def state_playing(self):
        if self.ball.position in self.player1.zone:
            if self.player1.active():
                self.ball.heading = self.ball.HEADING_RIGHT
            elif self.ball.position == 0:
                self.player2.score += 1
                self.ball.position = self.np.n - 1
                self.ball.moving = False
                self.current_player = self.player2
                self.state = self.state_waiting
                self.np.clear()

        elif self.ball.position in self.player2.zone:
            if self.player2.active():
                self.ball.heading = self.ball.HEADING_LEFT
            elif self.ball.position == self.np.n - 1:
                self.player1.score += 1
                self.ball.position = 0
                self.ball.moving = False
                self.current_player = self.player1
                self.state = self.state_waiting
                self.np.clear()

        if self.ball.moving:
            self.ball.move()


        # if self.ball.position == 0 and not self.player1.active():
        #     self.player2.score += 1
        #     self.ball.position = self.np.n - 1
        #     self.ball.moving = False
        #     self.state = self.state_waiting
        # elif self.ball.position == (self.np.n - 1) and not self.player2.active():
        #     self.player1.score += 1
        #     self.ball.position = 0
        #     self.ball.moving = False
        #     self.state = self.state_waiting
        # else:
        #     self.ball.move()
        #     if self.ball.position in self.player1.zone and self.player1.active:
        #         self.ball.heading = self.ball.HEADING_RIGHT
        #     if self.ball.position in self.player2.zone and self.player2.active:
        #         self.ball.heading = self.ball.HEADING_LEFT

    def state_gameover(self):
        pass

    def loop(self):
        while True:
            self.state()
            self.render()

    def render(self):
        for obj in self.render_queue:
            obj.render()
        self.update_queue = set()
        # self.np.clear()
        # self.np[self.ball.position] = Color.WHITE
        # self.np.write()


if __name__ == '__main__':
    game = Pong()
    game.loop()
