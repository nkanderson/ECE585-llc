'''
functional tests will say something like, "running test xyz.py

tests will have a name, a possible testing resource file, expected output

test runner will run all the functional tests when the test runner is called say which
ones failed, which ones passed

'''
from tests import *
from abc import ABC, abstractmethod

def main():

    TC_1_work_in_progress()
    
    print("Begin Functional Tests")

# Step 1: Define the abstract class
class TestRunner(ABC):
    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def perimeter(self):
        pass

class FunctionalTest(TestRunner):
    def __init__(self, name):
        self.name = name

    def __init__(self, name, ):
        self.name = name
    def parseOutput(self):
        asdfasd = asdfasdf
    def expected(self):