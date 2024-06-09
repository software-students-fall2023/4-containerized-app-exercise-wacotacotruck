FROM python:3.8
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /machine_learning_client
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/librosa/librosa
COPY . .
EXPOSE 5002
CMD ["python", "ml.py"]