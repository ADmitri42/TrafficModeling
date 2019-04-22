import numpy as np
from typing import List, Tuple
from road_network.utilities import OrderedUniqueList
from road_network.cars import CarManagerClass, speeds

CarManager = CarManagerClass()


class RoadManager:
    roads: List = []


class BaseRoad:

    def __init__(self, grid_size, shuffle: bool = False, name=None):
        self._road = np.zeros(grid_size, dtype="int32")
        self._next_state = self._road.copy()

        self._history: List[np.ndarray] = []
        self._inputs: List = []
        self._outputs: List = []
        self._cars = OrderedUniqueList()
        self._new_cars = OrderedUniqueList()
        self.shuffle = shuffle

        self._stats: List[Tuple] = []  # (speed, n_cells, n_cars, n_moved)

        self._name = name if name is not None else "road"
        RoadManager.roads.append(self)

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name

    def add_input(self, input_road, direction=0, index=0):
        if len(self._inputs) - 1 < direction:
            self._inputs.extend([None] * (direction - len(self._inputs) + 1))

        self._inputs[direction] = (input_road, index)

    def add_output(self, output_road, direction: int = 0, index: int = 0):
        # print(self, output_road, direction, index)
        if len(self._outputs) - 1 < direction:
            self._outputs.extend([None] * (direction - len(self._outputs) + 1))

        output_road.add_input(self, index, direction)
        self._outputs[direction] = (output_road, index)

    def add_car(self, car_id: int, direction: int = 0) -> int:
        """
        Add car on a road if input empty

        :param car_id: id of a car
        :param direction: index of input
        :return:
            0 if input is not empty and car cannot be processed
            1 otherwise
        """
        self._new_cars.add(car_id)
        return 1

    def _remove_car(self, car_id: int):
        self._cars.remove(car_id)

    def process_output(self, direction: int = 0):
        pass

    def process_outputs(self):
        return self.process_output()

    def render(self):
        return self._road.copy()

    def get_history(self, depth):
        if depth == 0:
            return [self.render()]

        return self._history[-depth:] + [self.render()]

    def is_empty(self, coords: np.ndarray):
        if coords.shape != (2,):
            raise ValueError("coords should be an array with 2 coordinates")
        return (self._road[coords[0], coords[1]] == 0) and (self._next_state[coords[0], coords[1]] == 0)

    def _get_state(self, coords: np.ndarray):
        if coords.shape != (2,):
            raise ValueError("coords should be an array with 2 coordinates")
        return self._next_state[coords[0], coords[1]]

    def set_state(self, coords: np.ndarray, state: int):
        if coords.shape != (2,):
            raise ValueError("coords should be an array with 2 coordinates")
        self._next_state[coords[0], coords[1]] = state

    def move_cars(self, frame=0):
        pass

    def step(self, time_step=0) -> Tuple:
        """
        Complete evaluation and calculate speed
        :param time_step:
        :return:
            tuple with n_cells, n_cars, n_moved_cars
        """
        #         if self.shuffle:
        #             np.random.shuffle(self._cars)

        self._history.append(self.render())
        self._road = self._next_state
        self._next_state = self._road.copy()

        self._cars.extend(self._new_cars)
        self._new_cars.clear()

        n_cars = self._cars.length()
        moved = ((self._history[-1] - self.render()) != 0).sum() / 2
        #         n_cars = n_cars if n_cars > moved else moved
        self._stats.append((self._road.shape[0] * self._road.shape[1], n_cars, moved))
        # print(2, type(self))
        return self._stats[-1]

    def get_stats(self):
        return self._stats


class VoidGenerator(BaseRoad):

    def __init__(self, p_new: int = 1, random_walk: bool = True, p_rot: List = None, first_n: int = 0, **kwargs):
        super(VoidGenerator, self).__init__((1, 1), name=kwargs.get("name", "void"))
        self.p_new = p_new
        self.random_walk = random_walk
        self.p_rot = p_rot if p_rot is not None else [.25, .25, .25, .25]
        self.first_n = first_n

    def add_output(self, output_road, direction: int = 0, index: int = 0):
        direction = len(self._outputs)
        output_road.add_input(self, index, direction)
        self._outputs.append((output_road, index))

    def process_output(self, direction: int = 0):

        if np.random.choice((0, 1), p=(1 - self.p_new, self.p_new)) == 0:
            return 1

        if self._cars.length() == 0:
            self._cars.add(CarManager.new_car())

        car_id = self._cars.get_first()
        if self.random_walk:
            #             car = CarManager.get_car(car_id)
            route = np.random.choice((0, 1, 2, 3), self.first_n, p=self.p_rot).tolist()
            route.extend(np.random.choice((0, 1, 2, 3), 20).tolist())
            CarManager.change_route(car_id, route)

        if self._outputs[direction][0].add_car(car_id, self._outputs[0][1]):
            self._cars.remove(car_id)
            # print("Crec")
            return 1
        return 0

    def process_outputs(self):
        for i in range(len(self._outputs)):
            if self._outputs[i] is None:
                continue
            self.process_output(i)

    def step(self, time_step=0):
        self._stats.append((0, 0, 0))
        return 0, 0, 0


