# List of potential functional tests
* test_TC-1_no_input.py
* test_TC-2_memory_reference_crosses_cache_line_boundary.py
    * skip for now
* test_TC-4_include_0x_in_trace_file.py
* test_TC-5_negative_command_enum_n.py
* test_TC-6_negative_address_in_trace.py
* test_TC-7_empty_trace_file.py
* test_TC-8_address_out_of_range.py
* test_TC-9_performance_test.py
    * It may be useful to benchmark how long it takes to run the sim on certian
      trace files and if it takes too long, may be indication of an issue.
    * maybe not needed
* test_TC-10_verify_silent_mode.py
* test_TC-11_bad_trace_file.py
    * maybe not needed
    * What happens if there is an unexpected symbol in the trace file
* test_TC-12_1M_trace_file.py
    * can we stress this simulation and what are the results
* test_TC-13_bad_command_line_option_input.py
    * random garbage for the command line, how does the program handle that
* test_TC-14_enable_silent_and_normal_mode_at_the_same_time.py
* test_TC-15_cache_miss_on_read_of_empty_cache.py
    * in these kinds of tests you may also want to verify the snoop results
* test_TC-16_cache_miss_on_write_of_empty_cache.py
* test_TC-17_cache_conflict_miss_on_write_to_occupied_line.py
  * verify that the PLRU evicts the PLRU line by parsing read request to DRAM
* test_TC-18_cache_conflict_miss_on_read.py
  * verify that the PLRU evicts the PLRU line by parsing read request to DRAM
* test_TC-19_cache_conflict_miss_on_write_dirty_line.py
  * verify that the PLRU evicts the PLRU line by parsing read and write request 
  to DRAM
* test_TC-20_cache_conflict_miss_on_read_dirty_line.py
  * verify that the PLRU evicts the PLRU line by parsing read and write request 
  to DRAM
* test_TC-21_insert_same_data_to_cache_twice.py
* test_TC-22_dirty_line_after_write_hit.py
* test_TC-23_cache_clear_after_command_8.py
  * check PLRU, tag, valid and dirty bits
* other test about the MESI protocol, but I dont understand it, so I cant speak to it yet

