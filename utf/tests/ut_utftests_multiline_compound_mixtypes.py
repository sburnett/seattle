# This test makes sure that multiline pragmas can be mixed and still function.

#pragma out
#pragma out Test message one
#pragma out Test message two
#pragma out 
#pragma out Test message three

#pragma error bad exception one
print "Test message one"
print "Test message two"
print "Test message three"

raise Exception("bad exception one")
