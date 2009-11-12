import xmlrpclib

def main():
  proxy = xmlrpclib.Server("http://blackbox.cs.washington.edu:9050/xmlrpc/")
  
  print proxy.create_installer("jaymzlee", "1337")
  

if __name__=="__main__":
  main()