'''
"Why spend 10 minutes doing something when you can spend 10 hours failing to automate it"
    -Fireship

    
test files MUST be named "test_TC_*", the test functions themselves MUST be
named "test", and located in the "tests" in order for the functional test runner
to pick it up. 
'''
import importlib
import os

def functionalTestRunner():

    print("Begin Functional Tests")
    results = []

    # point to tests folder and just execute all of those tests in a loop
    test_folder = "tests"
    for filename in os.listdir(test_folder):
        if filename.startswith("test_TC"): # if a test case test, then execute it. Ignore everything else
            module_name = filename[:-3] # remove the ".py" extention
            module_path = f"{test_folder}.{module_name}" # create module path from the name
            module = importlib.import_module(module_path) # import module dynamically

            # check to make sure that a function AKA module named test exists in the file
            if hasattr(module, "test"):
                result = module.test()
                results.append((module_name, result))
                print(f"{module_name}: {'Passed' if result else 'Failed'}")

    total_tests = len(results)
    failed_tests = sum(1 for _, result in results if not result)
    print(f"\n{failed_tests} out of {total_tests} tests failed.")

def main():
    functionalTestRunner()

if __name__ == "__main__":
    main()