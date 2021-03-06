from typing import List, Tuple
import numpy as np

MAX_WAITING_TIME = 2
speeds = [np.array([0, 0]), np.array([-1, 0]), np.array([0, -1]), np.array([1, 0]), np.array([0, 1])]


class CarManager:
    all_cars: List = [None]


class RoadManager:
    roads: List = []
    dict_road: dict = {}

    @staticmethod
    def add_road(road):
        if RoadManager.dict_road.get(str(road)) is not None:
            raise NameError("Name {} is taken".format(str(road)))
        RoadManager.dict_road[str(road)] = road
        RoadManager.roads.append(road)

    @staticmethod
    def connect_roads(road1, road2, road2_direction: int = 0, road1_direction: int = 0):
        """
        Direct cars from road1 to road2
        :param road1:
        :param road2:
        :param road2_direction:
        :param road1_direction:
        :return:
        """
        road1.add_output(road2, road1_direction, road2_direction)

    @staticmethod
    def connect_roads_str(name_road1: str, name_road2: str, road2_direction: int = 0, road1_direction: int = 0):
        if RoadManager.dict_road.get(name_road1) is None:
            raise NameError("Road {} isn't exist".format(name_road1))
        if RoadManager.dict_road.get(name_road2) is None:
            raise NameError("Road {} isn't exist".format(name_road2))
        road1 = RoadManager.dict_road.get(name_road1)
        road2 = RoadManager.dict_road.get(name_road2)
        road1.add_output(road2, road1_direction, road2_direction)


class Car:
    route = []
    coords = np.array([0, 0])
    speed = speeds[0]
    speed_code = 0
    to_output = 0

    def __init__(self, route: List[int] = None, destination_id: int = -1, rotate_in_case: bool = False):
        """

        :param route: list with no. of an output on every crossroad
        """
        self._hist = []
        self.counter = 0
        self.moves = 0
        self.id = len(CarManager.all_cars)
        CarManager.all_cars.append(self)

        self.route = route if route is not None else []
        self.destination = destination_id
        self.rotate = rotate_in_case

    def position(self):
        """
        :return: coordinates of a car
        """
        return self.coords

    def set_position(self, coords: np.ndarray):
        self.coords = coords

    def set_speed(self, new_speed: int):
        """
        Change speed of a car
        :param new_speed: new speed
        """
        if type(new_speed) != int:
            raise TypeError

        self.speed_code = new_speed

        self.speed = speeds[new_speed]

    def get_next_destination(self):
        if len(self.route) > 0:
            return self.route[0]
        else:
            return -1

    def next_point_on_route(self):
        if len(self.route) > 0:
            return self.route.pop(0)

        return -1

    def move(self, road):
        """
        Move a car on a trafic greed if possible
        :param road: road class on which moving
        """
        if road.is_empty(self.coords + self.speed) > 0:
            road.set_state(self.coords, 0)
            road.set_state(self.coords + self.speed, self.id)
            self.coords += self.speed
            self.counter = 0
            self.moves += 1
        else:
            self.counter += 1
        # self._hist.append(self.speed_code)


