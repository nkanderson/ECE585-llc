# ECE 585 Final Project - Last Level Cache Simulation Program

## Usage

### Preparing the environment

The cache simulator requires several Python packages as noted in requirements.txt. The simplest way to prepare your runtime environment without breaking things is to create a virtual envronment before installing the needed packages. To do so execute the following command in the ECE585-llc directory (the name of the virtual environment can be changed to your liking):

```sh
python -m venv ./venv
```

After successful creation you can then activate your new virtual environment with the command:

```sh
source venv/bin/activate
```

Next install the packages. You will need pip installed on your system:

```sh
pip install -r requirements.txt
```
You should now have a virtual environment configured to run the simulator.

### Running the program

The following commands can be run from within the `src` directory of the project root, or the `app` directory if running in the Docker container.

```
main.py [-h] [-f FILE] [--capacity CAPACITY] [--line_size {4,16,32,64,128}] [--associativity {1,2,4,8,16,32}] [--protocol {MESI,MSI}] [-s] [-d]

options:
  -h, --help            show this help message and exit
  -f, --file FILE       Path to the trace file to process (default: data/trace.txt)
  --capacity CAPACITY   Total last-level cache capacity in megabytes (default: 16)
  --line_size {4,16,32,64,128}
                        Size of each cache line in bytes (default: 64)
  --associativity {1,2,4,8,16,32}
                        Number of ways in set-associative cache (default: 16)
  --protocol {MESI,MSI}
                        (NOTE: MSI option not yet implmented) Cache coherence protocol (default: MESI)
  -s, --silent          Reduce program output (default: False)
  -d, --debug           Enable debug output (default: False)
```

The following example will run the program with the specified input trace file of `cc1.din`, which is in the `data` directory. This will run in the `normal` output mode by default.

```sh
python -m main -f data/cc1.din
```

The following example will run the program with the default input trace file of `trace.txt`, which is in the `data` directory. This will run in the `silent` output mode.

```sh
python -m main --silent
```

### Running Tests

The testing commands can be run from the project root.

The following will run all of the tests in the `tests` directory.

```sh
PYTHONPATH=./src python -m unittest
```

It's also possible to run individual test files, or a specific test within a file. The following will run the `test_exclusive` integration test for the L1 write request.

```sh
PYTHONPATH=./app python -m unittest tests.integration.test_l1_write_request.TestCommandL1WriteRequest.test_exclusive
```

## Local Development

See [CONTRIBUTING.md](docs/CONTRIBUTING.md)
