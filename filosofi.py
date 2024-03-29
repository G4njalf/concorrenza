import queue
import time
from threading import Thread
import random
from threading import Semaphore


ch1 = Semaphore(1)
ch2 = Semaphore(1)
ch3 = Semaphore(1)
ch4 = Semaphore(1)
ch5 = Semaphore(1)



def philo1():
    while True:
        print('thinking1...')
        time.sleep(random.randrange(1,6))
        ch1.acquire()
        ch2.acquire()
        print('eating1...')
        time.sleep(random.randrange(1,6))
        ch1.release()
        ch2.release()

def philo2():
    while True:
        print('thinking2...')
        time.sleep(random.randrange(1,3))
        ch2.acquire()
        ch3.acquire()
        print('eating2...')
        time.sleep(random.randrange(1,3))
        ch2.release()
        ch3.release()

def philo3():
    while True:
        print('thinking3...')
        time.sleep(random.randrange(1,3))
        ch3.acquire()
        ch4.acquire()
        print('eating3...')
        time.sleep(random.randrange(1,3))
        ch3.release()
        ch4.release()

def philo4():
    while True:
        print('thinking4...')
        time.sleep(random.randrange(1,3))
        ch4.acquire()
        ch5.acquire()
        print('eating4...')
        time.sleep(random.randrange(1,3))
        ch4.release()
        ch5.release()

def philo5():
    while True:
        print('thinking5...')
        time.sleep(random.randrange(1,3))
        ch1.acquire()
        ch5.acquire()
        print('eating5...')
        time.sleep(random.randrange(1,3))
        ch1.release()
        ch5.release()


t1 = Thread(target=philo1)
t2 = Thread(target=philo2)
t3 = Thread(target=philo3)
t4 = Thread(target=philo4)
t5 = Thread(target=philo5)

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
