"""

Author: Armon Dadgar

Start Date: February 16th, 2009

Description:
Functions to reconstruct a dictionary object from its string representation.

"""

# Convert a string, which either a quoted string, floating point number, or int
# to a primitive, not string type (where applicable)
def stringToPrimitive(inStr):
  # String, or a numeric type?
  if inStr.startswith("'"):
    # Strip the extra quotes
    val = inStr.replace("'", "")
  
  # It is another dictionary, so recurse
  elif inStr.startswith("{"):
    val = deserializeDict(inStr)
    
  else:
    try:
      # Check if it is floating point
      if inStr.find(".") != -1:
        val = float(inStr)
    
      # It must be a long/int
      else:
        val = int(inStr)
    except:
      return inStr
  
  return val

# Returns an array with the index of the search char
def findChar(char, str):
  indexes = []
  
  # Look for all starting braces
  location = 0
  first = True
  while first or index != -1:
    # Turn first off
    if first:
      first = False

    # Search for sub dictionaries
    index = str.find(char,location)

    # Add the index, update location
    if index != -1:
      indexes.append(index)
      location = index+1   
  
  return indexes
      
# Find sub-dictionaries
def findSubObjs(str, start,end):
  # Location of the start and end braces
  startIndexes = findChar(start, str)
  
  # Check if any sub-dicts exist    
  if len(startIndexes) == 0:
    return []
            
  endIndexes = findChar(end, str)
  
  # Partitions of the string
  partitions = []
  
  startindex = 0
  endindex = 0
  
  while True:    
    maxStartIndex = len(startIndexes) - 1
    
    if maxStartIndex == -1:
      break
      
    if maxStartIndex == startindex or endIndexes[endindex] < startIndexes[startindex+1]:
      partitions.append([startIndexes[startindex],endIndexes[endindex],startindex])
      del startIndexes[startindex]
      del endIndexes[endindex]
      startindex = 0
      endindex = 0
    else:
      startindex += 1
  
  return partitions

def partitionedDict(value, partitions):
  index = int(value.lstrip("#"))
  return partitions[index][3]
      
# Convert a string representation of a Dictionary back into a dictionary
def deserializeDict(strDict, partitions=[]):
  # Remove dict brackets
  strDict = strDict[1:len(strDict)-1]
  
  # Check for sub dictionaries
  if strDict.find("{") != -1:
    subDicts = findSubObjs(strDict,"{","}")
    partitionIndex = 0
      
    # Determine maximum depth
    maxDepth = 0
    for dict in subDicts:
      maxDepth = max(maxDepth, dict[2])
    
    while maxDepth >= 0:
      for dict in subDicts:
        (start,end,depth) = dict
        if depth == maxDepth:
          realDict = deserializeDict(strDict[start:end+1],partitions)
          partitions.append((start,end,depth,realDict))
          
          addIn = "#"+str(partitionIndex)

          strDict = strDict[0:start]+addIn+strDict[end+1:]
          partitionIndex += 1
          
          indexOffset = 1+end-start
          indexOffset -= len(addIn)
          index = 0
          
          while index < len(subDicts):
            if subDicts[index][0] > start:
              subDicts[index][0] -= indexOffset
            if subDicts[index][1] > start:
              subDicts[index][1] -= indexOffset
            index += 1
              
      maxDepth -= 1
    
  # Get key/value pairs by exploding on commas
  keyVals = strDict.split(", ")

  # Create new dictionary
  newDict = {}

  # Process each key/Value pair
  for pair in keyVals:
    (key, value) = pair.split(": ",1)
  
    key = stringToPrimitive(key)
    
    if (value[0] == "#"):
      value = partitionedDict(value,partitions)
    else:
      value = stringToPrimitive(value)
  
    newDict[key] = value

  return newDict
  
def listToDict(lst):
  dict = {}
  counter = 0
  for value in lst:
      dict[counter] = value
      counter += 1
  return dict
