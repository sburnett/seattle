'''
Add shares:
- validate
- new share record

diplaying donated resources
- for each vessel that has owner public key set to this user, addd it to the myvessels list
- (donated by others, to me)
  - ?

displaying shares:
- select all shares for which i am the from_user

get resources (get_more):
- 1. check whether the person is allowed to get more resources
'''

import sys
from copy import deepcopy
from geni.control.models import Share, User

def build_shares(with_percent=True):
   shares = {}
   for share in Share.objects.all():
      if with_percent:
         s = (share.to_user, int(share.percent))
      else:
         s = share.to_user
      if shares.has_key(share.from_user):
         shares[share.from_user].append(s)
      else:
         shares[share.from_user] = [s]
   return shares

def get_base_vessels():
   vessels = {}
   for share in Shares.objects.all():
      for u in [share.to_user, share.from_user]:
         if not vessels.has_key(u):
            vessels[u] = u.base_vcount
   return vessels

def get_percent(a, b, pshares):
   for (x,p) in pshares[a]:
      if x == b:
         return (p * 1.0) / 100.0
   return 0

def get_flow_vessels(flow, pshares, vessels):
   vcount = 0
   for i in range(len(flow)-1):
      a = flow[i]
      b = flow[i+1]
      p = get_percent(a,b,pshares)
      # vessels[a] should contain the total vessels that a has **flowing into it**
      print "(%s, %s) : += %f * %f = %f"%(a, b, vessels[a], p, vessels[a] * p )
      vcount += vessels[a] * p
   return vcount

def get_children(shares):
   children = []
   for dsts in shares.values():
      children += dsts
   return children

def get_root_nodes(shares):
   roots = []
   children = get_children(shares)
   for src in shares.keys():
      if not src in children:
         roots.append(src)
   return roots

def prune_roots(shares, roots):
   for root in roots:
      del(shares[root])
   return

def get_reachable_nodes(shares, src):
   # returns a list of all nodes reachables in shares from src
   reachables = []
   if not shares.has_key(src):
      return []
   for child in shares[src]:
      reachables += get_reachable_nodes(shares, child)
   reachables += shares[src]
   return reachables
   
def will_form_loop(shares, src, dst):
   # returns True if adding src-dst link would form a loop in shares
   # otherwise returns False
   return (src in get_reachable_nodes(shares, dst))

def flow_credits_from_roots(orig_shares, pshares, vessels):
   shares = deepcopy(orig_shares)
   # print "initial vessels: "
#    print vessels
#    print "initial pshares :"
#    print pshares

   credits_from = {}
   for node, value in vessels.items():
      credits_from[node] = [(node, value)]
   
   while len(shares.keys()) != 0:
      roots = get_root_nodes(shares)
      #print "roots: "
      #print roots
      for root in roots:
         for child in shares[root]:
            p = get_percent(root, child, pshares)
            value = vessels[root] * p
            vessels[child] += value
            credits_from[child].append((root, value))
      prune_roots(shares, roots)
      # print "pruned roots, resulting shares: "
#       print shares
#       print "pruned roots, resulting vessels: "
#       print vessels
#       print
#    print "credits from: "
#    print credits_from

      
def get_flows_in(node, shares):
   def get_alist(n):
      retlist = []
      for src, dsts in shares.items():
         if n in dsts:
            # print "found ", n , " in " , dsts
            subchains = get_alist(src)
            # print "subchains is " , subchains
            link = [(src)]
            if subchains == []:
               # print "subchain is [], link :" , link
               retlist.append(link)
            else:
               for subchain in subchains:
                  newsubchain = link + subchain
                  # print "newsubchain : " , newsubchain
                  retlist.append(newsubchain)
      return retlist
   
   alist = get_alist(node)
   for chain in alist:
      chain.insert(0,node)
      chain.reverse()
   return alist


def main():
   success, guser = User.get_guser_by_username("ivan")
   if not success:
      print "ERROR"
   shares = build_shares(False)
   pshares = build_shares(True)
   base_vessels = get_base_vessels()
   print "before flow_credit_from_roots: " , base_vessels
   flow_credits_from_roots(shares, pshares, base_vessels)
   print "after flow_credit_from_roots: " , base_vessels


def unit_test():
   shares = {'a' : ['b', 'c'],
             'b' : ['d', 'e', 'f', 'g'],
             'c' : ['g', 'h', 'i', 'j'],
             'f' : ['g']
             }

   pshares = {'a' : [('b',10), ('c',10)],
              'b' : [('d',20), ('e',20), ('f',30), ('g',40)],
              'c' : [('g',20), ('h',40), ('i',10), ('j',10)],
              'f' : [('g', 10)]
              }

   base_vessels = {'a': 100,
              'b' : 100,
              'c' : 100,
              'd' : 100,
              'e' : 100,
              'f' : 100,
              'g' : 100,
              'h' : 100,
              'i' : 100,
              'j' : 100}

   print "before flow_credit_from_roots: " , base_vessels
   flow_credits_from_roots(shares, pshares, base_vessels)
   print "after flow_credit_from_roots: " , base_vessels
#    g_flows = get_flows_in('g', shares)
#    for flow in g_flows:
#       print "flow : " , flow
#       fvalue = get_flow_vessels(flow, pshares, base_vessels)
#       print "value: " , fvalue
#   print "flow dst value: " , 100

   print get_reachable_nodes(shares, 'a')
   print get_reachable_nodes(shares, 'f')
   print will_form_loop(shares, 'g', 'a')
   print will_form_loop(shares, 'g', 'h')
   
   

if __name__ == "__main__":
   unit_test()
   main()
