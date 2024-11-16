# LLC Cache Test Plan:
The purpose of this test plan is to provide a comprehensive test case analysis. The LLC Cache Simulator takes a trace file as its input. This trace file has the purpose 
of simulating Processor Side cache requests, and Bus Operation side requests/traffic. In this sense our LLC must perform many checks to keep the balance of inclusivity and cache coherence
in the shared memory configuration presented in the project requirements. A single trace may generate an command 0-9 which are summarized below, the preceding sections cover each operation type in detail, 
along with the Simulation Flow. 

#### Cache Trace Operations Reference Table:
| Operation Code (n) | Description | Example |
|-------------------|-------------|----------|
| 0 | Read request from L1 data cache | `0 10019d94` |
| 1 | Write request from L1 data cache | `1 10019d88` |
| 2 | Read request from L1 instruction cache | `2 408ed4` |
| 3 | Snooped read request | `3 408ed8` |
| 4 | Snooped write request | `4 408edc` |
| 5 | Snooped read with intent to modify (RWIM) | `5 408ee0` |
| 6 | Snooped invalidate command | `6 408ee4` |
| 8 | Clear cache and reset all state | `8 0` |
| 9 | Print cache contents | `9 0` |

## Trace Command Coverage: 
### Command 0 - Read Request from L1 Data Cache
This is a processor side request from the L1 data cache (i.e. Misses in L1). 

**Simulation Flow:** 
1. **Address Lookup**
   - Calculate set index from address
   - Search all ways in the set for matching tag
   - Update access pattern for pseudo-LRU

2. **Cache Hit Case**
   - If line exists in LLC:
     * Increment hit counter
     * Increment read counter
     * Check MESI state of line
     * If state is Modified or Exclusive:
         - Send data to L1 (SENDLINE)
     * If state is Shared:
         - Send data to L1 (SENDLINE)
     * Return from operation

3. **Cache Miss Case**
   - If line doesn't exist in LLC:
     * Increment miss counter
     * Increment read counter
     * Perform `BusOperation(READ, Address, SnoopResult);`
        * Get `GetSnoopResult()`
            * If `NOHIT` read data in, and set MESI state to `Exclusive`
            * If `HIT` read data in, and set MESI state to `Shared` 
            * If `HITM` data is Modified, what for other Cache to perform WriteBack (TODO: Confirm this step)
                * Once written back, read data in, and set MESI to `Exlcusive`
     * Upon receiving data, check victim row (if any)
        * If victim row modified, perform `BusOperation()` -> i.e. WriteBack 
        * If `Shared` or `Exclusive` NOP
        * If Victim Row is in L1, send `message(EVICTLINE, Address);`

     * Send requested data `message(SENDLINE, Address)`


#### Test Cases Required:
1. Simple read hit to Exclusive line
2. Read hit to Modified line
3. Read hit to Shared line
4. Read miss requiring memory access
5. Read miss with HITM from other cache
6. Read miss causing clean eviction (i.e NOP)
7. Read miss causing dirty eviction (i.e BusOp, I think ??)

#### Sample Trace Sequence:
- TODO: Add more here, this is just a simple example
```
# Test read operations
8 0        # Clear cache
0 1000     # Cold miss read
3 1000     # Another processor reads (makes Shared)
0 1000     # Read to Shared line
0 2000     # Read causing potential eviction
9 0        # Verify final state
```