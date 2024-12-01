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
   - Extract and decode the incoming address fields into tag, index, and byte select
   - Search Cache for Potential HIT
2. **Cache Hit Case**
   - If line exists in LLC:
     * Increment hit counter
     * Increment read counter
     * Check MESI state of line
     * If state is EXCLUSIVE, MODIFIED, or SHARED:
         - Send data to L1 message(SENDLINE)
     * Return from operation
3. **Cache Miss Case**
   - If line doesn't exist in LLC:
     * Increment miss counter
     * Perform `BusOperation(READ, Address, SnoopResult);`
        * Get `GetSnoopResult()`
            * If `NOHIT` read data in, and set MESI state to `EXCLUSIVE`
            * If `HIT` read data in, and set MESI state to `SHARED` 
            * If `HITM` data is Modified, wait for other Cache to perform WriteBack?? (TODO: Confirm this step)??
                * Once written back, read data in, and set MESI to `EXCLUSIVE`
     * Upon receiving data, check victim row in the case of a full set (i.e. PLRU victim)
        * First check if is in L1 `MessageToCache(GETLINE, Address)`, this is important in the case of a MODIFIED Line in L1
            * IF is in L1, send message to evict line `MessageToCache(EVICTLINE, Address);`
        * If modified in L1, or L2 perform `BusOperation(WRITE, Address, SnoopResult);` -> TODO: Do we need a SnoopResult on a writeback?  
        * If `SHARED` or `EXCLUSIVe` victim line, NOP

     * Finally, send requested data `MessageToCache(SENDLINE, Address)` to L1


#### Test Cases:
1. Simple read hit to Exclusive line
2. Read hit to Modified line
- `TRACE` Case 1 & 2: Read hit to Exclusive Line and Modified Line
```bash
8 0      # Clear cache
0 0x1000 # Read miss, gets line in E state
0 0x2000 # Read miss, gets line in E state
1 0x2000 # Puts line into M state, write hit
0 0x1000 # Read hit
9 0      # Verify states should be one line E and one M
```
3. Read hit to Shared line
- `TRACE` Case 3: 
```bash
# Create Shared state scenario
8 0       # Clear cache
0 0x3000  # Get line in E state
3 0x3000  # Another processor reads (changes to S)
9 0       # Verify S state
0 0x3000  # Read hit to Shared line
9 0       # Verify state remains S
8 0       # Clear cache 
9 0       # Should print nothing
```

4. Read miss with HITM from other cache
- `TRACE` Case 4: 
```bash
# Setup HITM scenario
8 0               # Clear cache
# Note: This scenario requires specific GetSnoopResult() 
# implementation to return HITM for this address not sure how we will do this yet
0 0x5000          # Read miss, other cache has M
9 0               # Verify state after HITM handling, should be no data
# Possibly have other Cache Write Data back, confirm with Mark or TA. 
```
5. Read miss causing clean eviction (i.e NOP)
- `TRACE` Case 5
```bash
# Fill cache set then cause eviction
8 0                # Clear cache
# Fill all ways in a set (assuming 16-way)
0 0x0C0000          # Way 0
0 0x1C0000   # Way 1 (same set, different tag)
0 0x2C0000         # Way 2
0 0x3C0000        # Way 3
0 0x4C0000        # Way 4
0 0x5C0000        # Way 5
0 0x6C0000        # Way 6
0 0x7C0000        # Way 7
0 0x8C0000        # Way 8
0 0x9C0000        # Way 9
0 0xAC0000        # Way 10
0 0xBC0000        # Way 11
0 0xCC0000        # Way 12
0 0xDC0000        # Way 13
0 0xEC0000        # Way 14
0 0xFC0000        # Way 15
9 0                # Verify set is full
0 0x7FC0000        # Read miss causing clean eviction
9 0                # Verify eviction and new line
```
6. Read miss causing dirty eviction (i.e BusOp)
- `TRACE` Case 6
```bash
# Initialize and create dirty line in Way 0
8 0                # Clear cache
0 0x0C0000        # Load line into Way 0
1 0x0C0000        # Modify the line (makes it M state)
9 0                # Verify line is Modified

# Fill remaining ways in the same set
0 0x1C0000        # Way 1
0 0x2C0000        # Way 2
0 0x3C0000        # Way 3
0 0x4C0000        # Way 4
0 0x5C0000        # Way 5
0 0x6C0000        # Way 6
0 0x7C0000        # Way 7
0 0x8C0000        # Way 8
0 0x9C0000        # Way 9
0 0xAC0000        # Way 10
0 0xBC0000        # Way 11
0 0xCC0000        # Way 12
0 0xDC0000        # Way 13
0 0xEC0000        # Way 14
0 0xFC0000        # Way 15
9 0               # Verify set is full

# Cause eviction of Way 0 (which is Modified)
0 0x10C0000    # Read miss that should evict the modified line in Way 0
9 0            # Verify eviction occurred and new line is present
```
- Note: In this scenario we will need to verify that our Cache performs writeback when it evicts a Modified Line

