FROM python:3.9-slim
# Install libraries for making HTTP requests and for advanced ACL interaction
RUN pip install requests hvac
WORKDIR /app
# Copy our single, all-in-one script into the container
COPY run_all_examples.py /app/