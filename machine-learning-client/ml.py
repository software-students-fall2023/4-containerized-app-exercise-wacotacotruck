"""Module for the machine learning client."""
import subprocess
import os
import logging
import librosa

# import io (commented out because import is unused currently)
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


def write_audio_to_file(file_name, audio_stream):
    """function to write audio to file"""
    with open(file_name, "wb") as file:
        file.write(audio_stream.read())


def sort_notes_data(notes_data):
    """function to sort notes data"""
    return sorted(notes_data, key=lambda x: x["time"])


def process_notes(notes_data):
    """function to process notes"""
    smoothed_notes = smooth_pitch_data(notes_data)
    return filter_and_combine_notes(smoothed_notes)


def generate_midi_url(filtered_and_combined_notes, onsets, durations, tempo):
    """function to generate midi url"""
    midi_filename = create_midi(filtered_and_combined_notes, onsets, durations, tempo, output_file='output.mid')
    return url_for("static", filename=midi_filename)


@app.route("/process", methods=["POST"])
def process_data():
    """Route to process the data."""
    try:
        webm_file = "temp_recording.webm"
        wav_file = "temp_recording.wav"

        # Write audio to file and convert formats
        write_audio_to_file(webm_file, request.files["audio"])
        convert_webm_to_wav(webm_file, wav_file)

        # Process audio chunks to get notes data
        audio, sr = sf.read(wav_file)
        notes_data = process_audio_chunks(audio, sr)
        notes_data_sorted = sort_notes_data(notes_data)
        logging.info("Chunked notes data for jsonify: %s", notes_data_sorted)

        # Clean up temporary files
        clean_up_files(webm_file, wav_file)

        # Further processing on notes data
        filtered_and_combined_notes = process_notes(notes_data)

        onsets = detect_note_onsets(wav_file)
        durations = estimate_note_durations(onsets, audio_length=len(audio)/sr)
        tempo = estimate_tempo(wav_file)

        midi_url = generate_midi_url(filtered_and_combined_notes, onsets, durations, tempo)
        return jsonify({"midi_url": midi_url})
        #store file in database, grab from there and show.

    except IOError as io_err:
        app.logger.error("IO error occurred: %s", io_err)
        return jsonify({"error": str(io_err)}), 500
    except ValueError as val_err:
        app.logger.error("Value error occurred: %s", val_err)
        return jsonify({"error": str(val_err)}), 500


# commented out the following function due to too many local variables
# a revised version is as above
# def process_data():
#     """Route to process the data."""
#     try:
#         webm_file = "temp_recording.webm"
#         wav_file = "temp_recording.wav"

#         with open(webm_file, "wb") as file:
#             file.write(request.files["audio"].read())

#         convert_webm_to_wav(webm_file, wav_file)

#         audio, sr = sf.read(wav_file)

#         confidence_threshold = 0.90
#         chunk_size = 1024 * 10
#         notes_data = []

#         for start in range(0, len(audio), chunk_size):
#             end = start + chunk_size
#             audio_chunk = audio[start:end]
#             # commented out due to unused variable activation
#             # original: time, frequency, confidence, activation = crepe.predict(
#             #     audio_chunk, sr, viterbi=True
#             # )

#             time, frequency, confidence, _ = crepe.predict(
#                 audio_chunk, sr, viterbi=True
#             )

#             for t, f, c in zip(time, frequency, confidence):
#                 if c >= confidence_threshold:
#                     note_name = frequency_to_note_name(f)
#                     notes_data.append(
#                         {
#                             "time": float(t),
#                             "note": note_name,
#                             "confidence": round(float(c), 2),
#                         }
#                     )

#         notes_data_sorted = sorted(notes_data, key=lambda x: x["time"])
#         # logging.info(f"Chunked notes data for jsonify: {notes_data_sorted}")
#         logging.info("Chunked notes data for jsonify: %s", notes_data_sorted)

#         os.remove(webm_file)
#         os.remove(wav_file)

#         smoothed_notes = smooth_pitch_data(notes_data)

#         filtered_and_combined_notes = filter_and_combine_notes(smoothed_notes)
#         # logging.info(f"Filtered and combined notes: {filtered_and_combined_notes}")
#         logging.info("Filtered and combined notes: %s", filtered_and_combined_notes)

#         midi_filename = create_midi_file(filtered_and_combined_notes)
#         midi_url = url_for("static", filename=midi_filename)

#         return jsonify({"midi_url": midi_url})


