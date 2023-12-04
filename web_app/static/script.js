let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const host = "159.65.44.240";

function startRecording() {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((stream) => {
      const options = { mimeType: "audio/webm" };
      mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorder.ondataavailable = handleDataAvailable;
      mediaRecorder.onstop = handleStop;
      mediaRecorder.start();
      audioChunks = [];
    })
    .catch((error) => {
      console.error("Error accessing the microphone: ", error);
    });
}

function stopRecording() {
  mediaRecorder.stop();
}

function handleDataAvailable(event) {
  audioChunks.push(event.data);
}

function handleStop() {
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
  const userID = getCurrentUserID();
  sendAudioToServer(audioBlob, userID);
}

function sendAudioToServer(audioBlob, userID) {
  let formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  formData.append("user_id", userID);
  showLoader();

  fetch(`http://${host}:5002/process`, {
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
      //console.log("Server response:", data);
      displayMidiLink(data.midi_url);
    })
    .catch((error) => {
      console.error("Error sending audio data to the server: ", error);
    })
    .finally(() => {
      hideLoader();
    });
}

function getCurrentUserID(){
  return currentUserID;
}

function showLoader() {
  document.getElementById("loader").style.display = "flex";
}

function hideLoader() {
  document.getElementById("loader").style.display = "none";
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
  const recordButton = document.getElementById("recordButton");
  const recordIcon = document.getElementById("recordIcon");

  if (!isRecording) {
    startRecording();
    recordButton.title = "Stop Recording";
    recordIcon.textContent = "stop";
    recordButton.classList.add("recording");
  } else {
    stopRecording();
    recordButton.title = "Start Recording";
    recordIcon.textContent = "fiber_manual_record";
    recordButton.classList.remove("recording");
  }

  isRecording = !isRecording;
}

function playMidi() {
  const player = document.querySelector("midi-player");
  if (player) {
    player.start();
  }
}

function stopMidi() {
  const player = document.querySelector("midi-player");
  if (player) {
    player.stop();
  }
}

function playPostMidi(playerId) {
  const player = document.getElementById(playerId);
  if (player) {
    player.start();
  }
}

function stopPostMidi(playerId) {
  const player = document.getElementById(playerId);
  if (player) {
    player.stop();
  }
}

function displayMidiLink(midiUrl) {
  // Update MIDI player and visualizer source
  if (!midiUrl) {
    console.error("midi url is undefined");
    return;
  }
  // console.log(midiUrl); 
  const midiPlayer = document.querySelector("midi-player");
  const midiVisualizer = document.getElementById("myVisualizer");

  if (midiPlayer && midiVisualizer) {
    midiPlayer.src = midiUrl;
    midiVisualizer.src = midiUrl;
  }

  const saveButton = document.getElementById("save");
  if (saveButton) {
    saveButton.setAttribute("data-midi-url", midiUrl);
  }
}

function downloadMidi() {
  const saveButton = document.getElementById("save");
  const midiUrl = saveButton.getAttribute("data-midi-url");
  if (midiUrl) {
    window.location.href = midiUrl;
  }
}

function uploadMidi() {
  const midiPlayer = document.querySelector("midi-player");
  const midiSrc = midiPlayer ? midiPlayer.src : null;

  if (!midiSrc) {
    console.error("No MIDI source to upload");
    return;
  }

  const filename = midiSrc.split("/").pop();

  fetch(`http://${host}:5001/upload-midi`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename: filename }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error uploading MIDI file:", data.error);
      } else {
        console.log("MIDI file uploaded successfully:", data.message);
      }
    })
    .catch((error) => {
      console.error("Error in MIDI file upload:", error);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".midi-post").forEach((post) => {
    const midiPlayer = post.querySelector("midi-player");
    const midiVisualizer = post.querySelector("midi-visualizer");

    if (midiPlayer && midiVisualizer) {
      midiVisualizer.src = midiPlayer.src;
    }
  });
});

function downloadMidiPost(midiUrl) {
  if (midiUrl) {
    window.location.href = midiUrl; // This triggers the download
  }
}
