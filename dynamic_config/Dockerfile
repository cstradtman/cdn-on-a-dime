# Use a lightweight Python base image.
FROM python:alpine

# Set the working directory.
WORKDIR /app

# Copy your config service script into the container.
COPY dynamic_config.py .

# Install required Python dependencies.
RUN pip install flask pyyaml kubernetes

# Expose the port that the app listens on.
EXPOSE 5000

ARG CONFIG_SERVICE_VERSION="unknown"
ENV CONFIG_SERVICE_VERSION=$CONFIG_SERVICE_VERSION

# Run the Python script on container startup.
CMD ["python3", "dynamic_config.py", "--port", "5000"]
