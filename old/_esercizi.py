from threading import Thread
from pysm import monitor
from threading import Semaphore
import queue
import time

class safeprint(monitor.monitor):
	def __init__(self):
		super().__init__()

	@monitor.entry
	def print(self, *args,**kwargs):
		print(*args,**kwargs)

safeprint = safeprint().print

#I bit di un numero intero rappresentano condizioni di un sistema. Se lo stato attuale è 6 (0110) vuole dire
#che attualmente sono vere le condizioni 2 (0010) e 4 (0100).
#Scrivere un monitor bitcond che fornisca le seguenti procedure entry:
#void set(int bit2set); accende nello stato attuale i bit di bit2set
#void unset(int bit2unset) spegne nello stato attuale i bit di bit2unset
#void statuswait(int bit2wait) attende che lo stato attuale soddisfi tutti le condizioni indicate in bit2wait (cioè
#che tutti i bit in bit2wait siano accesi nello stato attuale).
#Le richieste statuswait devono essere servite in ordine FIFO (cioè un processo anche se sono presenti tutte le
#condizioni necessarie deve attendere se un processo che ha chiamato statuswait prima è in attesa).
#Lo stato iniziale è zero (nessuna risorsa disponibile)

class bitcond(monitor.monitor):
    def __init__(self,actualState):
        super().__init__()
        self.actualState = actualState
        self.bit2waitOk = monitor.condition(self)
    
    @monitor.entry
    def set(self,bit2set):      #bit2set deve essere 1 o 2 o 4 o 8
        self.actualState = self.actualState + bit2set
        safeprint(self.actualState)
        self.bit2waitOk.signal()

    @monitor.entry
    def unset(self,bit2unset):      #bit2set deve essere 1 o 2 o 4 o 8
        self.actualState = self.actualState - bit2unset
        safeprint(self.actualState)
        self.bit2waitOk.signal()

    @monitor.entry
    def statuswait(self,bit2wait):
        while(self.actualState != bit2wait):
            self.bit2waitOk.wait()

#---------------------------------------------------------------------------------------------------------------------------------------

#Usando i semafori implementare un servizio che preveda due funzioni:
#void sumstop(int v)
#int sumgo(void)
#La funzione sumstop deve mettere il processo chiamante in attesa.
#La funzione sumgo deve sbloccare tutti i processi messi in attesa con la sumstop e restituire la somma algebrica dei
#valori passati come parametro alla sumstop dai processi che sono stati sbloccati (zero se la sumgo viene richiamate
#quando non c'è nessun processo bloccato).

somma = 0
counter = 0
s = Semaphore(0)
mutex = Semaphore(1)

def sumstop(v):
    mutex.acquire()
    global somma
    global counter
    somma += v
    counter += 1
    mutex.release()
    s.acquire()

def sumgo():
    mutex.acquire()
    global somma
    global counter
    safeprint(somma)
    for _ in range(counter):
        s.release()
    counter = 0
    somma = 0
    mutex.release()

#---------------------------------------------------------------------------------------------------------------------------------------

#In un porto con una sola banchina utilizzabile occorre caricare cereali sulle navi. I camion portano i cereali
#al porto. Una sola nave alla volta può essere attraccata al molo, un solo camion alla volta scarica i cereali nella nave.
#Il codice eseguito da ogni nave è:
#nave[i] process:
#porto.attracca(capacità)
#porto.salpa()
#...naviga verso la destinazione
#Il codice di ogni camion è:
#camion[j] process:
#while (1):
#quantità = carica_cereali()
#porto.scarica(quantità)
#I camion fanno la spola dai depositi alla nave. La nave arriva vuota e può salpare solo se è stata completamente
#riempita (la somma delle quantità scaricate dai camion raggiunge la capacità indicata come parametro della funzione
#attracca). Se un camion può scaricare solo parzialmente il suo carico rimane in porto e aspetta di completare
#l'operazione con la prossima nave che attraccherà al molo.
#Scrivere il monitor porto.

