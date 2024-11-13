"""
dstest.py -- python script to demonstrate cache class.
Uses the class to instantiate an 8 set 2-way associative
cache data structure and prints the empty structure in
order to visualize it.
"""

from pprint import pprint
from cachestruct import cache

testCache = cache(8, 2)

print(" ")
print('testCache has', testCache.numSets, 'sets and is', testCache.assoc, 'way associative.')
print(" ")
print("Set  Ways")
pprint(testCache.set)
