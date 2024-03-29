#from pysm import semaphore
import queue
import time
from threading import Thread
from threading import Semaphore
import random

# Inizializzazione: Il semaforo viene inizializzato con un valore intero e positivo.

# Operazione P o wait: Il semaforo viene decrementato. Se, dopo il decremento, il semaforo ha un valore negativo, 
# il task viene sospeso e accodato, in attesa di essere riattivato da un altro task.

# Operazione V o signal: Il semaforo viene incrementato. Se ci sono task in coda, uno dei task in coda 
# (il primo nel caso di accodamento FIFO) viene tolto dalla coda, posto in stato di ready 
# (sarà perciò eseguito appena schedulato dal sistema operativo) e richiama P per decrementare.

s1 = Semaphore(1)
s2 = Semaphore(0)
l = list()

def producer():
    global l
    while True:
        s1.acquire()
        l.insert(1,5) # CRITICAL SECTION
        print(l) # CRITICAL SECTION
        s2.release()

        

def consumer():
    global l
    while True:
        s2.acquire()
        l.pop() # CRITICAL SECTION
        print(l) # CRITICAL SECTION
        s1.release()

t1 = Thread(target=producer,name='prod')
t2 = Thread(target=consumer,name='cons')


t1.start()
t2.start()







