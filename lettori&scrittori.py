from pysm import semaphore
import queue
import time
from threading import Thread
import random

doc = 'pippo'

s1 = semaphore.semaphore()
s2 = semaphore.semaphore()
s3 = semaphore.semaphore()

nr = 0
nw = 0

def writer():
    if nr == 0 & nw == 0:
        nw += 1
        while True:
            s1.P()
            global doc
            doc = 'pluto'
        nw -= 1

def reader():
    if nw == 0:
        nr += 1
        while True:
            print(doc)
        nr -= 1
        

t1 = Thread(target=scrittore1,name='scritt1')
t3 = Thread(target=lettore,name='lett')

t1.start()
t3.start()

