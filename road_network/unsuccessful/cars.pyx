from libc.stdlib cimport malloc, realloc, free, rand, RAND_MAX
import numpy as np

STEP_SIZE = 10

speeds = np.array([[0, 0], [-1, 0], [0, -1], [1, 0], [0, 1]])


##############
#
#
#   List for route
#
#
##############

ctypedef struct pLinkedList:
    int value
    pLinkedList *next

ctypedef pLinkedList* LinkedList

cdef LinkedList add_lhead(LinkedList head, int value):
    cdef LinkedList new_node = <LinkedList>malloc(sizeof(pLinkedList))
    new_node.next = head
    new_node.value = value
    return new_node

cdef LinkedList remove_lhead(LinkedList head):
    if head == NULL:
        return NULL
    cdef LinkedList next_node = head.next
    free(head)
    return next_node

cdef void delete_llist(LinkedList head):
    cdef LinkedList tmp
    while head != NULL:
        tmp = head.next
        free(head)
        head = tmp


##############
#
#
#   Cars
#
#
##############

ctypedef struct pCarStruct:
    LinkedList route
    int x_coord
    int y_coord

    int x_speed
    int y_speed

ctypedef pCarStruct* CarStruct

##############
#
#
#   Car Manager
#
#
##############

cdef class CarManagerClass:
    # all_cars = [None]
    cdef CarStruct* all_cars
    cdef int size
    cdef int max_size

    # @staticmethod
    # def get_car(car_id: int):
    #     assert 0 < car_id < len(CarManager.all_cars)
    #     return CarManager.all_cars[car_id-1]

    def __init__(self):
        self.all_cars = <CarStruct*>malloc(sizeof(CarStruct)*STEP_SIZE)
        self.size = 0
        self.max_size = STEP_SIZE

    def new_car(self, route = None):
        """

        :param route: list with no. of an output on every crossroad
        """
        if self.size == self.max_size:
            self.max_size += STEP_SIZE
            self.all_cars = <CarStruct*>realloc(self.all_cars, sizeof(CarStruct)*self.max_size)

        self.all_cars[self.size] = <CarStruct>malloc(sizeof(pCarStruct))
        cdef CarStruct car = self.all_cars[self.size]
        car.route = NULL
        car.x_coord = 0
        car.y_coord = 0
        car.x_speed = 0
        car.y_speed = 0

        # self._id = len(CarManager.all_cars)
        # CarManager.all_cars.append(self)

        if route is not None:
            for i in route:
                car.route = add_lhead(car.route, i)

        self.size += 1
        return self.size

    def position(self, int car_id):
        """
        :return: coordinates of a car
        """
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))

        return np.array([self.all_cars[car_id-1].x_coord,
                         self.all_cars[car_id-1].y_coord])

    def speed(self, int car_id):
        """
        :return: coordinates of a car
        """
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))

        return np.array([self.all_cars[car_id-1].x_speed,
                         self.all_cars[car_id-1].y_speed])

    def set_position(self, int car_id, coords):
        assert coords.shape[0] == 2
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))

        self.all_cars[car_id-1].x_coord = coords[0]
        self.all_cars[car_id-1].y_coord = coords[1]

    def change_route(self, int car_id, list new_route):
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))
        cdef CarStruct car = self.all_cars[car_id-1]
        delete_llist(car.route)
        car.route = NULL

        for i in new_route:
            car.route = add_lhead(car.route, i)

    def set_speed(self, int car_id, new_speed):
        """
        Change speed of a car
        :param new_speed: new speed
        """
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))
        cdef CarStruct car = self.all_cars[car_id-1]

        if type(new_speed) == int:
            new_speed = speeds[new_speed]
        elif type(new_speed) != np.ndarray:
            new_speed = np.array(new_speed)

        assert new_speed.shape[0] == 2

        car.x_speed = new_speed[0]
        car.y_speed = new_speed[1]

    def get_next_destination(self, int car_id):
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))
        cdef CarStruct car = self.all_cars[car_id-1]

        if car.route != NULL:
            return car.route.value
        else:
            return -1

    def next_point_on_route(self, int car_id):
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))
        cdef CarStruct car = self.all_cars[car_id-1]

        cdef LinkedList tmp = NULL
        cdef int val = -1
        if car.route != NULL:
            val = car.route.value
            car.route = remove_lhead(car.route)

        return val

    def move(self, int car_id, road):
        """
        Move a car on a traffic greed if possible
        :param road: road class on which moving
        """
        if 0 > car_id or car_id > self.size:
            raise IndexError("Wrong car id({}), max {}".format(car_id, self.size))
        cdef CarStruct car = self.all_cars[car_id-1]

        try:
            next_coord = np.array([car.x_coord + car.x_speed, car.y_coord + car.y_speed])
            if road.is_empty(next_coord):
                road.set_state(self.position(car_id), 0)
                road.set_state(next_coord, car_id)

                car.x_coord = car.x_coord + car.x_speed
                car.y_coord = car.y_coord + car.y_speed
        except IndexError:
            pass
        
    def delete(self):
        if self.all_cars != NULL:
            for i in range(self.size):
                free(self.all_cars[i])
            free(self.all_cars)
            self.all_cars = NULL