import numpy as np
from typing import Tuple

from .road_and_cars import BaseRoad, LineWLight, Line, Crossroad, Car


class CrossroadAndLines:

    def __init__(self, length, red, green, offset: int = 0, rotary_2: bool = False, name="Crossroad and lines"):
        lineW0 = LineWLight(length, length - 2, red, green, offset, name=name + "/LineWLight0")
        lineW1 = LineWLight(length, length - 2, red, green, offset, name=name + "/LineWLight1")
        lineW2 = LineWLight(length, length - 2, red, green, offset+(red+green)//2, name=name + "/LineWLight2")
        lineW3 = LineWLight(length, length - 2, red, green, offset+(red+green)//2, name=name + "/LineWLight3")

        line0 = Line(length, name=name + "/Line0")
        line1 = Line(length, name=name + "/Line1")
        line2 = Line(length, name=name + "/Line2")
        line3 = Line(length, name=name + "/Line3")

        self.crossroad = Crossroad(1, 1, 1, 1, rotary_2 = rotary_2, name=name + "/Crossroad")

        #     void = VoidGenerator(.8)

        lineW0.add_output(self.crossroad, 0, 0)
        lineW1.add_output(self.crossroad, 0, 1)
        lineW2.add_output(self.crossroad, 0, 2)
        lineW3.add_output(self.crossroad, 0, 3)

        self.crossroad.add_output(line0, 0)
        self.crossroad.add_output(line1, 1)
        self.crossroad.add_output(line2, 2)
        self.crossroad.add_output(line3, 3)

        self.input_roads = [lineW0, lineW1, lineW2, lineW3]
        self.output_roads = [line0, line1, line2, line3]

        self._history = []
        self.shuffle = True

    def add_car(self, car: Car, direction: int = 0):
        return self.input_roads[direction].add_car(car)

    def render(self):
        renders = list(map(lambda r: r.render(), self.input_roads + self.output_roads + [self.crossroad]))

        top = np.concatenate((np.zeros((renders[2].shape[1], renders[1].shape[1]), dtype="int32"),
                              np.flip(np.transpose(renders[2]), axis=1),
                              np.flip(np.transpose(renders[7]), axis=0),
                              np.zeros((renders[2].shape[1], renders[4].shape[1] + 1), dtype="int32")), axis=1)

        center = np.concatenate((np.vstack((np.zeros((1, renders[1].shape[1])),
                                            np.flip(renders[4], axis=1),
                                            renders[1])),
                                 renders[-1],
                                 np.vstack((np.flip(np.flip(renders[0], axis=1), axis=0),
                                            renders[5],
                                            np.zeros((1, renders[0].shape[1]))))
                                 ), axis=1)

        bottom = np.concatenate((np.zeros((renders[2].shape[1], renders[1].shape[1] + 1), dtype="int32"),
                                 np.flip(np.transpose(renders[6]), axis=1),
                                 np.flip(np.transpose(renders[3]), axis=0),
                                 np.zeros((renders[2].shape[1], renders[4].shape[1]), dtype="int32")), axis=1)

        return np.vstack((top, center, bottom))

    def move_cars(self, frame=0):
        for road in self.output_roads + self.input_roads + [self.crossroad]:
            road.move_cars(frame)

    def step(self, frame=0):
        for road in self.output_roads + self.input_roads + [self.crossroad]:
            road.step(frame)

    def process_outputs(self, frame=0):
        for road in self.output_roads + self.input_roads:
            road.process_output(frame)

        self.crossroad.process_outputs()
        self._history.append(self.render())

    def get_stats(self):
        stats = np.zeros((len(self._history), 4))
        for road in self.input_roads + self.output_roads:
            stats += np.array(road.get_stats())

        return stats


class CrossroadAndLines2x2: #(BaseRoad):

    def __init__(self, length, red, green, offsets=[0, 0, 0, 0], rotary_2: bool = False, name = "CrandLines2x2"):
        self.crossroad1 = CrossroadAndLines(length, red, green, offsets[0], rotary_2 = rotary_2, name=name + "/Cross0")
        self.crossroad2 = CrossroadAndLines(length, red, green, offsets[1], rotary_2 = rotary_2, name=name + "/Cross1")
        self.crossroad3 = CrossroadAndLines(length, red, green, offsets[2], rotary_2 = rotary_2, name=name + "/Cross2")
        self.crossroad4 = CrossroadAndLines(length, red, green, offsets[3], rotary_2 = rotary_2, name=name + "/Cross3")

        self.crossroad1.output_roads[1].add_output(self.crossroad2.input_roads[1], 0, 0)
        self.crossroad1.output_roads[2].add_output(self.crossroad3.input_roads[2], 0, 0)

        self.crossroad2.output_roads[0].add_output(self.crossroad1.input_roads[0], 0, 0)
        self.crossroad2.output_roads[2].add_output(self.crossroad4.input_roads[2], 0, 0)

        self.crossroad3.output_roads[1].add_output(self.crossroad4.input_roads[1], 0, 0)
        self.crossroad3.output_roads[3].add_output(self.crossroad1.input_roads[3], 0, 0)

        self.crossroad4.output_roads[0].add_output(self.crossroad3.input_roads[0], 0, 0)
        self.crossroad4.output_roads[3].add_output(self.crossroad2.input_roads[3], 0, 0)

        self.crossroads = [self.crossroad1, self.crossroad2, self.crossroad3, self.crossroad4]

        self._history = []
        self.shuffle = True

#     def add_car(self, car: Car, direction: int = 0):
#         return self.input_roads[direction].add_car(car)

    def render(self):
        cr1 = self.crossroad1.render()
        cr2 = self.crossroad2.render()
        cr3 = self.crossroad3.render()
        cr4 = self.crossroad4.render()

        top = np.concatenate((cr1, cr2), axis=1)
        bottom = np.concatenate((cr3, cr4), axis=1)

        return np.vstack((top, bottom))

    def move_cars(self, frame=0):
        for road in self.crossroads:
            road.move_cars(frame)

    def step(self, frame=0):
        for road in self.crossroads:
            road.step(frame)

    def process_outputs(self, frame=0):
        for road in self.crossroads:
            road.process_outputs(frame)

        self._history.append(self.render())

    def get_stats(self):
        stats = np.zeros((len(self._history), 4))
        for road in self.crossroads:
            stats += np.array(road.get_stats())

        return stats


class CrossroadAndLines4x4:  # (BaseRoad):

    def __init__(self, length, red, green, offsets=[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
                 rotary_2: bool = False, name="CrandLines2x2"):
        self.cross1 = CrossroadAndLines2x2(length, red, green, offsets[0], rotary_2=rotary_2, name=name + "/Cross0")
        self.cross2 = CrossroadAndLines2x2(length, red, green, offsets[1], rotary_2=rotary_2, name=name + "/Cross1")
        self.cross3 = CrossroadAndLines2x2(length, red, green, offsets[2], rotary_2=rotary_2, name=name + "/Cross2")
        self.cross4 = CrossroadAndLines2x2(length, red, green, offsets[3], rotary_2=rotary_2, name=name + "/Cross3")

        self.cross1.crossroad2.output_roads[1].add_output(self.cross2.crossroad1.input_roads[1], 0, 0)
        self.cross1.crossroad3.output_roads[2].add_output(self.cross3.crossroad1.input_roads[2], 0, 0)

        self.cross1.crossroad4.output_roads[1].add_output(self.cross2.crossroad3.input_roads[1], 0, 0)
        self.cross1.crossroad4.output_roads[2].add_output(self.cross3.crossroad2.input_roads[2], 0, 0)

        ################################################################
        self.cross2.crossroads[0].output_roads[0].add_output(self.cross1.crossroad2.input_roads[0], 0, 0)
        self.cross2.crossroads[2].output_roads[0].add_output(self.cross1.crossroad4.input_roads[0], 0, 0)
        self.cross2.crossroads[2].output_roads[2].add_output(self.cross4.crossroad1.input_roads[2], 0, 0)

        self.cross2.crossroads[3].output_roads[2].add_output(self.cross4.crossroad2.input_roads[2], 0, 0)

        ################################################################
        self.cross3.crossroads[0].output_roads[3].add_output(self.cross1.crossroad3.input_roads[3], 0, 0)

        self.cross3.crossroads[1].output_roads[1].add_output(self.cross4.crossroad1.input_roads[1], 0, 0)
        self.cross3.crossroads[1].output_roads[3].add_output(self.cross1.crossroad4.input_roads[3], 0, 0)
        self.cross3.crossroads[3].output_roads[1].add_output(self.cross4.crossroad3.input_roads[1], 0, 0)

        ################################################################
        self.cross4.crossroads[0].output_roads[0].add_output(self.cross3.crossroad2.input_roads[0], 0, 0)
        self.cross4.crossroads[0].output_roads[3].add_output(self.cross2.crossroad3.input_roads[3], 0, 0)

        self.cross4.crossroads[1].output_roads[3].add_output(self.cross2.crossroad4.input_roads[3], 0, 0)

        self.cross4.crossroads[2].output_roads[0].add_output(self.cross3.crossroads[3].input_roads[0], 0, 0)

        self.crossroads = [self.cross1, self.cross2, self.cross3, self.cross4]

        self._history = []
        self.shuffle = True

    #     def add_car(self, car: Car, direction: int = 0):
    #         return self.input_roads[direction].add_car(car)

    def render(self):
        cr1 = self.cross1.render()
        cr2 = self.cross2.render()
        cr3 = self.cross3.render()
        cr4 = self.cross4.render()

        top = np.concatenate((cr1, cr2), axis=1)
        bottom = np.concatenate((cr3, cr4), axis=1)

        return np.vstack((top, bottom))

    def move_cars(self, frame=0):
        for road in self.crossroads:
            road.move_cars(frame)

    def step(self, frame=0):
        for road in self.crossroads:
            road.step(frame)

    def process_outputs(self, frame=0):
        for road in self.crossroads:
            road.process_outputs(frame)

        self._history.append(self.render())

    def get_stats(self):
        stats = np.zeros((len(self._history), 4))
        for road in self.crossroads:
            stats += np.array(road.get_stats())

        return stats
    