# Test Plan
"Slow is smooth and smooth is fast"

## Table of Contents
1. [Unit testing](Unit-Testing)
   1. [What is Unit Testing?](What-is-Unit-Testing?)
   2. [Steps for unit testing](Steps-for-unit-testing)
      1. [0. Testing Framework](0.-Testing-Framework)
      2. [1. Test Cases, Test Suites and Testable Units]
2. [Functional Testing](Functional-Testing)
3. [CI/CD](CI/CD)
4. [Edge Cases](Edge-Cases)
    * Make sure to have example code

# Unit Testing
## What is Unit Testing? 
A unit test verifies the accuracy of a block of code, typically a function. 
This is incredibly useful for debugging and developing. Unit tests enable 
engineers to find bugs earlier in code that they are currently working on
and verify the accuracy of their code, answering the question "How do you know
that your code works?"

## Steps for unit testing
### 0. Testing Framework
Most commonly used programming languages have unit testing frameworks. C++ has 
gtest (among others, but gtest is most commonly used for C++), python has a 
built-in unit testing framework, Java has JUnit, etc. For our project we will 
use the built-in python unit testing framework [unittest](https://docs.python.org/3/library/unittest.html).

### 1. Test Cases, Test Suites and Testable Units
Generally a unit test should be one test case. Testing suites aggregate unit
tests that should be run together, for example unit tests that verify the parser
for our project should be aggregated into a testing suite. Unit tests work best 
on functions that do one thing (Not a swiss army knife, which is a function that 
attempts to do everything).

### 2. Writing a Unit Test
Unit tests can be split up into 3 parts: setup, verification, and teardown.
1. Setup is where you instantiate objects and variables used in the test
2. Verification is where you run your UUT (unit under test) and evaluate the 
output using an assert.
3. Teardown is only needed if you need to clean up after your test such as
freeing memory or deleting threads.

More in-depth unit test creation involves the usage of test fixtures to avoid
having to write the same test setups repeatedly or automating more complex 
setups.

The following is a simple example of a unit test from the python unit testing
library documentation https://docs.python.org/3/library/unittest.html:

```
import unittest

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
```

The first test `test_upper()` demonstrates how simple it is to create a unit 
test. This test requires no setup or teardown, only the UUT which is the 
`.upper` function of the string class. `test_split()` is a test that shows a 
setup, the `s = 'hello world'`, and also shows a demonstration of negative 
testing. Negative testing is when we expect the UUT to NOT do something. An 
example of this is seen in the above code where we expect that `s.split()` to 
fail when the parameter to `s.split()` is the int 2, and not a string.

The following is an example using a function `TraceFileParser.open` from our 
from our codebase.

```
def open(self) -> bool: 
    """Open the trace file""" 
    try: 
        self.fd = open(self.filename, 'r', encoding="utf-8") 
        return True
    except FileNotFoundError:    
        print(f"[ERROR] - could not find trace file '{self.filename}'") 
        return False
    except PermissionError: 
        print(f"[ERROR] - Permission denied accessing file: '{self.filename}'")
        return False
    except Exception as e: 
        print(f"[ERROR] - Opening file: {e}")
        return False
```

A unit test for this function could looks something like this:

```
class traceFileParser_Open(unittest.TestCase)

    def test_openFile(self):
        parser = TraceFileParser()
        self.assertTrue(parser.open("filename"))
    
    def test_FileNotFoundError:
        parser = TraceFileParser()
        self.assertFalse(parser.open("bad_filename"))

    def test_FileNotFoundError

```

Note, this would be a good function to refactor for returning the error instead
of immediately printing it. Then we can test the error message as well.

[Link to more unit test examples](https://github.com/mdhardenburgh/matrixLibrary/blob/main/unitTest/matrixTest.cpp).
These examples are in C++, but you can see the 2 of the 3 parts of a unit test: 
setup and verification. These examples did not need the optional teardown. 

#### Note on functions that do not return a value
These are a bit harder to test. In my experience, the function is modified to
return a value. However, this may not be desirable in some cases and debug 
prints could be parsed by the unit test, if the former solution is completely 
unworkable. 

#### Note on naming convention
Unit tests should be given a descriptive name such that someone reading it 
understands the purpose of the test. Ex: `test_multiply_tall_with_wide_matrix`.

# Functional Testing
Functional testing involves testing the entire application itself, simulating a
user. This can be done a few ways: manual testing, automated behavioral testing, 
or scripted testing. Manual testing is usually employed for code that has a GUI
or a linkage with a physical interface (such as physical buttons or knobs). 
Automated behavioral testing could be employed, but will require the 
implementation of a Gherkin parser (a non trivial task), which will
result in scope creep. Scripted testing would be the easiest method of 
functional testing. This would require the implementation of a test framework
(which will also be unit tested) to run the simulation, parse the output from 
the command line, and verify the output based on expected behavior. 

# CI/CD
Github has recently added a workflow automation feature called github actions. 
This is similar to Jenkins and can automatically run actions on certain 
conditions. These actions are determined by a yaml file and run in a docker
container on a Github server. The plan is to automatically run unit tests and
functional tests on every pull request and pull requests cannot be merged until
those tests pass. [Link to an example yaml file](https://github.com/mdhardenburgh/matrixLibrary/blob/main/.github/workflows/build-and-test-on-pull-request.yml).

# Edge Cases
It is important to consider edge cases when writing tests, but this is often
difficult to consider all edge cases when dealing with a complex software 
system. Instead there are paradigms and practices to employ when writing tests 
to attempt to catch important edge case bugs. These paradigms and practices are:
* Invalid inputs, does your program crash when you send in random garbage?
* boundary value testing, what happens when you exceed boundaries?
* 