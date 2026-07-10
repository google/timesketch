# Use a lightweight python image
FROM python:3.12-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-privileged user for least-privilege execution
RUN useradd -u 1000 -m -s /bin/bash byotuser

# Copy implementation files and set ownership
COPY --chown=byotuser:byotuser *.py ./

# Drop root privileges
USER byotuser

# Entrypoint running the BYOT client
ENTRYPOINT ["python", "byot_client.py"]
