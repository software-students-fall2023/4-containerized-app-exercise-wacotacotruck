"""Module for Testing Python Functions"""
import random
import pytest
import os
from unittest.mock import MagicMock
import numpy as np
import pretty_midi
from .. import ml


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

<<<<<<< HEAD
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
=======
    # This function is producing 7 warnings about Deprecation, not sure how to remove these...
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
>>>>>>> cfe6708b6f28772e540a0bf0bcd0e16f9a5b3e60
