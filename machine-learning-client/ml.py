"""Module for the machine learning client."""
from flask import Flask, jsonify
import pyaudio
import numpy as np
from madmom.processors import SequentialProcessor, ParallelProcessor
from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor
import mido
from mido import Message
import threading
import aubio

app = Flask(__name__)

# MIDI setup
midi_output = mido.open_output()  # Open the first available MIDI port

@app.route("/process", methods=["POST"])
def process_data():
    """Starts the audio processing in a separate thread."""
    threading.Thread(target=rhythm_analysis).start()
    return jsonify({"status": "processing started"})

def send_midi_message(note, velocity, on=True):
    """Sends a MIDI message."""
    msg_type = 'note_on' if on else 'note_off'
    midi_message = Message(msg_type, note=note, velocity=velocity)
    midi_output.send(midi_message)

def schedule_note_off(note, delay):
    """Schedules a note-off message after a delay."""
    def off():
        time.sleep(delay)
        send_midi_message(note, velocity=64, on=False)
    threading.Thread(target=off).start()

def process_audio_data(data):
    """Process the audio data for onsets."""
    # Convert the audio data to a format aubio understands
    samples = np.frombuffer(data, dtype=aubio.float_type)

    # Detect onsets
    if onset_detector(samples):
        onset_time = onset_detector.get_last_s()
        print(f"Onset detected at: {onset_time} seconds")
        
        # Example: Send a MIDI note on message
        note = 60  # Middle C
        send_midi_message(note, velocity=64, on=True)

        # Schedule a note-off message after a short duration (e.g., 0.5 seconds)
        schedule_note_off(note, delay=0.5)

def rhythm_analysis():
    """Performs rhythm analysis and sends MIDI messages."""
    # Initialize PyAudio and audio stream
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    # Create beat detection processors
    beat_processor = SequentialProcessor([RNNBeatProcessor(), DBNBeatTrackingProcessor(fps=100)])

    try:
        while True:
            # Read audio stream
            data = np.frombuffer(stream.read(1024), dtype=np.float32)

            # Perform beat detection
            beats = beat_processor.process(data)

            # Perform onset detection
            process_audio_data(data)

            # If a beat is detected, send a MIDI message
            if beats:
                send_midi_message(note=60, velocity=64, on=True)
                # Implement logic for note_off messages

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Stop and close the stream and PyAudio
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)