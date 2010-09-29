fn = "ShimStackInterface.repy"
f = open(fn, 'r')
ret = ""
count = 0
for line in f:
    checkline = line.strip()
    if checkline.startswith("#"):
        count += 1
    else:
        ret += line
f.close()

f = open(fn, 'w')
f.write(ret)
f.close()
print "Removed %d lines of comments." % count
