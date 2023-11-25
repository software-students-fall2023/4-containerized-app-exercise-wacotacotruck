FROM python:3.8
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /machine-learning-client
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "ml.py"]