class Line(BaseRoad):

    def __init__(self, length, **kwargs):
        super(Line, self).__init__((1, length), name=kwargs.get("name", "Line"))
        self.length = length
        self.beginning = np.array((0, 0))
        self.end = np.array((0, length - 1))

    def add_car(self, car_id: int, direction: int = 0) -> int:
        """
        Add car on a road if input empty

        :param car: car
        :param direction: index of input
        :return:
            0 if input is not empty
            1 otherwise
        """
        if self._get_state(self.beginning) != 0:
            return 0

        self._next_state[0, 0] = car_id
        #         car = CarManager.get_car(car_id)
        CarManager.set_position(car_id, self.beginning.copy())
        CarManager.set_speed(car_id, 4)
        return super(Line, self).add_car(car_id, direction)

    def render(self):
        return self._road

    def process_output(self, direction: int = 0) -> int:
        """

        :param direction:
        :return:
            1 if everything is OK
            0 otherwise
        """
        car_id = self._get_state(self.end)
        if car_id == 0:
            return 1

        #         if not (car_id in self._cars):
        #             self.set_state(self.end, 0)
        #             return 0

        # this = car.next_point_on_route()
        if self._outputs[0][0].add_car(car_id, self._outputs[0][1]):
            self.set_state(self.end, 0)
            self._remove_car(car_id)
            return 1

        # car.route.insert(0, this)
        return 0

    def move_cars(self, time_step=0):
        """
        :param time_step:
        :return:
        """
        if self.shuffle:
            for car_id in self._cars.shuffled():
                if (CarManager.position(car_id) == self.end).all():
                    continue
                CarManager.move(car_id, self)
        else:
            for car_id in self._cars.values():
                if (CarManager.position(car_id) == self.end).all():
                    continue
                CarManager.move(car_id, self)


class LineWLight(Line):

    def __init__(self,
                 length: int,
                 light_position: int,
                 red_dur: int,
                 green_dur: int,
                 time_offset: int=0,
                 **kwargs):
        super(LineWLight, self).__init__(length, name=kwargs.get("name", "LineWLights"));
        self.light_position = np.array((0, light_position))
        self.red_dur = red_dur
        self.green_dur = green_dur
        self.time_offset = time_offset
        # self.direction = direction
        self.light = int(time_offset%(red_dur+green_dur) < red_dur)

    def render(self):
        render = super(LineWLight, self).render()
        render = np.vstack((render, np.zeros_like(render)))
        render[1, self.light_position[-1]] = self.light + 2
        return render

    def move_cars(self, time_step=0):
        """
        :param time_step:
        :return:
        """
        self.light = int((time_step + self.time_offset) % (self.red_dur + self.green_dur) < self.red_dur)
        if self.shuffle:
            for car_id in self._cars.shuffled():
                if (CarManager.position(car_id) == self.end).all():
                    continue
                if (CarManager.position(car_id) == self.light_position).all() and self.light:
                    continue
                CarManager.move(car_id, self)
        else:
            for car_id in self._cars.values():
                if (CarManager.position(car_id) == self.end).all():
                    continue
                if (CarManager.position(car_id) == self.light_position).all() and self.light:
                    continue
                CarManager.move(car_id, self)

        # super(Line, self).step(time_step)

    def step(self, time_step=0) -> Tuple:
        """
        Complete evaluation and calculate speed
        :param time_step:
        :return:
            tuple with speed, n_cells, n_cars, n_moved_cars
        """
        if self.shuffle:
            np.random.shuffle(self._cars)

        self._history.append(self.render())
        self._road = self._next_state
        self._next_state = self._road.copy()

        self._cars.extend(self._new_cars)
        self._new_cars.clear()

        n_cars = self._cars.length()
        moved = ((self._history[-1][0] - self.render()[0]) != 0).sum()/2
#         n_cars = np.max(n_cars, moved)
        # speed = moved/n_cars if n_cars > 0 else 0
        self._stats.append((self._road.shape[0]*self._road.shape[1], n_cars, moved))
        # print(2, type(self))
        return self._stats[-1]


