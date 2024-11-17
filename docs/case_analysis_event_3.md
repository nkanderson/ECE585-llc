### Command 3 - Snooped Read Request
This is a snooped bus operation from other caches.

**Simulation Flow:** 
1. **Address Lookup**
   - Calculate set index from address
   - Search all ways in the set for matching tag

2. **Cache Hit Case**
   - If line exists in LLC:
     * Check MESI state of line
     * If state is Modified:
         - `PutSnoopResult(Address, HITM)`
         - `BusOperation(WRITE, Address)`
         - Update state to S
     * If state is Exclusive:
         - `PutSnoopResult(Address, HIT)`
         - Update state to S
     * If state is Shared:
         - `PutSnoopResult(Address, HIT)`
     * Return from operation

3. **Cache Miss Case**
   - If line doesn't exist in LLC:
     * `PutSnoopResult(Address, NOHIT)`


#### Test Cases Required:
1. Hit to Modified line
1. Hit to Exclusive line
1. Hit to Shared line
1. Miss

#### Trace Sequences:

1. Hit to Modified line
```
# Test read operations
8 0        # Clear cache
1 1000     # Write misses in L1 but allocates modified line in L2
3 1000     # Another LLC reads
9 0        # Verify final state
```

Besides verifying that final state in L2 is S for address 1000, need to confirm that `PutSnoopResult` was called with `HITM` and that `BusOperation` with `WRITE` action was called.

1. Hit to Exclusive line
```
# Test read operations
8 0        # Clear cache
0 1000     # Read misses in L1 but allocates Exclusive line in L2
3 1000     # Another LLC reads
9 0        # Verify final state
```

Besides verifying that final state in L2 is S for address 1000, need to confirm that `PutSnoopResult` was called with `HIT`.

1. Hit to Shared line
```
# Test read operations
8 0        # Clear cache
3 1000     # Another LLC reads
0 1000     # Read misses in L1 but allocates Shared line in L2
3 1000     # Another LLC reads
9 0        # Verify final state
```

Besides verifying that final state in L2 is S for address 1000, need to confirm that `PutSnoopResult` was called with `HIT`.

1. Miss
```
# Test read operations
8 0        # Clear cache
3 1000     # Another LLC reads
9 0        # Verify final state
```

Confirm that `PutSnoopResult` was called with `NOHIT`.
