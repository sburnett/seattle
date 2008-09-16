# simple client.   A better test client (but nothing like what a real client
# would be)
import socket

import traceback

import advertise            #  used to do OpenDHT lookups

# needed to sign nonces, etc.
import rsa
privkey = None
pubkey = None

def send_command(node,port,*args):
  # connect 
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((node, port))

  # send
  mystr = ('|'.join(args))
  sock.send(mystr)

  # stop sending...
  sock.shutdown(1)

  # get the response
  data = ''
  while True:
    thisdata = sock.recv(4096)
    if thisdata =='':
      break
    data = data + thisdata
  
  return data


def get_pub_key(keyfn):
  global pubkey
  pubkey = eval(read_file(keyfn))

def get_priv_key(keyfn):
  global privkey
  privkey = eval(read_file(keyfn))

def read_file(fn):
  fo = open(fn,"r")
  data = fo.read()
  fo.close()
  return data




def get_state(host,port):

  nodedata = send_command(host,port,"Get Experiments")

  if len(nodedata.split('|'))<2:
    raise Exception, "Cannot get node status"

  if nodedata.split('|')[0] != 'SUCCESS':
    raise Exception, nodedata

  return eval(nodedata.split('|',1)[1])
  



def command_loop():
  # things that may be set herein and used in later commands
  host = None
  port = None
  expnum = None
  filename = None
  cmdargs = None

  # exit via a return
  while True:

    try:
      userinput = raw_input("!> ")
      userinput = userinput.strip()

      userinputlist = userinput.split()
      if len(userinputlist)==0:
        continue

      if userinputlist[0] == 'help' or userinputlist[0] == '?':
        print \
"""
hi (host) (port)                              -- Say hi to a host
loadpub filename                              -- loads a public key
loadpriv filename                             -- loads a private key
args (...)                                    -- Set the experiments' args
start (experiment) (host) (port)              -- Start an experiment
stop (experiment) (host) (port)               -- Stop an experiment
list (host) (port)                            -- Get the experiments 
rawlist (host) (port)                         -- Get the experiments and more
changeprog program (experiment) (host) (port) -- Change an experiment's program
changekey key (experiment) (host) (port)      -- Change an experiment's pubkey
download remotefn (localfn) (host) (port)     -- Download a file 
upload localfn (remotefn) (host) (port)       -- Upload a file 
browse (key)                                  -- Find experiments I can control
exit                                          -- exits the shell

optional arguments (optional) are the last argument used of that type if not 
specified
"""
        continue

      elif userinputlist[0] == 'exit':
        return

      elif userinputlist[0] == 'quit':
        return

# hi (host) (port)                              -- Say hi to a host
      elif userinputlist[0] == 'hi':
        if len(userinputlist)>1:
          host = userinputlist[1]
        if len(userinputlist)>2:
          port = int(userinputlist[2])
        if len(userinputlist)>3:
          print "Warning, extra args"

        print send_command(host,port,"Hi")
        continue
  
# loadpub filename                              -- loads a public key
      elif userinputlist[0] == 'loadpub':
        if len(userinputlist)!=2:
          print "Error: incorrect number of args"
  
          continue
        get_pub_key(userinputlist[1])
        continue
  
# loadpriv filename                              -- loads a private key
      elif userinputlist[0] == 'loadpriv':
        if len(userinputlist)!=2:
          print "Error: incorrect number of args"
          continue
  
        get_priv_key(userinputlist[1])
        continue
  
# args (...)                                       -- Set the experiments' args
      elif userinputlist[0] == 'args':
        if len(userinputlist)>1:
          cmdargs = ' '.join(userinputlist[1:])
        else:
          cmdargs = None
  

# start (experiment) (host) (port) (args)           -- Start an experiment
      elif userinputlist[0] == 'start':
        if len(userinputlist)>1:
          expnum = int(userinputlist[1])
        if len(userinputlist)>2:
          host = userinputlist[2]
        if len(userinputlist)>3:
          port = int(userinputlist[3])
        if len(userinputlist)>4:
          cmdargs = ' '.join(userinputlist[4:])
  
        currentstate = get_state(host,port)
        if currentstate[expnum][2] != pubkey:
          print "Error: public key doesn't match the experiment's key"
          continue
  
        signednonce = rsa.sign(str(currentstate[expnum][1]),privkey)
        
        if cmdargs:
          print send_command(host,port,"Start",str(expnum),signednonce, cmdargs)
        else:
          print send_command(host,port,"Start",str(expnum),signednonce)
  
        continue
  
  
# stop (experiment) (host) (port)               -- Stop an experiment
      elif userinputlist[0] == 'stop':
        if len(userinputlist)>1:
          expnum = int(userinputlist[1])
        if len(userinputlist)>2:
          host = userinputlist[2]
        if len(userinputlist)>3:
          port = int(userinputlist[3])
        if len(userinputlist)>4:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        if currentstate[expnum][2] != pubkey:
          print "Error: public key doesn't match the experiment's key"
          continue
  
        signednonce = rsa.sign(str(currentstate[expnum][1]),privkey)
        
        print send_command(host,port,"Stop",str(expnum),signednonce)
  
        continue
  
