import time
import random
names = ["Peter", "Armon", "Justin", "Ivan", "Carter", "Sean", "Joe", "Bob", "John", "Jane", "Jacob", "Issac", "Venessa"]

while True:
  filehandle = open("status", "w")
  numberofvessels = random.randint(1, 100)
  totalallocated = 100
  for i in range(0, numberofvessels):
    if totalallocated <= .1 :
      break
    if numberofvessels-1 == i :
      valueallocated = totalallocated  
    else :
	  valueallocated = round(random.uniform(0, totalallocated), 1)
    valueinuse = round(random.uniform(0, 100), 1)
    print >> filehandle, random.choice(names), "," ,valueallocated, "," , valueinuse
    totalallocated = totalallocated - valueallocated 
  filehandle.close()
  time.sleep(10)

  



