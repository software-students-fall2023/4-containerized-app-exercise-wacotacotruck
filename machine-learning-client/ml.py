"""Module for the machine learning client."""
import subprocess
import os
import logging
import io 
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
import crepe
import pretty_midi
import soundfile as sf
import numpy as np

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
        
        confidence_threshold = 0.90
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
        logging.info(f"Chunked notes data for jsonify: {notes_data_sorted}")

        os.remove(webm_file)
        os.remove(wav_file)

        smoothed_notes = smooth_pitch_data(notes_data)

        filtered_and_combined_notes = filter_and_combine_notes(smoothed_notes)
        logging.info(f"Filtered and combined notes: {filtered_and_combined_notes}")

        midi_filename = create_midi_file(filtered_and_combined_notes)
        midi_url = url_for('static', filename=midi_filename)

        return jsonify({"midi_url": midi_url})
        
    except Exception as e:
        app.logger.error(f"Error processing data: {e}")
        return jsonify({"error": str(e)}), 500

def create_midi_file(filtered_notes, filename="output.mid"):
    logging.info(f"Received notes for MIDI creation: {filtered_notes}")
    logging.info("Starting to create MIDI file.")
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    midi_file_path = os.path.join(static_dir, filename)
    midi = pretty_midi.PrettyMIDI()
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano = pretty_midi.Instrument(program=piano_program)

    for note_info in filtered_notes:
        logging.info(f"Adding note: {note_info}")
        midi_note = pretty_midi.Note(
            velocity=100, 
            pitch=pretty_midi.note_name_to_number(note_info['note']),
            start=note_info['start_time'],
            end=note_info['end_time']
        )
        piano.notes.append(midi_note)

    midi.instruments.append(piano)
    midi.write(midi_file_path)
    logging.info(f"MIDI file written to {midi_file_path}")
    return filename


def smooth_pitch_data(notes_data, window_size=5):
    smoothed_data = []
    for i in range(len(notes_data)):
        start = max(i - window_size // 2, 0)
        end = min(i + window_size // 2 + 1, len(notes_data))
        window = notes_data[start:end]

        avg_time = sum(note['time'] for note in window) / len(window)
        note_counts = {}
        for note in window:
            note_counts[note['note']] = note_counts.get(note['note'], 0) + 1
        avg_note = max(note_counts, key=note_counts.get)

        smoothed_data.append({'time': avg_time, 'note': avg_note})
    return smoothed_data

def filter_and_combine_notes(notes_data, minimum_note_duration=0.1):
    filtered_notes = []
    last_note = None
    last_note_start_time = None

    for i, note in enumerate(notes_data):
        if last_note is not None and note['note'] != last_note:
            end_time = max(note['time'], last_note_start_time + minimum_note_duration)
            filtered_notes.append({
                'note': last_note, 
                'start_time': last_note_start_time, 
                'end_time': end_time
            })
            last_note = note['note']
            last_note_start_time = note['time']
        elif last_note is None:
            last_note = note['note']
            last_note_start_time = note['time']

    if last_note is not None:
        last_duration = notes_data[-1]['time'] - last_note_start_time
        end_time = max(notes_data[-1]['time'], last_note_start_time + minimum_note_duration)
        filtered_notes.append({
            'note': last_note, 
            'start_time': last_note_start_time, 
            'end_time': end_time
        })

    logging.info(f"Filtered notes: {filtered_notes}")
    return filtered_notes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
