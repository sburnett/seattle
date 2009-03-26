
MAX_NUM = 4000000000 # 4 bilion

if callfunc == "initialize":
  # Generate a massive data file
  dataFile = ""

  print getruntime(), "Generating Data"
  while len(dataFile) < int(callargs[0]):
    dataFile += str(int(randomfloat() * MAX_NUM))
  print getruntime(), "Generation Finished"

  fileh = open(callargs[1], "w")
  fileh.write(dataFile)
  fileh.close()