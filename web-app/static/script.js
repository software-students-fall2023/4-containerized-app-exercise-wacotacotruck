let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function startRecording() {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((stream) => {
      const options = { mimeType: "audio/webm" };
      mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorder.start();
      audioChunks = [];
      mediaRecorder.addEventListener("dataavailable", (event) => {
        audioChunks.push(event.data);
      });
    })
    .catch((error) => {
      console.error("Error accessing the microphone: ", error);
    });
}

function stopRecording() {
  mediaRecorder.stop();

  mediaRecorder.addEventListener("stop", () => {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    sendAudioToServer(audioBlob);
  });
}

function sendAudioToServer(audioBlob) {
  let formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  fetch("http://localhost:5002/process", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server returned status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server response:", data);
      displayMidiLink(data.midi_url);
    })
    .catch((error) => {
      console.error("Error sending audio data to the server: ", error);
    });
}

function displayMidiLink(midiUrl) {
  const linkContainer = document.getElementById("detectedNotesDisplay");
  linkContainer.innerHTML = "";
  const link = document.createElement("a");
  link.href = midiUrl;
  link.textContent = "Download MIDI File";
  link.download = "processed_midi.mid";
  linkContainer.appendChild(link);
  linkContainer.classList.remove("notes-display-hidden");
}

// Function to handle description button
function toggleDescription() {
  const modalBackground = document.getElementById("modal-background");
  if (
    modalBackground.style.display === "none" ||
    !modalBackground.style.display
  ) {
    modalBackground.style.display = "flex";
  } else {
    modalBackground.style.display = "none";
  }
}

function toggleRecording() {
  const recordButton = document.getElementById('recordButton');
  const recordIcon = document.getElementById('recordIcon');

  if (!isRecording) {
      startRecording();
      recordButton.title = "Stop Recording";
      recordIcon.textContent = "stop";
      recordButton.classList.add('recording');
  } else {
      stopRecording();
      recordButton.title = "Start Recording";
      recordIcon.textContent = "fiber_manual_record";
      recordButton.classList.remove('recording');
  }

  isRecording = !isRecording;
}