import threading 
import Queue 
 
class Mathematiker(threading.Thread): 
    Ergebnis = {} 
    ErgebnisLock = threading.Lock() 
 
    Briefkasten = Queue.Queue() 
 
    def run(self): 
        while True: 
            zahl = Mathematiker.Briefkasten.get() 
            ergebnis = self.istPrimzahl(zahl) 
 
            Mathematiker.ErgebnisLock.acquire() 
            Mathematiker.Ergebnis[zahl] = ergebnis 
            Mathematiker.ErgebnisLock.release() 
 
            Mathematiker.Briefkasten.task_done() 
 
    def istPrimzahl(self, zahl): 
        i = 2 
        while i*i < zahl + 1: 
            if zahl % i == 0: 
                return "%d * %d" % (zahl, zahl / i) 
 
            i += 1 
 
        return "prim" 
 
 
meine_threads = [Mathematiker() for i in range(5)] 
for thread in meine_threads: 
    thread.setDaemon(True) 
    thread.start() 
 
while True: 
    eingabe = raw_input("> ") 
    if eingabe == "ende": 
        break 
 
    elif eingabe == "status": 
        print "-------- Aktueller Status --------" 
        Mathematiker.ErgebnisLock.acquire() 
        for z, e in Mathematiker.Ergebnis.iteritems(): 
            print "%d: %s" % (z, e) 
        Mathematiker.ErgebnisLock.release() 
        print "----------------------------------" 
 
    elif long(eingabe) not in Mathematiker.Ergebnis: 
        Mathematiker.ErgebnisLock.acquire() 
        Mathematiker.Ergebnis[long(eingabe)] = "in Arbeit" 
        Mathematiker.ErgebnisLock.release()

        Mathematiker.Briefkasten.put(long(eingabe)) 
 
Mathematiker.Briefkasten.join()