class BaseRoad:

    def __init__(self, grid_size, shuffle: bool = True, name=None):
        self._road = np.zeros(grid_size, dtype="int32")
        self._next_state = self._road.copy()

        self._history: List[np.ndarray] = []
        self._inputs: List = []
        self._outputs: List = []
        self._cars: List[Car] = []
        self._new_cars: List[Car] = []
        self.shuffle = shuffle

        self._stats: List[Tuple] = []  # (speed, n_cells, n_cars, n_moved)

        self._name = name if name is not None else "road"
        RoadManager.add_road(self)

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name

    def add_input(self, input_road, direction=0, index=0):
        if len(self._inputs) - 1 < direction:
            self._inputs.extend([None]*(direction - len(self._inputs) + 1))

        self._inputs[direction] = (input_road, index)

    def add_output(self, output_road, direction: int = 0, inp_road_direction: int = 0):
        # print(self, output_road, direction, index)
        if len(self._outputs) - 1 < direction:
            self._outputs.extend([None]*(direction - len(self._outputs) + 1))

        output_road.add_input(self, inp_road_direction, direction)
        self._outputs[direction] = (output_road, inp_road_direction)

    def _get_car(self, car_id: int) -> Car:
        car = list(filter(lambda x: x.id == car_id, self._cars))
        if len(car) == 0:
            return None
        return car[0]

    def add_car(self, car: Car, direction: int = 0) -> int:
        """
        Add car on a road if input empty

        :param car: car
        :param direction: index of input
        :return:
            0 if input is not empty and car cannot be processed
            1 otherwise
        """
        self._new_cars.append(car)
        return 1

    def add_car_at_position_w_speed(self, cars: List[Car]):
        for car in cars:
            self.set_state(car.position(), car.id)
            self._cars.append(car)

    def _remove_car(self, car_id: int):
        car = self._get_car(car_id)
        ind = list(map(lambda x: x[1], filter(lambda x: x[0].id == car_id, zip(self._cars, range(len(self._cars))))))
        if len(ind) == 0:
            return 0
        self._cars.pop(ind[0])
        # return car[0]
        # try:
        #     self._cars.remove(car)
        return 1
        # except ValueError:
        #     return 0

    def process_output(self, direction: int = 0):
        pass

    def process_outputs(self):
        return self.process_output()

    def render(self, moment: int = -1):
        if moment < 0:
            return self._road.copy()
        elif moment < len(self._history):
            return self._history[moment].copy()
        else:
            raise IndexError("No such a moment")

    def get_history(self, depth):
        if depth == 0:
            return [self.render()]

        return self._history[-depth:] + [self.render()]

    def is_empty(self, coords: np.ndarray):
        if 0 <= coords[0] < self._road.shape[0] and 0 <= coords[1] < self._road.shape[1]:
            return int((self._road[coords[0], coords[1]] == 0) and (self._next_state[coords[0], coords[1]] == 0))
        else:
            return -1

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
            tuple with speed, n_cells, n_cars, n_moved_cars
        """
        if self.shuffle:
            np.random.shuffle(self._cars)

        self._history.append(self.render())
        self._road = self._next_state
        self._next_state = self._road.copy()

        self._cars.extend(self._new_cars)
        self._new_cars = []

        n_cars = np.sum(self._road != 0)
        moved = ((self._history[-1] - self.render()) != 0).sum() // 2
        # n_cars = np.max(n_cars, moved)
        self._stats.append((self._road.shape[0]*self._road.shape[1], n_cars, moved))
        # print(2, type(self))
        return self._stats[-1]

    def get_stats(self):
        return self._stats


class VoidGenerator(BaseRoad):

    def __init__(self, p_new: int = 1,
                 random_walk: bool = False,
                 p_rot: List = None,
                 first_n: int = 0,
                 rotate_in_case: bool = False, **kwargs):

        super(VoidGenerator, self).__init__((1, 1), name=kwargs.get("name", "void"))
        self.p_new = p_new
        self.random_walk = random_walk
        self.p_rot = p_rot if p_rot is not None else [.25, .25, .25, .25]
        if type(self.p_rot[0]) != list:
            self.p_rot = [self.p_rot]*first_n
        self.rotate = rotate_in_case
        self.path_length = []

    def add_output(self, output_road, direction: int = 0, inp_road_direction: int = 0):
        direction = len(self._outputs)
        output_road.add_input(self, inp_road_direction, direction)
        self._outputs.append((output_road, inp_road_direction))

    def add_car(self, car: Car, direction: int = 0) -> int:
        # super(VoidGenerator, self).add_car(car, direction)
        self._cars.append(car)
        self.path_length.append(car.moves + 1)
        car.moves = 0
        return 1

    def process_output(self, direction: int = 0):

        if np.random.choice((0, 1), p=(1-self.p_new, self.p_new)) == 0:
            return 1

        if len(self._cars) == 0:
            self._cars.append(Car(rotate_in_case=self.rotate))

        car = self._cars.pop()
        if self.random_walk:
            car.route = []
            for p in self.p_rot:
                car.route.extend(np.random.choice((0, 1, 2, 3), 1, p=p).tolist())
            car.route.extend(np.random.choice((0, 1, 2, 3), 100-len(self.p_rot)).tolist())

        if self._outputs[direction][0].add_car(car, self._outputs[0][1]):
            # car.moves += 1
            return 1

        self._cars.append(car)
        return 0

    def process_outputs(self):
        # self._cars.extend(self._new_cars)
        # self._new_cars = []
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
        self.end = np.array((0, length-1))

    def add_car(self, car: Car, direction: int = 0) -> int:
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

        self._next_state[0, 0] = car.id
        car.set_position(self.beginning.copy())
        car.set_speed(4)
        car.moves += 1
        return super(Line, self).add_car(car, direction)

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

        car = self._get_car(car_id)
        if car is None:
            self.set_state(self.end, 0)
            return 0

        # this = car.next_point_on_route()
        if self._outputs[0][0].add_car(car, self._outputs[0][1]):
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
        for car in self._cars:
            if (car.position() == self.end).all():
                continue
            car.move(self)
            
        # super(Line, self).step(time_step)


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
        for car in self._cars:
            if (car.position() == self.end).all():
                continue

            if (car.position() == self.light_position).all() and self.light:
                continue
            car.move(self)

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
        self._new_cars = []

        n_cars = np.sum(self._road != 0)
        moved = ((self._history[-1][0] - self.render()[0]) != 0).sum()/2
        # n_cars = np.max(n_cars, moved)
        # speed = moved/n_cars if n_cars > 0 else 0
        self._stats.append((self._road.shape[0]*self._road.shape[1], n_cars, moved))
        # print(2, type(self))
        return self._stats[-1]


class Crossroad(BaseRoad):
    
    def __init__(self, n_left, n_right, n_bottom, n_top, rotary_2: bool = False, **kwargs):
        super(Crossroad, self).__init__((2+n_left+n_right, 2+n_top+n_bottom), name=kwargs.get("name", "crossroad"))
        self.n_left = n_left
        self.n_right = n_right
        self.n_bottom = n_bottom
        self.n_top = n_top

        n = self.n_left + self.n_right + self.n_bottom + self.n_top
        self._outputs = [None] * n
        self._inputs = [None] * n
        self.rotary_rule_2 = rotary_2

    def add_car(self, car: Car, direction: int = 0) -> int:
        """
        Add car on a road if input empty

        :param car: car
        :param direction: index of input
        :return:
            0 if input is not empty
            1 otherwise
        """

        if direction < 0:
            raise ValueError("Direction must be non-negative")

        edge = self._road.shape
        if direction < self.n_left:
            coords = np.array((direction+1, edge[1]-1))
            speed = 2
        elif direction < self.n_left + self.n_right:
            coords = np.array((direction+1, 0))
            speed = 4
        elif direction < self.n_left + self.n_right + self.n_bottom:
            coords = np.array((0, direction - self.n_left - self.n_right+1))
            speed = 3
        elif direction < self.n_left + self.n_right + self.n_bottom + self.n_top:
            coords = np.array((edge[0]-1, direction - self.n_left - self.n_right+1))
            speed = 1
        else:
            raise ValueError("Direction must be less than {self.n_left + self.n_right + self.n_bottom + self.n_top}")

        if self._get_state(coords) != 0:
            return 0

        self.set_state(coords, car.id)
        car.set_position(coords)
        car.set_speed(speed)
        car.moves += 1
        return super(Crossroad, self).add_car(car, direction)
    
    def is_empty(self, coords: np.ndarray):
        if coords[0] == 0 and (coords[1] == 0 or coords[1] == self._road.shape[1]-1):
            return -1
        elif coords[1] == 0 and (coords[0] == 0 or coords[0] == self._road.shape[0]-1):
            return -1
        elif coords[1] == self._road.shape[1]-1 and coords[0] == self._road.shape[0]-1:
            return -1
        return super(Crossroad, self).is_empty(coords)

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
            coords = np.array((direction+1, 0))
        elif direction < self.n_left + self.n_right:
            coords = np.array((direction+1, edge[1]-1))
        elif direction < self.n_left + self.n_right + self.n_bottom:
            coords = np.array((edge[0]-1, direction - self.n_left - self.n_right+1))
        elif direction < self.n_left + self.n_right + self.n_bottom + self.n_top:
            coords = np.array((0, direction - self.n_left - self.n_right+1))
        else:
            raise ValueError("Direction must be less than {self.n_left + self.n_right + self.n_bottom + self.n_top}")

        car_id = self._get_state(coords)
        if car_id == 0:
            return 1

        car = self._get_car(car_id)
        if car is None:
            self.set_state(coords, 0)
            return 0

        this = car.next_point_on_route()
        if self._outputs[direction][0].add_car(car, self._outputs[0][1]):
            self.set_state(coords, 0)
            self._remove_car(car_id)
            return 1

        car.route.insert(0, this)
        return 0

    def process_outputs(self):
        n = self.n_left + self.n_right + self.n_bottom + self.n_top
        for i in range(n):
            if self._outputs[i] is None:
                continue
            self.process_output(i)

    def move_cars(self, time_step=0):
        """
        :param time_step:
        :return:
        """
        vertical = self.n_bottom + self.n_top
        horizontal = self.n_left + self.n_right

        for car in self._cars:
            hor_speed = car.speed_code == 2 or car.speed_code == 4
            vert_speed = car.speed_code == 1 or car.speed_code == 3
            coords = car.position()

            if car.speed_code == 2 and coords[1] == 0:
                continue
            elif car.speed_code == 4 and coords[1] == horizontal+1:
                continue
            elif car.speed_code == 1 and coords[0] == 0:
                continue
            elif car.speed_code == 3 and coords[0] == vertical+1:
                continue

            car.move(self)

            next_dest = car.get_next_destination()

            if coords[0] == 0 or car.coords[1] == 0 or coords[0] == self._road.shape[0] or coords[1] == self._road.shape[1]:
                continue

            elif self.rotary_rule_2 and self._road.shape == (4, 4):
                # print(car.id)
                if np.random.choice((0, 1)):
                    # print(car.id)
                    if (car.position() == np.array([1, 1])).all():
                        if car.speed_code == 2:
                            car.set_speed(3)
                        elif car.speed_code == 3:
                            car.set_speed(2)
                    elif (car.position() == np.array([1, 2])).all():
                        if car.speed_code == 2:
                            car.set_speed(1)
                        elif car.speed_code == 1:
                            car.set_speed(2)
                    elif (car.position() == np.array([2, 1])).all():
                        if car.speed_code == 3:
                            car.set_speed(4)
                        elif car.speed_code == 4:
                            car.set_speed(3)
                    elif (car.position() == np.array([2, 2])).all():
                        if car.speed_code == 1:
                            car.set_speed(4)
                        elif car.speed_code == 4:
                            car.set_speed(1)

            elif car.rotate and car.counter > MAX_WAITING_TIME:
                if car.speed_code%2 == 0:
                    if coords[1] < self.n_bottom + 1 and self.is_empty(coords + speeds[3]):
                        car.set_speed(3)
                    elif self.n_bottom < coords[1] and self.is_empty(coords + speeds[1]):
                        car.set_speed(1)
                elif (car.speed_code+1)%2 == 0:
                    if coords[0] < self.n_left + 1 and self.is_empty(coords + speeds[2]):
                        car.set_speed(2)
                    elif self.n_left < coords[0] and self.is_empty(coords + speeds[4]):
                        car.set_speed(4)
                car.counter = 0

            elif hor_speed and horizontal <= next_dest < vertical + horizontal: # horizontal cars
                # print("1")
                if (coords == np.array((coords[0], 1+next_dest - horizontal))).all():
                    if next_dest < vertical + self.n_bottom:  # to bottom
                        car.set_speed(3)
                        # print("3")
                    else:                           # to top
                        car.set_speed(1)

            elif vert_speed and 0 <= next_dest < vertical + horizontal:
                # print("2")
                if (coords == np.array((1 + next_dest, coords[0]))).all():
                    if next_dest < self.n_left:
                        car.set_speed(2)
                    else:
                        car.set_speed(4)

    def step(self, time_step=0):
        super(Crossroad, self).step(time_step)
        v1, v2, v3 = self._stats[-1]
        v1 -= 4
        self._stats[-1] = (v1, v2, v3)
        return self._stats[-1]

    @property
    def border(self):
        return self._road.shape