class porto(monitor.monitor):
    def __init__(self):
         super().__init__()
         self.okNave = monitor.condition(self) # quando la nave è piena (capNave = 0) puo partire
         self.okCamion = monitor.condition(self) # quando il camion ha scaricato tutti i cereali può partire
         self.okAttraccoN = monitor.condition(self) # se la nave può attraccare
         self.okScaricoC = monitor.condition(self) # se il camion può scaricare
         self.capNave = 0
         self.qc = 0
         self.naveInPorto = False
         self.camionInPorto = False
         
         

    @monitor.entry
    def attracca(self,capNave):
        if self.naveInPorto == False:
            self.naveInPorto = True
            self.capNave = capNave
            if self.camionInPorto == True:
                self.capNave = self.capNave - self.qc 
                self.camionInPorto = False
                self.qc = 0
                self.okCamion.signal()
            self.okScaricoC.signal()
        else:
            self.okAttraccoN.wait()
            self.naveInPorto = True
            self.capNave = capNave
            self.okScaricoC.signal()


    @monitor.entry
    def salpa(self):
        if self.capNave == 0:
            self.okNave.signal()
            self.naveInPorto = False
            self.okAttraccoN.signal()
        else:
            self.okNave.wait()
            self.naveInPorto = False
            self.okAttraccoN.signal()

    
    @monitor.entry
    def scarica(self,quantitaCereali):
        if self.naveInPorto == False:
            self.okScaricoC.wait()
        if self.camionInPorto == False:
            self.camionInPorto = True
            self.qc = quantitaCereali
            if self.qc > self.capNave:
                self.qc = self.qc - self.capNave
                self.capNave = 0
                self.okNave.signal()
                self.okCamion.wait()
            else:
                self.capNave = self.capNave - self.qc
                if self.capNave == 0: self.okNave.signal()
                self.qc = 0
                self.camionInPorto = False
                self.okCamion.signal()
                self.okScaricoC.signal()
        else:
            self.okScaricoC.wait()
            self.qc = quantitaCereali
            if self.qc >= self.capNave:
                self.qc = self.qc - self.capNave
                self.capNave = 0
                self.okNave.signal()
                self.okCamion.wait()
            else:
                self.capNave = self.capNave - self.qc
                self.qc = 0
                self.okCamion.signal()
        
#---------------------------------------------------------------------------------------------------------------------------------------

# Scrivere il monitor delay che fornisce due procedure entry:
# int wait_tick(int nticks)
# void tick(void)
# La procedure entry tick è pensata per essere richiamata periodicamente (es. ogni secondo o ora o giorno) da un
# processo.
# Quando un processo chiama la wait_tick deve attendere un numero di chiamate della tick pari al parametro nticks.
# Per esempio se un processo chiama wait_tick(2) deve fermarsi e verrà riattivato alla seconda successiva chiamata di
# tick.
# La funzione wait_tick ha come valore di ritorno il numero di processi che erano bloccati al momento della tick che ha
# sbloccato il chiamante.
# Esempio: P chiama wait_tick(2) e si blocca. Q chiama wait_tick(3) e si blocca. T chiama tick() non succede nulla. R
# chiama wait_tick(2) e si blocca. T chiama tick(), viene sbloccata la wait_tick di P e il valore ritornato è 3. T chiama
# tick(), vengono sbloccate le wait_tick di Q e R e il valore ritornato per entrambi i processi è 2

