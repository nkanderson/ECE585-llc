from pprint import pprint
from cachestruct import cache

testCache = cache(8, 2)

print(" ")
print('testCache has', testCache.numSets, 'sets and is', testCache.assoc, 'way associative.')
print(" ")
print("Set  Ways")
pprint(testCache.set)