#     # commented out due to too general exception, original is as below
#     # except Exception as e:
#     #     # app.logger.error(f"Error processing data: {e}")
#     #     app.logger.error("Error processing data: %s", e)
#     #     return jsonify({"error": str(e)}), 500
#     except IOError as io_err:
#         app.logger.error("IO error occurred: %s", io_err)
#         return jsonify({"error": str(io_err)}), 500
#     except ValueError as val_err:
#         app.logger.error("Value error occurred: %s", val_err)
#         return jsonify({"error": str(val_err)}), 500

#def create_midi_file(filtered_notes, onsets, durations, tempo, filename="output.mid"):
#    """function to create midi file"""
#    # logging.info(f"Received notes for MIDI creation: {filtered_notes}")
#    logging.info("Received notes for MIDI creation: %s", filtered_notes)
#    logging.info("Starting to create MIDI file.")
#    static_dir = os.path.join(app.root_path, "static")
#    if not os.path.exists(static_dir):
#        os.makedirs(static_dir)
#
#    midi_file_path = os.path.join(static_dir, filename)
#    midi = pretty_midi.PrettyMIDI()
#    midi.estimate_tempo = tempo
#    piano_program = pretty_midi.instrument_name_to_program("Acoustic Grand Piano")
#    piano = pretty_midi.Instrument(program=piano_program)
#
#    for note_info in filtered_notes, onsets, durations:
#        # logging.info(f"Adding note: {note_info}")
#        logging.info("Adding note: %s", note_info)
#        midi_note = pretty_midi.Note(
#            velocity=100,
#            pitch=pretty_midi.note_name_to_number(note_info["note"]),
#            start=onsets,
#           end=durations,
#        )
#        piano.notes.append(midi_note)
#
#    midi.instruments.append(piano)
#    midi.write(midi_file_path)
#    # logging.info(f"MIDI file written to {midi_file_path}")
#    logging.info("MIDI file written to %s", midi_file_path)
#    return filename


def smooth_pitch_data(notes_data, window_size=5):
    """smoothing pitch data."""
    smoothed_data = []
    for i in range(len(notes_data)):
        start = max(i - window_size // 2, 0)
        end = min(i + window_size // 2 + 1, len(notes_data))
        window = notes_data[start:end]

        avg_time = sum(note["time"] for note in window) / len(window)
        note_counts = {}
        for note in window:
            note_counts[note["note"]] = note_counts.get(note["note"], 0) + 1
        avg_note = max(note_counts, key=note_counts.get)

        smoothed_data.append({"time": avg_time, "note": avg_note})
    return smoothed_data


def filter_and_combine_notes(notes_data, minimum_note_duration=0.1):
    """function to filter and combine notes."""
    filtered_notes = []
    last_note = None
    last_note_start_time = None

    # commented out due to unused i, original: for i, note in enumerate(notes_data):
    for note in enumerate(notes_data):
        if last_note is not None and note["note"] != last_note:
            end_time = max(note["time"], last_note_start_time + minimum_note_duration)
            filtered_notes.append(
                {
                    "note": last_note,
                    "start_time": last_note_start_time,
                    "end_time": end_time,
                }
            )
            last_note = note["note"]
            last_note_start_time = note["time"]
        elif last_note is None:
            last_note = note["note"]
            last_note_start_time = note["time"]

    if last_note is not None:
        # last_duration = notes_data[-1]["time"] - last_note_start_time
        # (commented out due to unused variable)
        end_time = max(
            notes_data[-1]["time"], last_note_start_time + minimum_note_duration
        )
        filtered_notes.append(
            {
                "note": last_note,
                "start_time": last_note_start_time,
                "end_time": end_time,
            }
        )

    # logging.info(f"Filtered notes: {filtered_notes}")
    logging.info("Filtered notes: %s", filtered_notes)
    return filtered_notes


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

def create_midi(filtered_notes, onsets, durations, tempo, output_file='output.mid'):
    logging.info("Received notes for MIDI creation: %s", filtered_notes)
    logging.info("Starting to create MIDI file.")
    static_dir = os.path.join(app.root_path, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    midi_file_path = os.path.join(static_dir, output_file)
    midi_data = pretty_midi.PrettyMIDI()
    midi_data.estimate_tempo = tempo
    instrument = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Acoustic Grand Piano'))

    for note_info, onset, duration in zip(filtered_notes, onsets, durations):
        logging.info("Adding note: %s", note_info)
        note_number = pretty_midi.note_name_to_number(note_info['note'])
        start_time = onset
        end_time = start_time + duration

        note = pretty_midi.Note(velocity=100, pitch=note_number, start=start_time, end=end_time)
        instrument.notes.append(note)

    midi_data.instruments.append(instrument)
    midi_data.write(midi_file_path)
    logging.info("MIDI file written to %s", midi_file_path)
    return output_file

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
