# Use the Python image
FROM python:3.9

# Set the working directory
WORKDIR /app/fetch_news

# Copy the Python script and requirements file
COPY fetch_news.py requirements.txt /app/fetch_news/

# Install Python dependencies
RUN pip install -r /app/fetch_news/requirements.txt

# Set the environment variable
ENV OPENAI_API_KEY=$OPENAI_API_KEY

# Define the command to run when the container starts
CMD ["python", "/app/fetch_news/fetch_news.py"]
