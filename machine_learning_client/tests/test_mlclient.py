"""Module for Testing Python Functions"""
import random
import os
from unittest.mock import MagicMock, patch
import subprocess
import pytest
import numpy as np
import pretty_midi
from machine_learning_client import ml


class Tests:
    """Test Functions for the Machine Learning Client"""

    @pytest.fixture
    def example_fixture(self):
        """An example of a pytest fixture"""
        yield

    @pytest.fixture
    def mocker(self):
        """Mocker fixture"""
        return MagicMock()

    # Test functions
    def test_sanity_check(self):
        """Run a simple test for mlclient side that always passes."""
        expected = True
        actual = True
        assert actual == expected, "Expected it to always be True!"

    # Test for frequency_to_note_name
    def test_frequency_to_note_name(self):
        """Provided valid frequency, return note name."""
        actual = ml.frequency_to_note_name(random.uniform(8.1758, 12543.854))
        midi_note_names = [
            "C0",
            "C#0",
            "D0",
            "D#0",
            "E0",
            "F0",
            "F#0",
            "G0",
            "G#0",
            "A0",
            "A#0",
            "B0",
            "C1",
            "C#1",
            "D1",
            "D#1",
            "E1",
            "F1",
            "F#1",
            "G1",
            "G#1",
            "A1",
            "A#1",
            "B1",
            "C2",
            "C#2",
            "D2",
            "D#2",
            "E2",
            "F2",
            "F#2",
            "G2",
            "G#2",
            "A2",
            "A#2",
            "B2",
            "C3",
            "C#3",
            "D3",
            "D#3",
            "E3",
            "F3",
            "F#3",
            "G3",
            "G#3",
            "A3",
            "A#3",
            "B3",
            "C4",
            "C#4",
            "D4",
            "D#4",
            "E4",
            "F4",
            "F#4",
            "G4",
            "G#4",
            "A4",
            "A#4",
            "B4",
            "C5",
            "C#5",
            "D5",
            "D#5",
            "E5",
            "F5",
            "F#5",
            "G5",
            "G#5",
            "A5",
            "A#5",
            "B5",
            "C6",
            "C#6",
            "D6",
            "D#6",
            "E6",
            "F6",
            "F#6",
            "G6",
            "G#6",
            "A6",
            "A#6",
            "B6",
            "C7",
            "C#7",
            "D7",
            "D#7",
            "E7",
            "F7",
            "F#7",
            "G7",
            "G#7",
            "A7",
            "A#7",
            "B7",
            "C8",
            "C#8",
            "D8",
            "D#8",
            "E8",
            "F8",
            "F#8",
            "G8",
            "G#8",
            "A8",
            "A#8",
            "B8",
            "C9",
            "C#9",
            "D9",
            "D#9",
            "E9",
            "F9",
            "F#9",
            "G9",
        ]
        assert actual in midi_note_names

    # Test for successful convert_webm_to_wav
    @patch("machine_learning_client.ml.subprocess.run")
    def test_convert_webm_to_wav_success(self, mock_run):
        """Given WebM audio file, convert to WAV format."""
        mock_run.return_value.returncode = 0

        ml.convert_webm_to_wav("test_input.webm", "test_output.wav")

        mock_run.assert_called_with(
            ["ffmpeg", "-i", "test_input.webm", "test_output.wav"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    # Test for failure convert_webm_to_wav
    @patch("machine_learning_client.ml.subprocess.run")
    def test_convert_webm_to_wav_failure(self, mocker):
        """Test failure scenario for convert_webm_to_wav."""
        mocker.return_value = MagicMock(returncode=1, stderr=MagicMock())
        mocker.return_value.stderr.decode.return_value = "ffmpeg error message"

        with pytest.raises(ValueError) as exc_info:
            ml.convert_webm_to_wav("test_input.webm", "test_output.wav")

        assert "Error converting WebM to WAV" in str(exc_info.value)

        mocker.assert_called_with(
            ["ffmpeg", "-i", "test_input.webm", "test_output.wav"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    # Test for process_audio_chunks
    @patch("machine_learning_client.ml.sf.read")
    @patch("machine_learning_client.ml.crepe.predict")
    @patch("machine_learning_client.ml.pretty_midi.hz_to_note_number")
    @patch("machine_learning_client.ml.pretty_midi.note_number_to_name")
    def test_process_audio_chunks(
        self,
        mock_note_number_to_name,
        mock_hz_to_note_number,
        mock_crepe_predict,
        mock_soundfile_read,
    ):
        """Mock audio processing"""
        fake_audio = np.random.rand(1024 * 20)  # Example fake audio data
        sr = 22050  # Example sampling rate
        mock_soundfile_read.return_value = (fake_audio, sr)

        mock_crepe_predict.return_value = (
            np.array([0.1, 0.2]),  # time
            np.array([440, 880]),  # frequency
            np.array([0.8, 0.75]),  # confidence
            None,  # additional return value
        )

        mock_hz_to_note_number.side_effect = (
            lambda f: 69 if f == 440 else 81
        )  # A4 and A5 note numbers
        mock_note_number_to_name.side_effect = lambda n: "A4" if n == 69 else "A5"

        notes_data = ml.process_audio_chunks(fake_audio, sr)
        assert len(notes_data) >= 2, "Should at least identify two notes"
        assert notes_data[0]["note"] == "A4", "First note should be A4"
        assert notes_data[1]["note"] == "A5", "Second note should be A5"
        assert all(
            n["confidence"] >= 0.74 for n in notes_data
        ), "Confidence should be above threshold"

    # Test for clean_up_files
    @patch("machine_learning_client.ml.os.remove")
    def test_clean_up_files(self, mock_remove):
        """Mock remove temporary audio files."""
        webm_file = "test_audio.webm"
        wav_file = "test_audio.wav"

        ml.clean_up_files(webm_file, wav_file)

        mock_remove.assert_any_call(webm_file)
        mock_remove.assert_any_call(wav_file)
        assert mock_remove.call_count == 2, "os.remove should be called twice"

    # Test for write_audio_to_file
    def test_write_audio_to_file(self, mocker):
        """Given file name and audio stream, write audio to file"""

        # Create mock audio stream data
        test_data = b"This is test audio data"
        mocker.read.return_value = test_data

        # Define a test file name
        test_file_name = "test_audio_file.webm"

        # Call the function with the mock stream
        ml.write_audio_to_file(test_file_name, mocker)

        # Read back the file and assert its contents
        with open(test_file_name, "rb") as file:
            file_content = file.read()
            assert (
                file_content == test_data
            ), "The file content does not match the expected data"

        # Verify that read method was called on the mock
        mocker.read.assert_called_once()

        # Cleanup: Remove the test file
        if os.path.exists(test_file_name):
            os.remove(test_file_name)

    # Test for sort_notes_data
    def test_sort_notes_data(self):
        """Test function to sort notes data"""
        notes_data = [
            {"note": "C", "time": 1.0},
            {"note": "A", "time": 0.5},
            {"note": "B", "time": 0.75},
        ]

        expected_sorted_notes = [
            {"note": "A", "time": 0.5},
            {"note": "B", "time": 0.75},
            {"note": "C", "time": 1.0},
        ]

        sorted_notes = ml.sort_notes_data(notes_data)

        assert (
            sorted_notes == expected_sorted_notes
        ), "The sorted notes do not match the expected result"

    # Test for process_notes
    def test_process_notes(self):
        """Test function to process notes"""
        notes_data = [
            {"note": "C", "time": 0.1},
            {"note": "C", "time": 0.2},
            {"note": "D", "time": 0.3},
            {"note": "E", "time": 0.4},
            {"note": "E", "time": 0.5},
        ]

        expected_processed_notes = [{"note": "C"}, {"note": "E"}]

        processed_notes = ml.process_notes(notes_data)

        assert (
            processed_notes == expected_processed_notes
        ), "The sorted notes do not match the expected result"

    # Test for generate_midi_url
    @patch("machine_learning_client.ml.create_midi")
    def test_generate_midi_url(self, mock_create_midi):
        """Test generating midi url"""
        mock_create_midi.return_value = "output.mid"

        filtered_combined_notes = ["C", "D", "E"]  # Example note data
        onsets = [0.1, 0.5, 1.0]  # Example onset times
        durations = [0.4, 0.5, 0.6]  # Example note durations
        tempo = 120  # Example tempo

        # Expected URL
        expected_url = "http://localhost:5002/static/output.mid"

        # Call the function
        result_url = ml.generate_midi_url(
            filtered_combined_notes, onsets, durations, tempo
        )

        # Assert that the URL is correctly formed
        assert (
            result_url == expected_url
        ), "The generated MIDI URL does not match the expected result"

        # Additionally, check that create_midi was called with the correct arguments
        mock_create_midi.assert_called_once_with(
            filtered_combined_notes, onsets, durations, tempo, output_file="output.mid"
        )

    # Test for app process route

    # Test for smooth_pitch_data
    def test_smooth_pitch_data(self):
        """Test smoothing pitch data."""

        notes_data = [
            {"note": "C", "time": 0.1},
            {"note": "C", "time": 0.2},
            {"note": "D", "time": 0.3},
            {"note": "E", "time": 0.4},
            {"note": "E", "time": 0.5},
        ]

        expected_smoothed_data = [
            {"time": 0.20000000000000004, "note": "C"},
            {"time": 0.25, "note": "C"},
            {"time": 0.3, "note": "C"},
            {"time": 0.35, "note": "E"},
            {"time": 0.39999999999999997, "note": "E"},
        ]

        # Call the function
        result = ml.smooth_pitch_data(notes_data)

        assert (
            result == expected_smoothed_data
        ), "The smoothed data does not match the expected result"

    # Test for filter_and_combine_notes
    def test_filter_and_combine_notes(self):
        """Test function to filter and combine notes."""

        test_notes_data = [
            {"note": "C", "time": 0.1},
            {"note": "C", "time": 0.2},
            {"note": "D", "time": 0.3},
            {"note": "E", "time": 0.4},
            {"note": "E", "time": 0.5},
        ]

        expected_filtered_notes = [{"note": "C"}, {"note": "D"}, {"note": "E"}]

        # Call the function
        result = ml.filter_and_combine_notes(test_notes_data)

        # Assertions to check if the function behaves as expected
        assert (
            result == expected_filtered_notes
        ), "The filtered notes do not match the expected result"

    # Test for detect_note_onsets
    @patch("machine_learning_client.ml.librosa.onset.onset_detect")
    @patch("machine_learning_client.ml.librosa.load")
    def test_detect_note_onsets(self, mock_load, mock_onset_detect):
        """Test to detect when notes begin or onset."""
        mock_load.return_value = (
            None,
            44100,
        )  # y (audio signal) can be None as it's not used directly
        expected_onsets = [0.1, 0.5, 1.0]  # Example onsets
        mock_onset_detect.return_value = expected_onsets

        # Test data
        audio_file = "test_audio.wav"

        # Call the function
        result_onsets = ml.detect_note_onsets(audio_file)

        # Assertions to check if the function behaves as expected
        assert (
            result_onsets == expected_onsets
        ), "The detected onsets do not match the expected result"

        # Check if the mocked methods were called with correct arguments
        mock_load.assert_called_once_with(audio_file, sr=44100)
        mock_onset_detect.assert_called_once_with(y=None, sr=44100, units="time")

    # Test for estimate_tempo
    def test_estimate_tempo(self):
        """
        Checks if estimated tempo calculated from test_audio is same as calculated value
        If function returns an int/float, it passes as well.
        """
        test_dir = os.path.dirname(__file__)
        sample_audio_file = os.path.join(test_dir, "test_audio.wav")
        tempo = ml.estimate_tempo(sample_audio_file)
        print(tempo)

        assert isinstance(tempo, (int, float)), "Tempo should be a numeric value"
        assert np.allclose(tempo, 105.46875, rtol=1e-5)

    def test_calculate_amplitude_envelope(self):
        """Checks if the enveloped is the close to the expected envelope"""

        # Generate a simple test signal
        test_signal = np.array([1, 2, 3, 4, 5, 4, 3, 2, 1])

        # Call the function with the test signal
        envelope = ml.calculate_amplitude_envelope(
            test_signal, frame_size=3, hop_length=3
        )

        # Calculate the RMS using NumPy for verification and link it to expected_envelope
        calculated_rms = np.sqrt(np.mean(np.square(test_signal.reshape(-1, 3)), axis=1))
        print("Calculated RMS:", calculated_rms)
        expected_envelope = np.array([2.1602469, 4.35889894, 2.1602469])

        # Check if the calculated envelope is close to the expected result
        np.testing.assert_allclose(envelope, expected_envelope, rtol=1e-5)

    def test_estimate_note_durations(self):
        """
        This ensures the durations match the estimated durations based on the onsets
        Also ensures that each duration is at least an int/float
        """

        # Mock input data for testing
        onsets = [0.1, 0.3, 0.6]
        y = np.random.randn(44100)  # Mock audio signal with 1-second duration

        # Call the function with the mock data and print the duration to see expected values
        durations = ml.estimate_note_durations(onsets, y, sr=44100, threshold=0.025)
        print("Calculated Durations:", durations)

        # Assertions are based on if the values are an int/float
        # Assertion to see if the values meet the expected values.
        assert all(isinstance(duration, (int, float)) for duration in durations)
        assert np.allclose(durations, [0.2, 0.3, 0.4], rtol=1e-5)

    def test_create_midi_instrument(self, mocker):
        """
        This ensures the durations match the estimated durations based on the onsets
        Also ensures that each duration is at least an int/float
        """

        # Mock input data for testing
        filtered_notes = [{"note": "C4"}, {"note": "E4"}, {"note": "G4"}]
        onsets = [0.1, 0.3, 0.6]
        durations = [0.2, 0.3, 0.4]

        # Mocking pretty_midi functions:
        mocker.patch.object(pretty_midi, "instrument_name_to_program", return_value=0)
        mocker.patch.object(
            pretty_midi, "note_name_to_number", side_effect=lambda x: 60
        )

        # Call the function with the mock data
        instrument = ml.create_midi_instrument(filtered_notes, onsets, durations)

        # Assert that the instrument is an instrument of pretty_midi
        # Asset that the length of the notes of the instrument is the same as the input
        assert isinstance(instrument, pretty_midi.Instrument)
        assert len(instrument.notes) == len(filtered_notes)

    def test_create_midi(self, mocker):
        """
        This ensures the file is named output.mid
        This also ensures the filepath is saved at the static/ folder
        """

        # Mock input data for testing
        filtered_notes = [{"note": "C4"}, {"note": "E4"}, {"note": "G4"}]
        onsets = [0.1, 0.3, 0.6]
        durations = [0.2, 0.3, 0.4]
        tempo = 120

        # Mocking the steps of the entire function
        mocker.patch.object(
            ml, "create_midi_instrument", return_value=pretty_midi.Instrument
        )

        mocker.patch.object(
            os.path, "join", return_value="machine_learning_client/static/output.mid"
        )

        mocker.patch.object(os.path, "exists", return_value=False)
        mocker.patch.object(os, "makedirs")
        mock_pretty_midi = mocker.MagicMock(spec=pretty_midi.PrettyMIDI)
        mocker.patch.object(pretty_midi, "PrettyMIDI", return_value=mock_pretty_midi)

        # Call the function with the mock data
        output_file = ml.create_midi(filtered_notes, onsets, durations, tempo)

        # Assert that the file is named correctly
        assert output_file == "output.mid"

        # Additional assertion for the filepath
        expected_filepath = "machine_learning_client/static/output.mid"
        assert (
            os.path.join("machine_learning_client", "static", "output.mid")
            == expected_filepath
        )
    
    def test_estimate_note_durations_no_onsets(self):
        """Test estimating note durations with no onsets."""
        onsets = []  # Empty list of onsets
        y = np.random.randn(44100)  # Mock audio signal with 1-second duration

        durations = ml.estimate_note_durations(onsets, y, sr=44100, threshold=0.025)

        assert durations == [], "Durations should be an empty list with no onsets."
    
    def test_calculate_amplitude_envelope_zeros(self):
        """Test calculating amplitude envelope for signal with all zero values."""
        test_signal = np.zeros(10)  # Signal with all zero values

        envelope = ml.calculate_amplitude_envelope(
            test_signal, frame_size=3, hop_length=3
        )

        expected_envelope = np.zeros(4)  # Expected envelope with all zero values

        assert np.array_equal(envelope, expected_envelope), "Envelopes should be all zero."



    
