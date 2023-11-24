let mediaRecorder;
let audioChunks = [];

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const options = { mimeType: 'audio/webm' };
            mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorder.start();
            audioChunks = [];
            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });
        })
        .catch(error => {
            console.error("Error accessing the microphone: ", error);
        });
}

function stopRecording() {
    mediaRecorder.stop();

    mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        sendAudioToServer(audioBlob);
    });
}

function sendAudioToServer(audioBlob) {
    let formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    fetch("http://localhost:5002/process", {
    method: "POST",
    body: formData
    })
    .then(response => {
    if (!response.ok) {
        throw new Error(`Server returned status: ${response.status}`);
    }
    return response.json();
    })
    .then(data => {
    console.log("Server response:", data);
    })
    .catch(error => {
    console.error("Error sending audio data to the server: ", error);
    });

}