### Command 1 - Write request from L1 data cache
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
         - This would mean that L2 has a modified entry that L1 has evicted at some point. Since no other caches have requested the data, L2 has not flushed it to DRAM yet.
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
            * NOTE: For the purposes of our simulation, the above two cases behave the same: read in data immediately and assume other caches correctly invalidate their data (or write back in the HITM case)
        * Since L2 is write allocate, create a new entry and set it to state M
     * Upon receiving data, check victim row (if any)
        * If victim row modified, perform `BusOperation(WRITE, Address, SnoopResult)`
        * If `Shared` or `Exclusive` NOP
        * If Victim Row is in L1, send `message(EVICTLINE, Address);`
     * Update PLRU access pattern
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
1. Write to Exclusive line
```
# Test write operations
8 0        # Clear cache
0 1000     # Cold miss read (NOHIT, move to E state)
1 1000     # Write to data
9 0        # Verify final state
```

2. Write to Modified line
```
# Test write operations
8 0        # Clear cache
1 1000     # Cold miss write (NOHIT, move to M state)
1 1000     # Write to same data
9 0        # Verify final state
```

3. Write to Shared line
```
# Test write operations
8 0        # Clear cache
0 1000     # Cold miss write (HIT, move to S state)
1 1000     # Write to same data
9 0        # Verify final state
```

4. Write miss to Modified line in another cache
```
# Test write operations
8 0        # Clear cache
1 1000     # Write to data returning a HITM snoop response
9 0        # Verify final state
```

5. Write miss to shared line in another cache
```
# Test write operations
8 0        # Clear cache
1 1000     # Write to data returning a HIT snoop response
9 0        # Verify final state
```

6. Write miss causing a clean eviction
```
# Test write operations
8 0           # Clear cache
0 0x00100002  # Way 0
0 0x00200002  # Way 1
0 0x00300002  # Way 2
0 0x00400002  # Way 3
0 0x00500002  # Way 4
0 0x00600002  # Way 5
0 0x00700002  # Way 6
0 0x00800002  # Way 7
0 0x00900002  # Way 8
0 0x00A00002  # Way 9
0 0x00B00002  # Way 10
0 0x00C00002  # Way 11
0 0x00D00002  # Way 12
0 0x00E00002  # Way 13
0 0x00F00002  # Way 14
0 0x01000002  # Way 15
1 0x01100002  # Write to data causing an eviction
9 0           # Verify final state
```

7. Write miss causing a dirty eviction
```
# Test write operations
8 0           # Clear cache
1 0x00100002  # Way 0
1 0x00200002  # Way 1
1 0x00300002  # Way 2
1 0x00400002  # Way 3
1 0x00500002  # Way 4
1 0x00600002  # Way 5
1 0x00700002  # Way 6
1 0x00800002  # Way 7
1 0x00900002  # Way 8
1 0x00A00002  # Way 9
1 0x00B00002  # Way 10
1 0x00C00002  # Way 11
1 0x00D00002  # Way 12
1 0x00E00002  # Way 13
1 0x00F00002  # Way 14
1 0x01000002  # Way 15
1 0x01100002  # Write to data causing an eviction
9 0           # Verify final state
```


### Command 2 - Read request from L1 instruction cache

The LLC is unified, so this command should be identical to command 0 above, which handles a read request from the L1 *data* cache (L1 is a split cache). We should follow the same test plan to test all the cases identified for command 0 when testing command 2.

If we add load testing for specific traffic patterns, we may consider including a higher ratio of command 2 as compared to command 0, in order to simulate instruction retrieval. For example, we could consider a pattern where there are approximately 4 instruction reads for every 1 data read.

### Command 3 - Snooped read request 
This is a snooped bus operation from other caches.

Simulation Flow:

    Address Lookup
        Calculate set index from address
        Search all ways in the set for matching tag

    Cache Hit Case
        If line exists in LLC:
            Check MESI state of line
            If state is Modified:
                PutSnoopResult(Address, HITM)
                BusOperation(WRITE, Address)
                Update state to S
            If state is Exclusive:
                PutSnoopResult(Address, HIT)
                Update state to S
            If state is Shared:
                PutSnoopResult(Address, HIT)
            Return from operation

    Cache Miss Case
        If line doesn't exist in LLC:
            PutSnoopResult(Address, NOHIT)

Test Cases Required:

    Hit to Modified line
    Hit to Exclusive line
    Hit to Shared line
    Miss

Trace Sequences:

1. Hit to Modified line
```bash
# Test read operations
8 0        # Clear cache
1 1000     # Write misses in L1 but allocates modified line in L2
3 1000     # Another LLC reads
9 0        # Verify final state
```
Besides verifying that final state in L2 is S for address 1000, need to confirm that PutSnoopResult was called with HITM and that BusOperation with WRITE action was called.