class Crossroad(BaseRoad):

    def __init__(self, n_left, n_right, n_bottom, n_top, **kwargs):
        super(Crossroad, self).__init__((2 + n_left + n_right, 2 + n_top + n_bottom), **kwargs)
        self.n_left = n_left
        self.n_right = n_right
        self.n_bottom = n_bottom
        self.n_top = n_top

        n = self.n_left + self.n_right + self.n_bottom + self.n_top
        self._outputs = [None] * n
        self._inputs = [None] * n

    def add_car(self, car_id: int, direction: int = 0):
        """
        Add car on a road if input empty

        :param car_id: car
        :param direction: index of input
        :return:
            0 if input is not empty
            1 otherwise
        """

        if direction < 0:
            raise ValueError("Direction must be non-negative")

        edge = self._road.shape
        if direction < self.n_left:
            coords = np.array((direction + 1, edge[1] - 1))
            speed = 2
        elif direction < self.n_left + self.n_right:
            coords = np.array((direction + 1, 0))
            speed = 4
        elif direction < self.n_left + self.n_right + self.n_bottom:
            coords = np.array((0, direction - self.n_left - self.n_right + 1))
            speed = 3
        elif direction < self.n_left + self.n_right + self.n_bottom + self.n_top:
            coords = np.array((edge[0] - 1, direction - self.n_left - self.n_right + 1))
            speed = 1
        else:
            raise ValueError("Direction must be less than {self.n_left + self.n_right + self.n_bottom + self.n_top}")

        if self._get_state(coords) != 0:
            return 0

        self.set_state(coords, car_id)
        CarManager.set_position(car_id, coords)
        CarManager.set_speed(car_id, speed)
        return super(Crossroad, self).add_car(car_id, direction)

    def process_output(self, direction: int = 0) -> int:
        """

        :param direction:
        :return:
            1 if everything is OK
            0 otherwise
        """
        if direction < 0:
            raise ValueError("Direction must be non-negative")

        edge = self._road.shape
        if direction < self.n_left:
            coords = np.array((direction + 1, 0))
        elif direction < self.n_left + self.n_right:
            coords = np.array((direction + 1, edge[1] - 1))
        elif direction < self.n_left + self.n_right + self.n_bottom:
            coords = np.array((edge[0] - 1, direction - self.n_left - self.n_right + 1))
        elif direction < self.n_left + self.n_right + self.n_bottom + self.n_top:
            coords = np.array((0, direction - self.n_left - self.n_right + 1))
        else:
            raise ValueError("Direction must be less than {self.n_left + self.n_right + self.n_bottom + self.n_top}")

        car_id = self._get_state(coords)
        if car_id == 0:
            return 1

        #         this = car.next_point_on_route()
        if self._outputs[direction][0].add_car(car_id, self._outputs[0][1]):
            self.set_state(coords, 0)
            self._remove_car(car_id)
            CarManager.next_point_on_route(car_id)
            return 1

        #         car.route.insert(0, this)
        return 0


    def process_outputs(self):
        n = self.n_left + self.n_right + self.n_bottom + self.n_top
        for i in range(n):
            if self._outputs[i] is None:
                continue
            self.process_output(i)

    def move_cars(self, time_step: int = 0):
        """
        :param time_step:
        :return:
        """
        vertical = self.n_bottom + self.n_top
        horizontal = self.n_left + self.n_right

        #         for car in self._cars:
        for car_id in self._cars.shuffled() if self.shuffle else self._cars.values():
            #             if (CarManager.position(car_id) == self.end).all():
            #                 continue

            ###########
            speed = CarManager.speed(car_id)
            hor_speed = (speed == speeds[2]).all() or (speed == speeds[4]).all()
            vert_speed = (speed == speeds[1]).all() or (speed == speeds[3]).all()
            coords = CarManager.position(car_id)

            if (speed == speeds[2]).all() and coords[1] == 0:
                continue
            elif (speed == speeds[4]).all() and coords[1] == horizontal + 1:
                continue
            elif (speed == speeds[1]).all() and coords[0] == 0:
                continue
            elif (speed == speeds[3]).all() and coords[0] == vertical + 1:
                continue

            CarManager.move(car_id, self)

            next_dest = CarManager.get_next_destination(car_id)
            if hor_speed and horizontal <= next_dest < vertical + horizontal:  # horizontal cars
                # print("1")
                if (coords == np.array((coords[0], 1 + next_dest - horizontal))).all():
                    if next_dest < vertical + self.n_bottom:  # to bottom
                        CarManager.set_speed(car_id, 3)
                        # print("3")
                    else:  # to top
                        CarManager.set_speed(car_id, 1)
            elif vert_speed and 0 <= next_dest < vertical + horizontal:
                # print("2")
                if (coords == np.array((1 + next_dest, coords[0]))).all():
                    if next_dest < self.n_left:
                        CarManager.set_speed(car_id, 2)
                    else:
                        CarManager.set_speed(car_id, 4)

    def step(self, time_step: int = 0):
        super(Crossroad, self).step(time_step)
        v1, v2, v3 = self._stats[-1]
        v1 -= 4
        self._stats[-1] = (v1, v2, v3)
        return self._stats[-1]
