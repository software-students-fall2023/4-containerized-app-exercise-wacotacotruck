"""Module for the machine learning client."""
import os
import subprocess
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import crepe
import pretty_midi
import soundfile as sf

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


def convert_webm_to_wav(webm_file, wav_file):
    """Convert WebM audio file to WAV format."""
    result = subprocess.run(
        ["ffmpeg", "-i", webm_file, wav_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        print("ffmpeg error:", result.stderr.decode())
        raise ValueError("Error converting WebM to WAV")


def process_audio_chunks(audio, sr):
    """Process audio data in chunks and return notes data."""
    confidence_threshold = 0.74
    chunk_size = 1024 * 10
    notes_data = []

    for start in range(0, len(audio), chunk_size):
        audio_chunk = audio[start : (start + chunk_size)]
        time, frequency, confidence, activation = crepe.predict(
            audio_chunk, sr, viterbi=True
        )

        for t, f, c in zip(time, frequency, confidence, activation):
            if c >= confidence_threshold:
                note_name = frequency_to_note_name(f)
                notes_data.append(
                    {
                        "time": float(t),
                        "note": note_name,
                        "confidence": round(float(c), 2),
                    }
                )

    return notes_data


def clean_up_files(webm_file, wav_file):
    """Remove temporary audio files."""
    os.remove(webm_file)
    os.remove(wav_file)


@app.route("/process", methods=["POST"])
def process_data():
    """Route to process the data."""
    try:
        webm_file = "temp_recording.webm"
        wav_file = "temp_recording.wav"

        with open(webm_file, "wb") as file:
            file.write(request.files["audio"].read())

        convert_webm_to_wav(webm_file, wav_file)

        audio, sr = sf.read(wav_file)

        notes_data = process_audio_chunks(audio, sr)
        notes_data_sorted = sorted(notes_data, key=lambda x: x["time"])

        clean_up_files(webm_file, wav_file)

        return jsonify(notes_data_sorted)

    except ValueError as e:
        app.logger.error("Error processing data: %s", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
