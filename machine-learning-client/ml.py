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
import librosa

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
        midi_file = 'output.mid'

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

        onsets = detect_note_onsets(wav_file)
        durations = estimate_note_durations(onsets, audio_length=len(audio) / sr)
        tempo = estimate_tempo(wav_file)

        create_midi(notes_data_sorted, onsets, durations, tempo, output_file=midi_file)

        os.remove(webm_file)
        os.remove(wav_file)

        return jsonify(notes_data_sorted)
        #store file in database, grab from there and show.
        
    except Exception as e:
        app.logger.error(f"Error processing data: {e}")
        return jsonify({"error": str(e)}), 500

def detect_note_onsets(audio_file):
    y, sr = librosa.load(audio_file, sr=None)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    return onsets

def estimate_note_durations(onsets, audio_length):
    durations = np.diff(onsets, append=audio_length)
    return durations

def estimate_tempo(audio_file):
    y, sr = librosa.load(audio_file, sr=None)
    tempo, _ = librosa.beat.beat_track(y, sr=sr)
    return tempo

def create_midi(pitch_data, onsets, durations, tempo, output_file='output.mid'):
    midi_data = pretty_midi.PrettyMIDI()
    midi_data.estimate_tempo = tempo
    instrument = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Acoustic Grand Piano'))

    for pitch, onset, duration in zip(pitch_data, onsets, durations):
        note_number = pretty_midi.note_name_to_number(pitch['note'])
        start_time = onset
        end_time = start_time + duration

        note = pretty_midi.Note(velocity=100, pitch=note_number, start=start_time, end=end_time)
        instrument.notes.append(note)

    midi_data.instruments.append(instrument)
    midi_data.write(output_file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
