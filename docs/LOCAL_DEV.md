# Local Development

## Docker Setup Instructions

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
