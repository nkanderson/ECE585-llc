### Command 1 - Write Request from L1 Data Cache
This is a processor side request from the L1 data cache (i.e. Misses in L1). 

**Simulation Flow:** 
1. **Address Lookup**
   - Calculate set index from address
   - Search all ways in the set for matching tag

2. **Cache Hit Case**
   - If line exists in LLC:
     * Increment hit counter
     * Increment write counter
     * Check MESI state of line
     * If state is Modified:
         - This would mean that L2 has a modified entry that L1 has evicted. Since no other caches have requested the data, L2 has not flushed it to DRAM yet. TODO: Confirm that L1 write back on eviction works this way, versus writing all the way out to DRAM.
         - Send data to L1 (SENDLINE)
     * If state is Exclusive:
         - Update state to M
         - Send data to L1 (SENDLINE)
     * If state is Shared:
         - Perform `BusOperation(INVALIDATE, Address, SnoopResult);`
             * Shouldn't need to `GetSnoopResult` here because if the line is in the shared state, there are no other actions (e.g. flush) for other cases to take besides invalidate.
         - Update state to M
         - Send data to L1 (SENDLINE)
     * Update PLRU access pattern
     * Return from operation

3. **Cache Miss Case**
   - If line doesn't exist in LLC:
     * Increment miss counter
     * Increment write counter
     * Perform `BusOperation(RWIM, Address, SnoopResult);`
        * Get `GetSnoopResult()`
            * If `HITM` wait for other cache to flush, then read in data
            * If `HIT` or `NOHIT`, read in data (other caches have to invalidate their copies)
        * Since L2 is write allocate, create a new entry and set it to state M
     * Upon receiving data, check victim row (if any)
        * If victim row modified, perform `BusOperation(WRITE, Address, SnoopResult)`
        * If `Shared` or `Exclusive` NOP
        * If Victim Row is in L1, send `message(EVICTLINE, Address);`
     * Update PLRU access pattern? Does that happen on every new addition?
     * Send requested data `message(SENDLINE, Address)`


#### Test Cases Required:
1. Write hit to Modified line
1. Write hit to Exclusive line
1. Write hit to Shared line
1. Write miss with HIT / NOHIT from other cache
1. Write miss with HITM from other cache
1. Write miss causing clean eviction (i.e NOP)
1. Write miss causing dirty eviction (i.e BusOp, I think ??)

#### Sample Trace Sequence:
- TODO: Create examples, this is just a simple example
```
# Test read operations
8 0        # Clear cache
0 1000     # Cold miss read
3 1000     # Another processor reads (makes Shared)
0 1000     # Read to Shared line
0 2000     # Read causing potential eviction
9 0        # Verify final state
```
