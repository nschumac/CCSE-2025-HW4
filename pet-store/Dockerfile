# FROM python:3.11-slim

# Copy requirements file
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Set working directory
WORKDIR /app

# Copy application file
COPY app.py /app/app.py

# Create pictures directory
RUN mkdir -p /app/pictures

# Default environment variables (can be overridden)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV STORE_ID=1
ENV MONGODB_URI=mongodb://mongo:27017/
ENV PORT=5001

# Expose the port
EXPOSE 5001 5002

# Run the application
CMD ["python", "app.py"]
