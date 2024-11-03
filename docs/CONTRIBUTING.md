# Contributing to the Project

## Local Development using Docker

### Building the Docker Image

To build the Docker image for the program, run the following command:

```bash
docker build -t llcsim:latest .
```

This command builds the Docker image and tags it as `llcsim` with the `latest` version.

**NOTE:** Adding a Python package in requirements.txt will require rebuilding to ensure the new package is contained in the image.

### Running the Docker Container

After building the image, you can run the container using the command:

```bash
docker run --rm llcsim:latest
```

This will run `main.py` and exit. The `--rm` flag ensures that the container is removed after it exits.

## Using Docker Compose

### Starting the Development Environment

To start the development environment, use the following command:
```bash
docker compose up -d dev && docker compose exec dev bash
```

This command does two things:

1. Starts the `dev` service in detached mode (`-d`), allowing you to run it in the background.
1. Executes a bash shell in the running `dev` container, where you can run the program.

Once inside the container, you can execute your main program using:
```bash
python main.py
```

### Container Behavior
After exiting the shell, the `dev` container will still be running because it was started with a command that keeps it alive. You can stop this container by running:
```bash
docker compose down
```
Or you can connect to the shell again using `docker compose exec dev bash`.

### Running the Main Program
If you want to run the main program directly using `docker compose` and let the container exit upon completion, you can use:
```bash
docker compose up app
```
In this case, the container will run the `app` service defined in the `docker-compose.yml` file, execute the program, and then stop when the program finishes.

The `compose.yml` services may be extended in the future to support a `test` service, which could be used in a Github Actions environment.

## Code Quality Tools

We use **Black** for formatting, **Flake8** for linting, and **isort** to maintain consistent dependency import ordering and formatting. This section explains how to run each tool on the `src` directory to check code quality, and how to apply changes if any issues are found.

### Black (Code Formatter)

**Black** is used to automatically format Python code to adhere to a consistent style.

1. **Check Only**: To check if there are any formatting issues without modifying files, run:
```bash
black --check src/
```
or for additional detail:
```bash
black --diff src/
```

2. **Apply Formatting**: To automatically format all files in the `src` directory, run:
```bash
black src/
```

3. **Overriding Automated Formatting**: If there are specific lines or code blocks where you need to override Black’s automated formatting, you can use `# fmt: off` and `# fmt: on` comments. Black will skip formatting for code between these markers.
```python
# fmt: off
example = [
    "This", "is", "a", "long", "list", "that", "we", "want", "to", "format",
    "manually", "for", "readability", "even", "though", "Black", "would",
    "normally", "format", "it", "differently"
]
# fmt: on
```

Place `# fmt: off` before the code you want to exclude from formatting, and `# fmt: on` after it. Use these sparingly, as consistent formatting across the codebase is preferred. See the [Black documentation](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html#ignoring-sections) for more details.

### Flake8 (Code Linter)

**Flake8** is used to identify potential errors, code style issues, and other coding standard violations.

**Note**: Flake8 does not modify files, so the following command is sufficient to identify any issues that need to be manually addressed.
```bash
flake8 src/
```

### isort (Import Sorter)

**isort** is used to organize imports in Python files.

1. **Check Only**: To check for import order issues without making any changes, run:
```bash
isort --check-only src/
```

2. **Sort Imports**: To automatically sort and organize imports in all Python files within `src`, run:
```bash
isort src/
```
