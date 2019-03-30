from libc.stdlib cimport malloc, free, rand, RAND_MAX
import numpy as np

ctypedef struct pNumList:
    int value
    pNumList *next

ctypedef pNumList* NumList


cdef NumList add_head(NumList head, int value):
    cdef NumList new_head = <NumList>malloc(sizeof(pNumList))
    new_head.value = value
    new_head.next = head
    return new_head

cdef NumList add_node(NumList head, int value):
    cdef NumList new_node;
    if head == NULL:
        new_node = <NumList>malloc(sizeof(pNumList))
        new_node.value = value
        new_node.next = NULL
        return new_node
    elif head.value < value:
        new_node = <NumList>malloc(sizeof(pNumList))
        new_node.value = value
        new_node.next = head
        return new_node

    cdef NumList  prev = NULL, term = head;
    
    while term != NULL:
        if term.value == value :
            return head
        elif term.value < value:
            new_node = <NumList>malloc(sizeof(pNumList))
            new_node.value = value
            new_node.next = term
            if prev != NULL:
                prev.next = new_node
            return head
        prev = term
        term = term.next
    
    new_node = <NumList>malloc(sizeof(pNumList))
    new_node.value = value
    new_node.next = NULL
    if prev != NULL:
        prev.next = new_node
    return head

cdef NumList extend(NumList head, NumList additional):
    while additional != NULL:
        head = add_node(head, additional.value)
        additional = additional.next
    return head

cdef NumList get(NumList head, int index):
    cdef int counter = 0
    while head != NULL:
        if counter == index:
            return head
        head = head.next
        counter += 1
    return NULL

cdef NumList remove(NumList head, int value):
    cdef NumList term = head
    if head == NULL:
        return NULL
    elif head.value == value:
        term = head.next
        free(head)
        return term
    
    cdef NumList term2 = NULL, prev = NULL
    while term != NULL:
        if term.value == value:
            if prev != NULL:
                prev.next = term.next
            else:
                head = term.next
                free(term)
            return head
        else:
            prev = term
            term = term.next
    return head

cdef int length(NumList list_):
    cdef int count = 0
    while list_ != NULL:
        list_ = list_.next
        count += 1
    return count

cdef void delete_list(NumList head):
    cdef int count = 0
    cdef NumList next
    while head != NULL:
        next = head.next
        free(head)
        head = next


cdef int* random_array(int maximum):
    cdef int *array = <int*>malloc(sizeof(int)*maximum)
    cdef int t, counter = 0
    cdef Py_ssize_t i = 0, j

    while counter < maximum:
        array[counter] = counter
        counter += 1

    if maximum > 1:
        while i < maximum - 1:
            j = i + rand() / (RAND_MAX / (maximum - i) + 1)
            t = array[j]
            array[j] = array[i]
            array[i] = t
            i += 1

    return array


cdef class MyList:
    
    cdef NumList _list
    cdef int _length
    
    def __init__(self):
        self._list = NULL
        self._length = 0
    
    cpdef add(self, int val):
#         assert type(val) == int
        self._list = add_node(self._list, val)
        self._length = length(self._list)
        
    def length(self):
        return self._length
    
    def values(self):
        cdef NumList term = self._list
        while term != NULL:
            yield term.value
            term = term.next
            
    cpdef remove(self, int val):
        self._list = remove(self._list, val)
        self._length = length(self._list)

    cpdef get_first(self):
        return self._list.value

    def get(self, int index):
        assert 0<=index<=self._length
        cdef NumList answ =  get(self._list, index)
        return answ.value

    def extend(self, MyList additional):
        self._list = extend(self._list, additional._list)
        self._length = length(self._list)

    def clear(self):
        delete_list(self._list)
        self._list = NULL
        self._length = 0

    def shuffled(self):
        cdef int *indexes = random_array(self._length)
        cdef NumList answ
        for x in range(self._length):
            # assert 0<=x<=self._length
            answ =  get(self._list, indexes[x])
            assert answ != NULL
            yield answ.value

    def __length__(self):
        return self._length