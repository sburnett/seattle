"""
<Program Name>
  vessel_flow.py

<Started>
  February 25th, 2009

<Author>
  Ivan Beschastnikh

<Purpose>
  Deals with the share graph of GENI resources and provides
  functionality for understanding the amount of resources flowing into
  a node and out of a node via the sharing relationships between nodes
  (GENI users).

<ToDo>
  1. Created unit tests for all the functions with simple dictionary objects as
  shares/pshares and strings as nodes
  2. Add logging
"""

from copy import deepcopy


def get_percent(a, b, pshares):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   for (x,p) in pshares[a]:
      if x == b:
         return (p * 1.0) / 100.0
   return 0



def get_flow_vessels(flow, pshares, vessels):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   
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
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   
   children = []
   for dsts in shares.values():
      children += dsts
   return children



def get_root_nodes(shares):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   
   roots = []
   children = get_children(shares)
   for src in shares.keys():
      if not src in children:
         roots.append(src)
   return roots



def prune_roots(shares, roots):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   
   for root in roots:
      del(shares[root])
   return



def get_reachable_nodes(shares, src):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   
   # returns a list of all nodes reachables in shares from src
   reachables = []
   if not shares.has_key(src):
      return []
   for child in shares[src]:
      reachables += get_reachable_nodes(shares, child)
   reachables += shares[src]
   return reachables



def link_will_form_loop(shares, src, dst):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
     Returns True if adding src-dst link would form a loop in shares
     otherwise returns False
   <Note>
   <Todo>
   """
   return (src in get_reachable_nodes(shares, dst))

def flow_credits_from_roots(orig_shares, pshares, vessels):
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   None!
   <Returns>
   <Note>
   <Todo>
   """
   
   shares = deepcopy(orig_shares)
   print "initial vessels: "
   print vessels
   print "initial pshares :"
   print pshares

   credits_from = {}
   for node, value in vessels.items():
      credits_from[node] = []#[(node, value)]

   vessels_from_shares = {}
   
   while len(shares.keys()) != 0:
      roots = get_root_nodes(shares)
      print "roots: "
      print roots
      for root in roots:
         for child in shares[root]:
            p = get_percent(root, child, pshares)
            value = vessels[root] * p
            if not vessels_from_shares.has_key(child):
               vessels_from_shares[child] = value
            else:
               vessels_from_shares[child] += value
            #vessels[child] += value
            credits_from[child].append((root, value))
      prune_roots(shares, roots)
      print "pruned roots, resulting shares: "
      print shares
      print "pruned roots, resulting vessels: "
      print vessels
      print
   print "credits from: "
   print credits_from
   return credits_from, vessels_from_shares


# # TODO: potentially useful for building up credit list for a user without reflooding the vessel counts
# def get_flows_in(node, shares):
#    def get_alist(n):
#       retlist = []
#       for src, dsts in shares.items():
#          if n in dsts:
#             # print "found ", n , " in " , dsts
#             subchains = get_alist(src)
#             # print "subchains is " , subchains
#             link = [(src)]
#             if subchains == []:
#                # print "subchain is [], link :" , link
#                retlist.append(link)
#             else:
#                for subchain in subchains:
#                   newsubchain = link + subchain
#                   # print "newsubchain : " , newsubchain
#                   retlist.append(newsubchain)
#       return retlist
   
#    alist = get_alist(node)
#    for chain in alist:
#       chain.insert(0,node)
#       chain.reverse()
#    return alist


# def main():
#    # test for user ivan
#    success, guser = User.get_guser_by_username("ivan")
#    if not success:
#       print "ERROR"
#    shares = build_shares(False)
#    pshares = build_shares(True)
#    base_vessels = get_base_vessels()
#    print "before flow_credit_from_roots: " , base_vessels
#    flow_credits_from_roots(shares, pshares, base_vessels)
#    print "after flow_credit_from_roots: " , base_vessels


def unit_test():
   """
   <Purpose>
   <Arguments>
   <Exceptions>
   <Side Effects>
   <Returns>
   <Note>
   <Todo>
   """
   
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
   print link_will_form_loop(shares, 'g', 'a')
   print link_will_form_loop(shares, 'g', 'h')
   



   
if __name__ == "__main__":
   unit_test()
