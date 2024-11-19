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
### Command 2 - Read request from L1 instruction cache 
### Command 3 - Snooped read request 
### Command 4 - Snooped write request 
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
### Command 8 - Clear cache and reset all state 
### Command 9 - Print cache contents 