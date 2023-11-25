"""Module for the machine learning client."""
from flask import Flask, request, jsonify
from flask_cors import CORS
import io 
import crepe
import pretty_midi
import soundfile as sf
import numpy as np
import subprocess
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

CORS(app)

def frequency_to_note_name(frequency):
    """Convert a frequency in Hertz to a musical note name."""
    if frequency <= 0:
        return None
    frequency = float(frequency)
    note_number = pretty_midi.hz_to_note_number(frequency)
    return pretty_midi.note_number_to_name(int(note_number))

@app.route("/process", methods=["POST"])
def process_data():
    try:
        webm_file = 'temp_recording.webm'
        wav_file = 'temp_recording.wav'
        with open(webm_file, 'wb') as file:
            file.write(request.files['audio'].read())
        result = subprocess.run(['ffmpeg', '-i', webm_file, wav_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("ffmpeg error:", result.stderr.decode())
            raise Exception("Error converting WebM to WAV")
        
        audio, sr = sf.read(wav_file)
        # logging.info(f"Audio data type: {audio.dtype}, Sample rate: {sr}")
        
        confidence_threshold = 0.74 
        chunk_size = 1024 * 10  
        notes_data = []

        for start in range(0, len(audio), chunk_size):
            end = start + chunk_size
            audio_chunk = audio[start:end]
            time, frequency, confidence, activation = crepe.predict(audio_chunk, sr, viterbi=True)
            
            for t, f, c in zip(time, frequency, confidence):
                if c >= confidence_threshold:
                    note_name = frequency_to_note_name(f)
                    notes_data.append({"time": float(t), "note": note_name, "confidence": round(float(c), 2) })

        notes_data_sorted = sorted(notes_data, key=lambda x: x['time'])
        #  logging.info(f"Chunked notes data for jsonify: {notes_data_sorted}")

        os.remove(webm_file)
        os.remove(wav_file)

        return jsonify(notes_data_sorted)
        
    except Exception as e:
        app.logger.error(f"Error processing data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
