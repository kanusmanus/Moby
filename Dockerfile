FROM python:3.11-slim


WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
PIP_NO_CACHE_DIR=1 \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./
RUN pip install -r requirements.txt


COPY . .


EXPOSE 8000