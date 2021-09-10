# !/usr/bin/env python3
import json
import math


class Odometry:
    def __init__(self):
        """
        Initializes odometry module
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        pass

    def do(self):
        dx = 0
        dy = 0
        gamma = 0

        with open('../odometrie_json/handy_wilde_kurve_02.json', 'r') as reader:
            ticks = json.load(reader)

        # distance_per_tick = 14.5 / 300
        # distance_per_tick = 0.04833333333333333
        # wheel_distance = 15.6 # 15.6 15.6 15.6 15.6 15.6

        distance_per_tick = 14.5 / 300
        wheel_distance = 15.6

        ticks_delta = []
        last_element = ticks.pop(0)
        for i in ticks:
            ticks_delta.append((i[0] - last_element[0], i[1] - last_element[1]))
            last_element = i

        length_delta = []
        s_ges = 0
        for i in ticks_delta:
            dr = i[0] * distance_per_tick
            dl = i[1] * distance_per_tick
            alpha = (dr - dl) / wheel_distance
            beta = alpha / 2
            if alpha != 0:
                s = ((dr + dl) / alpha) * math.sin(beta)
            else:
                s = dr
            dx += -math.sin(gamma + beta) * s
            dy += math.cos(gamma + beta) * s
            s_ges += s
            gamma += alpha
            length_delta.append((s, alpha))

        print("New Orientation in degree: ", math.degrees(gamma))
        print("dx: ", dx)
        print("dy: ", dy)
        print("s_ges: ", s_ges)


        # distance = ticks * distance_per_tick


if __name__ == '__main__':
    o = Odometry()
    o.do()
