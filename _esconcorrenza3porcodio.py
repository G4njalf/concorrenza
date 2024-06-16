from pysm import monitor
from threading import Thread
from threading import Semaphore
import time

class safeprint(monitor.monitor):
	def __init__(self):
		super().__init__()

	@monitor.entry
	def print(self, *args,**kwargs):
		print(*args,**kwargs)

safeprint = safeprint().print

'''
Scrivere il monitor rgbsum che fornisce una procedure entry:
#define red 0
#define green 1
#define blue 2
double rgb(int color, double value)
I processi che usano il monitor rgbsum devono sommare i valori delle sequenze di chiamate dello stesso colore (red,
green o blue). La funzione rgb è sempre bloccante. Solo quando una sequenza di chiamate dello stesso colore viene
interrotta da una chiamata di colore diverso tutti i processi in attesa vengono sbloccati e rgb restituisce la somma dei
parametri 'value'.
Esempio: Il processo P chiama rgb(red, 2) -> si blocca. il processo Q chiama rgb(red, 4) ->si blocca. Il processo R chiama
rgb(blue, 1) sblocca i due processi P e Q che hanno chiamato rgb con parametro red, ad entrambi rgb ritorna il valore 6
(2 + 4). poi R si blocca. se ora un altro processo T chiama rgb(green, 39) il processo R continua e rgb ritorna 1 mentre R si
ferma. Ora i processi W,X,Y chiamano tutti rgb(green, 1) bloccandosi. Il processo Z chiamando rgb(red, 0) sblocca R,W,X,Y,
rgb restituisce a questi processi il valore 42 e Z si ferma.
'''

class rgbsum(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.color = -1
        self.value = 0
        self.blockedproc = 0
        self.condition = monitor.condition(self)
    
    @monitor.entry
    def rgb(self,color,value):
        if color != self.color :
            if self.blockedproc > 0: 
                for _ in range(self.blockedproc):
                    self.condition.signal()
                self.value = 0
                self.blockedproc = 0
            self.value = self.value + value
            self.color = color
            self.blockedproc += 1
            self.condition.wait()
        else:
            self.value = self.value + value
            self.color = color
            self.blockedproc += 1
            self.condition.wait()
        return self.value


'''
Scrivere il monitor ab12 che gestisce due buffer limitati FIFO, il primo memorizza elementi di tipo tipoa il
secondo elementi di tipo tipob. Entrambi i buffer contengono al massimo MAX elementi.
Il monitor ab12 fornisce quattro procedure entry:
void adda(tipoa a1, tipoa a2): aggiunge due elementi al primo buffer.
void addb(tipob b1): aggiunge un elemento al secondo buffer.
tipoa getone(void): restituisce un elemento dal primo buffer.
(tipoa, tipob) getab(void): restituisce un elemento dal primo buffer e uno dal secondo.
Tute le chiamate possono essere bloccanti (se non c'è spazio per inserire elementi nel caso delle chiamate di tipo add, se
non ci sono gli elementi da restituire per le chiamate di tipo get). Le richieste devono essere soddisfatte in ordine FIFO
'''


class ab12(monitor.monitor):
    def __init__(self):
         super().__init__()
         self.max = 5
         self.buffa = []
         self.counta = 0
         self.buffb = []
         self.countb = 0
         self.oka = monitor.condition(self)
         self.okb = monitor.condition(self)

    @monitor.entry
    def adda(self,a1,a2):
        if self.counta+2 > self.max :
            self.oka.wait()
        else:
            self.buffa.append(a1)
            self.buffa.append(a2)
            self.counta += 2
            self.oka.signal() 
        return
    
    @monitor.entry
    def addb(self,b1):
        if self.countb+1 > self.max :
            self.okb.wait()
        else:
            self.buffb.append(b1)
            self.countb += 1
            self.okb.signal()

    @monitor.entry
    def getoneA(self):
        if self.counta < 1:
            self.oka.wait()
        else:
            x = self.buffa.pop()
            self.counta -= 1
            if self.counta + 2 <= self.max:
                 self.oka.signal()
        return x
    
    @monitor.entry
    def getab(self):
        if self.counta < 1:
            self.oka.wait()
        if self.countb < 1 :
             self.okb.wait()
        else:
            x = self.buffa.pop()
            self.counta -= 1
            if self.counta + 2 <= self.max:
                 self.oka.signal()
            y = self.buffb.pop()
            self.countb -= 1
            if self.countb +1 <= self.max:
                self.okb.signal()
        return (x,y)





mon = ab12()

def p1():
    while True:
        time.sleep(2)
        safeprint(mon.adda(1,2))
def p2():
    while True:
        safeprint(mon.addb(4))
        time.sleep(1.5)
def p3():
    while True:
        time.sleep(2)
        safeprint(mon.getoneA())
        time.sleep(1)
        safeprint(mon.getab())

t1=Thread(target=p1)
t2=Thread(target=p2)
t3=Thread(target=p3)

t1.start()
t2.start()
t3.start()