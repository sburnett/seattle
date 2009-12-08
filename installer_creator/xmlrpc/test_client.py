import xmlrpclib

def main():
  proxy = xmlrpclib.Server("http://blackbox.cs.washington.edu:9050/xmlrpc")
  #proxy = xmlrpclib.Server("http://127.0.0.1:8000/xmlrpc")
  
  #[ {owner, percentage, [users]}, {owner, percentage, [users]} ... ]
  
  vessel_list = [{'owner':'jchen', 'percentage':40, 'users':[]}, {'owner':'james', 'percentage':40, 'users':[]}]
  pubkey_dict = {'jchen': {'pubkey':'jchen_pubkey1234'}, 'james':{'pubkey':'james_pubkey1234'}}
  
  print proxy.create_installer(vessel_list, pubkey_dict, "windows")
  

if __name__=="__main__":
  main()