2. Hit to Exclusive line
```bash
# Test read operations
8 0        # Clear cache
0 1000     # Read misses in L1 but allocates Exclusive line in L2
3 1000     # Another LLC reads
9 0        # Verify final state
```
Besides verifying that final state in L2 is S for address 1000, need to confirm that PutSnoopResult was called with HIT.

3. Hit to Shared line
```bash
# Test read operations
8 0        # Clear cache
3 1000     # Another LLC reads
0 1000     # Read misses in L1 but allocates Shared line in L2
3 1000     # Another LLC reads
9 0        # Verify final state
```
Besides verifying that final state in L2 is S for address 1000, need to confirm that PutSnoopResult was called with HIT.

4. Miss
```bash
# Test read operations
8 0        # Clear cache
3 1000     # Another LLC reads
9 0        # Verify final state
```
Confirm that PutSnoopResult was called with NOHIT.

### Command 4 - Snooped write request

This command communicates that a cache is actively writing its data back to DRAM. This results from a cache with a line in the Modified state either evicting the line due to a collision miss, or responding to another cache's read or write request for the line by writing it back to DRAM. The cache holding the modified line will then downgrade the state to Shared (if requesting cache is reading) or Invalid (if requesting cache is writing).

This command should be a no-op, assuming that we've correctly invalidated any cache lines matching those snooped in commands 5 or 6.

### Command 5 - Snooped read with intent to modify (RWIM) 
**Simulation Flow:** 
1. **Address Lookup**
   - Extract and decode the incoming address fields into tag, index, and byte select
   - Search Cache for Potential HIT
2. **Cache Hit Case**
   - If line exists in LLC:
     * If line is in MODIFIED state, perform writeback and invalidate. Send INVALIDATELINE to L1. 
     * If line is in EXCLUSIVE state, invalidate
3. **Cache Miss Case**
   - NOP
#### Test Cases: Snooped RWIM with different MESI states
```bash
#Part 1: Setup and test RWIM on Modified line
# Initialize cache state
8 0                # Clear cache
0 0x0C0000        # Get line in E state
1 0x0C0000        # Write to make it M state
9 0               # Verify line is Modified
5 0x0C0000        # Snooped RWIM - should cause writeback and invalidation
9 0               # Verify line is now invalid
# Part 2: Test RWIM on Exclusive line
0 0x1C0000        # Get new line in E state
9 0               # Verify E state
5 0x1C0000        # Snooped RWIM - should just invalidate
9 0               # Verify line is invalid
# Part 3: Test RWIM on Shared line
0 0x2C0000        # Get line in E state
3 0x2C0000        # Another processor read makes it S
9 0               # Verify S state
5 0x2C0000        # Snooped RWIM - should invalidate
9 0               # Verify invalid
# Part 4: Test RWIM on non-existent line (miss case)
5 0x3C0000        # Snooped RWIM to missing line - should be NOP
9 0               # Verify no change in cache state
```


### Command 6 - Snooped invalidate command 
This is a snooping operation detecting an invalidate command on the bus

*NOTE: this section could change as we decide how to handle inclusivity

Simulation Flow:

    Address Lookup
        Calculate set index from address
        Search all ways in the set for matching tag

    Cache Hit Case
        If line exists in LLC:
            Check MESI state of line
            If MESI state is SHARED set MESI state to INVALID
            Else if MESI state is not SHARED, NOP
            Return from operation

    Cache Miss Case
        If line doesn't exist in LLC:
            NOP

Test Cases Required:

    Send 6 trace for address of line known to be in LLC with current state of SHARED
        Confirm state changes to INVALID
    Send 6 trace for address of line known to be in LLC with current state of INVALID
        Confirm state remains INVALID
    Send 6 trace for address of line known to be in LLC with current state of EXCLUSIVE
        Confirm state remains EXCLUSIVE
    Send 6 trace for address of line known to be in LLC with current state of MODIFIED
        Confirm state remains MODIFIED
    Send 6 trace for address known not to be in LLC
        Confirm no change of any MESI states (i.e. no addressing error)

Related follow-up testing:

    Test cache/bus operations such that states changed in tests above
    change to another state when appropriate

### Command 8 - Clear cache and reset all state 
This is a control operation to reset the simulator

Simulation Flow:

    Reset
        Clear the cache by deallocating all ways
        By default this resets all states

Test Cases Required:

    Send 8 trace (address irrelevant)
        Confirm all ways deallocated (could use some debugging logic or send test requests)

### Command 9 - Print cache contents 
Command 9 - print contents and state of each valid cache

This is a control operation to dump contents of valid cache lines

Simulation Flow:

    Output
        Search LLC for all lines with a valid state (!INVALID)
        Print set, tag, PLRU status, and MESI state for each line

Test Cases Required:

    Send 9 trace (address irrelevant)
        Confirm number of cache lines printed matches number with valid state
        Confirm no cachelines with INVALID state are printed
        Parse output to confirm it matches cache line contents