# list (host) (port)                            -- Get the experiments 
      elif userinputlist[0] == 'list':
        if len(userinputlist)>1:
          host = userinputlist[1]
        if len(userinputlist)>2:
          port = int(userinputlist[2])
        if len(userinputlist)>3:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        for en in range(len(currentstate)):
          try:
            if currentstate[en][2] == pubkey:
#            print "*",(en, str(currentstate[en][0]), str(currentstate[en][2][10:30]), str(currentstate[en][3]))
              print " *%5d %30s %20s %5s" % (en, str(currentstate[en][0]), str(currentstate[en][2]['e'])[:20], str(currentstate[en][3]))
            else:
              print "  %5d %30s %20s %5s" % (en, str(currentstate[en][0]), str(currentstate[en][2]['e'])[:20], str(currentstate[en][3]))
          except TypeError:
            print currentstate[en]
            raise
        continue
  

# rawlist (host) (port)                         -- Get the experiments and more
      elif userinputlist[0] == 'rawlist':
        if len(userinputlist)>1:
          host = userinputlist[1]
        if len(userinputlist)>2:
          port = int(userinputlist[2])
        if len(userinputlist)>3:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        print currentstate
        continue
  
# changeprog program (experiment) (host) (port) -- Change an experiment's program
      elif userinputlist[0] == 'changeprog':
        if len(userinputlist)<2:
          print "Error: not enough args"
          continue
        program = userinputlist[1]
        if len(userinputlist)>2:
          expnum = int(userinputlist[2])
        if len(userinputlist)>3:
          host = userinputlist[3]
        if len(userinputlist)>4:
          port = int(userinputlist[4])
        if len(userinputlist)>5:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        if currentstate[expnum][2] != pubkey:
          print "Error: public key doesn't match the experiment's key"
          continue
  
        signednonce = rsa.sign(str(currentstate[expnum][1]),privkey)
        
        print send_command(host,port,"Change",str(expnum),signednonce,program, str(pubkey))
        continue
  
  
# changekey key (experiment) (host) (port)      -- Change an experiment's pubkey
      elif userinputlist[0] == 'changekey':
        if len(userinputlist)<2:
          print "Error: not enough args"
          continue
        key = eval(read_file(userinputlist[1]))
        if len(userinputlist)>2:
          expnum = int(userinputlist[2])
        if len(userinputlist)>3:
          host = userinputlist[3]
        if len(userinputlist)>4:
          port = int(userinputlist[4])
        if len(userinputlist)>5:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        if currentstate[expnum][2] != pubkey:
          print "Error: public key doesn't match the experiment's key"
          continue
  
        signednonce = rsa.sign(str(currentstate[expnum][1]),privkey)
        
        print send_command(host,port,"Change",str(expnum),signednonce, currentstate[expnum][0], repr(key))
        continue
  
  

# download remotefn (localfn) (host) (port)     -- Download a file 
      elif userinputlist[0] == 'download':
        if len(userinputlist)<2:
          print "Error: not enough args"
          continue
        remotefn = localfn = userinputlist[1]
        if len(userinputlist)>2:
          localfn = userinputlist[2]
        if len(userinputlist)>3:
          host = userinputlist[3]
        if len(userinputlist)>4:
          port = int(userinputlist[4])
        if len(userinputlist)>5:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        if currentstate[expnum][2] != pubkey:
          print "Error: public key doesn't match the experiment's key"
          continue
  
        signednonce = rsa.sign(str(currentstate[expnum][1]),privkey)
        
        data = send_command(host,port,"Download",str(expnum),signednonce, remotefn)
        if len(data.split('|')) == 1 or data.split('|')[0] != 'SUCCESS':
          print data
          continue
   
        filedata = data.split('|',1)[1]
  
        fo = open(localfn,"w")
        fo.write(filedata)
        fo.close()
  
        print 'SUCCESS'
  
        continue
  
  
# upload localfn (remotefn) (host) (port)       -- Upload a file 
      elif userinputlist[0] == 'upload':
        if len(userinputlist)<2:
          print "Error: not enough args"
          continue
        localfn = remotefn = userinputlist[1]
        if len(userinputlist)>2:
          remotefn = userinputlist[2]
        if len(userinputlist)>3:
          host = userinputlist[3]
        if len(userinputlist)>4:
          port = int(userinputlist[4])
        if len(userinputlist)>5:
          print "Warning, extra args"
  
        currentstate = get_state(host,port)
        if currentstate[expnum][2] != pubkey:
          print "Error: public key doesn't match the experiment's key"
          continue
  
        signednonce = rsa.sign(str(currentstate[expnum][1]),privkey)
        
        filedata = read_file(localfn)
        print send_command(host,port,"Upload",str(expnum),signednonce, remotefn,filedata)
  
        continue
  




# browse (key)                                  -- Find experiments I can control
      elif userinputlist[0] == 'browse':
        key = pubkey
        if len(userinputlist)>1:
          key = eval(read_file(userinputlist[1]))
        if len(userinputlist)>2:
          print "Warning, extra args"
  
        print advertise.lookup(key)
        continue
  
  
# else unknown
      else:
        print "Error: command not understood"
  

# handle errors
    except KeyboardInterrupt:
      # print or else their prompt will be indented
      print
      return
    except EOFError:
      # print or else their prompt will be indented
      print
      return
    except:
      traceback.print_exc()
      
  
  
if __name__=='__main__':
  command_loop()
