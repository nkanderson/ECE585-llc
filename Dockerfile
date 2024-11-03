FROM python:3.13-slim-bookworm

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Security updates, run as root:
RUN apt-get update && apt-get -y upgrade

COPY requirements.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Switch to non-root user:
RUN useradd --create-home llcsim
WORKDIR /home/llcsim
USER llcsim

COPY ./src .

CMD [ "python", "main.py" ]
