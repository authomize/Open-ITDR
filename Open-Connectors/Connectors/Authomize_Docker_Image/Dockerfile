##############################
# Base Image
##############################
FROM python:3-slim as base

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

##############################
# Runtime Image
##############################
FROM base AS runtime

ARG UID=1000
ARG GID=1000

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install gcc, python3-dev, and the required packages from requirements.txt
RUN apt-get update && \
    apt-get install -y gcc python3-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc python3-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application files
COPY . .

# Add non-root user to run the application
RUN groupadd -g $GID appuser && \
  adduser \
  --gecos "" \
  --disabled-password \
  --shell "/sbin/nologin" \
  --no-create-home \
  --gid $GID \
  appuser && \
  chown -R appuser:appuser . && \
  chmod -R u=rw,g=rw,o=r,a+X .

USER appuser

# Start the main application
CMD ["python3", "/app/main.py"]