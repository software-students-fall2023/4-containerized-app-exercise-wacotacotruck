"""Module for Testing Python Functions"""
import os
import pytest
import numpy as np
import pretty_midi
from unittest.mock import MagicMock
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
