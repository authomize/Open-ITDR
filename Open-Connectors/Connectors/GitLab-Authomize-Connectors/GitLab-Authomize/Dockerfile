##############################
# Base Image
##############################
FROM python:3.9-slim as base

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

##############################
# Build Image
##############################
FROM base AS builder

# Install git and other OS-level dependencies
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y git

ENV PIPENV_VENV_IN_PROJECT 1

# Install pipenv and other dependencies
RUN pip install pipenv

# Install python dependencies in /.venv
COPY ["Pipfile", "Pipfile.lock", "./"]
RUN pipenv install --deploy

##############################
# Runtime Image
##############################
FROM base AS runtime

ARG UID=1000
ARG GID=1000

# Copy python environment from builder
COPY --from=builder /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

WORKDIR /authomize

# Copy code into runtime image
COPY ./*.py ./
COPY ./connectors ./connectors

# Add non-root user to run authomize syncs
RUN groupadd -g $GID authomize && \
  adduser \
  --gecos "" \
  --disabled-password \
  --shell "/sbin/nologin" \
  --no-create-home \
  --gid $GID \
  authomize && \
  chown -R authomize:authomize . && \
  chmod -R u=rw,g=rw,o=r,a+X .

USER authomize

# Command to run when starting the container
ENTRYPOINT ["python", "main.py"]