class delay(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.mem = 0
        self.wait1 = monitor.condition(self)
        self.nticks = [] 
        self.sawticks = []

    @monitor.entry
    def wait_tick(self,nticks):
        self.counter += 1
        self.nticks.append(nticks)
        self.sawticks.append(0)
        self.wait1.wait()
        return self.mem
        


    @monitor.entry
    def tick(self):
        self.mem = self.counter
        j = 0
        for j in range(len(self.sawticks)):
            self.sawticks[j] += 1
        lenz = len(self.nticks)
        for _ in range(lenz):
            if self.sawticks[0] == self.nticks[0]:
                self.counter -= 1
                self.sawticks.remove(self.sawticks[0])
                self.nticks.remove(self.nticks[0])
                lenz -= 1
                self.wait1.signal()
                

#---------------------------------------------------------------------------------------------------------------------------------------

#Scrivere il monitor collocamento:
#void cercolavoro(char *nome, char *skill)
#void char *assumo(char * skill)
#Quando un processo chiama la cercolavoro si mette in attesa di una richiesta di lavoro e rimane bloccato nel monitor
#fino a che non è stato assunto. Nella cercolavoro viene indicato il nome dell'aspirante lavoratore la sua capacità (skill).
#Un datore di lavoro con necessità di personale chiama la assumo specificando la capacità richiesta. Se c'è in attesa
#almeno un aspirante lavoratore con quella specifica capacità (uguale valore di skill), il datore di lavoro riceve il nome del
#nuovo dipendente ed entrambi i processi escono dal monitor. Nel caso non ci siano richieste compatibili il datore di
#lavoro si blocca nel monitor attendendo un lavoratore con la capacità cercata. Quando arriva il lavoratore che soddisfa
#le richieste si sbloccano entrambi i processi lavoratore e datore di lavoro. La assumo restituisce in ogni caso il nome del
#dipendente da assumere.

class collocamento(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.ww = 0
        self.wo = 0
        self.ok2w = monitor.condition(self)
        self.ok2o = monitor.condition(self)
        self.skill = ''
        self.nome = ''

    @monitor.entry
    def cercolavoro(self,nome,skill):
        self.skill = skill
        if self.wo > 0:
            self.nome = nome
            self.ok2o.signal()
        else:
            self.ww +=1
            self.ok2w.wait()
            self.ww -=1
        self.nome = nome

    @monitor.entry
    def assumo(self,skill):
        self.skill = skill
        if self.ww > 0:
            self.ok2w.signal()
        else:
            self.wo += 1
            self.ok2o.wait()
            self.wo -=1
        return self.name
        

#---------------------------------------------------------------------------------------------------------------------------------------

#Scrivere il monitor semdata che implementi un semaforo con dato. Questa astrazione prevede due
#operazioni:
# datatype dP(void);
# void dV(datatype data);
#Non è previsto assegmento di valore iniziale nel costruttore, l'invariante è lo stesso dei semafori (con init = 0): ndP <=
#ndV (dove ndP e ndV rappresentano rispettivamente il numero di operazioni dP e dV completate. I dati passati come
#parametro alla dV devono essere memorizzati in ordine LIFO. L'operazione dP restituisce il valore più recente fra quelli
#memorizzati (e lo cancella dalla struttura dati)

from queue import LifoQueue

class semdata(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.q = LifoQueue()
        self.c = monitor.condition()
        self.value = 0
        

    @monitor.entry
    def dP(self):
        if self.value == 0:
            self.c.wait()
        self.value -= 1
        return self.q.get()
    
    @monitor.entry
    def dV(self,data):
        self.q.put(data)
        value += 1
        self.c.signal()


#---------------------------------------------------------------------------------------------------------------------------------------

#Scrivere il monitor delayvalue con una sola procedure entry:
#int delay(int value);
#Il monitor deve sospendere i primi NDELAY processi che chiamano la delay. Le successive chiamate di delay
#devono mantenere costante il numero di processi sospesi, ogni successiva chiamata devo riattivare il primo
#processo in attesa prima di sospendersi, la delay ritorna il valore passato come parametro dal processo che
#ne ha riattivato l'esecuzione. e.g. se NDELAY è 2:
#P1: delay(44) -> P1 si sospende
#P2: delay(40) -> P2 si sospende
#P3: delay(42) -> P1 si riattiva e ritorna 42, P3 si sospende
#P4: delay(22) -> P2 si riattiva e ritorna 22, P4 si sospende

class delayvalue(monitor.monitor):
    def __init__(self,ndelay):
        super().__init__()
        self.ndelay = ndelay  # processi da bloccare
        self.pB = 0 # processi bloccati
        self.w8 = monitor.condition(self)
        self.value = 0

    @monitor.entry
    def delay(self,value):
        self.value = value
        if self.pB < self.ndelay:
            self.pB +=1
            self.w8.wait()
            return self.value
        if self.pB == self.ndelay:
            self.w8.signal()
            self.w8.wait()
            return self.value

# ATTENZIONE ZIO CANE

# OGNI PROCESSO ENTRA COL PROPRIO VALORE E NON VIENE SOVRASCRITTO DAGLI ALTRI PROCESSI, QUANDO SI RISVEGLIA UN PROCESSO CON UNA SIGNAL
# IL VALORE VIENE AGGIORNATO A QUELLO DEL PROCESSO ATTIVO IN QUEL MOMENTO NEL MONITOR (INFATTI NEL MONITOR CI STA SEMPRE E SOLO
# 1 PROCESSO ATTIVO, GLI ALTRI PROCESSI DEVONO ESSERE TUTTI IN WAIT).

# per dare l' output corretto nell esercizio , ho quindi passato il value ad una variabile interna al monitor, cosi mi salvo la variabile
# dell ultimo processo che è entrato e si mantiene quella anche se ne si sveglia un altro

#---------------------------------------------------------------------------------------------------------------------------------------

#Un buffer sincrono strampalato (bss) ha due procedure entry:
#void put(T value)
#list of T get(void)
#La entry put viene utilizzata per aggiungere un elemento e la entry get per leggere tutti quelli disponibili.
#Se più processi chiamano la put quando nessun processo è in attesa per una get, rimangono tutti bloccati.
#Quando successivamente un processo chiama la get riceve la lista di tutti gli elementi inseriti con le put e
#tutti i processi vengono sbloccati.
#Se il buffer è vuoto tutti i processi che chiamano la get rimangono bloccati. quando un processo chiama
#successivamente la put tutti i processi in attesa per la get si sbloccano e ricevono lo stesso valore di ritorno:
#una lista contenente il solo valore passato come parametro alla put

class bss(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.elements = []   #buffer
        self.w8get = monitor.condition(self)
        self.w8put = monitor.condition(self)
        self.np = 0 #numero processi nella put
        self.ng = 0 #numero processi nella get


    @monitor.entry
    def put(self,value):
        self.np +=1
        self.elements.append(value)
        for _ in range(self.ng):
            self.w8put.signal()
        self.w8get.wait()
        self.np -=1
    
    @monitor.entry
    def get(self):
        self.ng +=1
        if len(self.elements) == 0:
            self.w8put.wait()
        else:
            for _ in range(self.np):
                self.w8get.signal()
        self.ng -=1
        return self.elements

#---------------------------------------------------------------------------------------------------------------------------------------

#Il monitor delay deve fornire tre procedure entry:
#boolean delay(unsigned int timeout)
#int count(void)
#void tick(void)
#La funzione tick viene richiamata ad ogni millisecondo. Un processo messo in attesa a causa di una delay attende per
#un numero di millisecondi (tick) indicato nel parametro.
#La procedure entry count deve restituire il numero di processi attualmente in attesa a causa di una delay.
#Scrivere delay

class delay2(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.nticks = [] #n ticks visti per ogni processo
        self.timeouts = [] #mi salvo i timeouts
        self.delays = 0 #n processi in attesa
        self.w8 = monitor.condition(self)
        self.ticked = monitor.condition(self)
    
    @monitor.entry
    def delay(self,timeout):
        self.timeouts.append(timeout)
        self.delays +=1
        self.nticks.append(0)
        self.ticked.wait()
        self.w8.wait()
        self.delays -=1
    
    @monitor.entry
    def count(self):
        return self.delays
    
    @monitor.entry
    def tick(self):
        i = 0
        for i in range(len(self.nticks)):
            self.ticked.signal()
            self.nticks[i] +=1
        for _ in range(len(self.nticks)):
            if self.nticks[0] >= self.timeouts[0]:
                self.nticks.remove(self.nticks[0])
                self.timeouts.remove(self.timeouts[0])
                self.w8.signal()
        
    
#---------------------------------------------------------------------------------------------------------------------------------------

#Il monitor "semaforo con timeout" semtimeout deve fornire tre procedure entry:
#void V(void)
#boolean P(unsigned int timeout)
#void tick(void)
#Vale l'invariante dei semafori generali. La funzione tick viene richiamata ad ogni millisecondo. Un processo messo in
#attesa a causa di una P attende al massimo il numero di millisecondi indicato nel parametro.
#Se un processo viene riattivato per timeout la P ritorna valore vero, altrimenti falso. Le operazioni V devono riattivare i
#processi in attesa in ordine FIFO.
#Scrivere semtimeout

# invariante nP ≤ nV + init

class semtimeout(monitor.monitor):
    def __init__(self,init):
        super().__init__()
        self.init = init
        self.w8 = monitor.condition(self)
        self.ticks = 0
        self.timeout = 0
        self.istime = False
    
    @monitor.entry
    def V(self):
            self.init +=1
            self.w8.signal()
    
    @monitor.entry
    def P(self,timeout):
        self.timeout = timeout
        if self.init > 0:
            self.init -=1
        elif self.init == 0:
            self.w8.wait()
            return self.istime
        else:
            safeprint('invariante non rispettata')
        
    @monitor.entry
    def tick(self):
        self.ticks +=1
        if self.ticks == self.timeout:
            self.istime = True
            self.w8.signal()

s = semtimeout(0)

def p1():
    safeprint(s.P(4))
    time.sleep(2)

def p2():
    #s.V()
    time.sleep(3)

def ticker():
    while True:
        s.tick()

t1=Thread(target=p1)
t2=Thread(target=p2)
t3=Thread(target=ticker)

t1.start()
t2.start()
t3.start()