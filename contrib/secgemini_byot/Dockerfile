# Use a lightweight python image
FROM python:3.12-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy implementation files
COPY *.py ./

# Entrypoint running the BYOT client
ENTRYPOINT ["python", "byot_client.py"]
