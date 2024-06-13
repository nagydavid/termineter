# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the entire local project directory (including Pipfile and Pipfile.lock) into the container
COPY . .

# Install pipenv and project dependencies
RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

# Optional: Define environment variables
# ENV NAME=value

# Run termineter with the specified rc-file when the container launches
CMD ["pipenv", "run", "python", "./termineter", "--rc-file", "./console.rc"]