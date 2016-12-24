import random, time
from threading import Thread
open("big.csv", "w").write("")
fl = open("big.csv", "a")
fl.write("A,B,C\n")

completed = 0
def calc():
   global completed
   for i in range(70000):
      fl.write("%s,%s,%s" % (i,random.randint(2,4233),random.randint(0,26))) 
   completed += 1

threads = 10
for i in range(threads):
   Thread(target=calc).start()

while completed != threads:
    time.sleep(1)
    print ("Done %s" % completed)

print ("COmpleted!")
fl.close()
