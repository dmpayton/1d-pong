import neopixel

class NeoPixel(neopixel.NeoPixel):
    def clear(self):
        for x in range(self.n):
            self[x] = (0, 0, 0)
