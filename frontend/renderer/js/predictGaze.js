const { ipcRenderer } = require("electron");

// Gaze Tracking and Visualization
function initializeVideo() {
  const video = document.getElementById("video-input");
  if (!video) return; // Ensure video element exists
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
      video.play();
    })
    .catch(err => {
      console.error("Error accessing the camera:", err);
    });

  video.addEventListener('play', () => {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');

    (function updateFrame() {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const buffer = Buffer.from(imageData.data.buffer);

      ipcRenderer.send("predict-gaze", buffer, {width: canvas.width, height: canvas.height});
      requestAnimationFrame(updateFrame);
    })();
  });
}

// Update canvas with gaze points
function updateCanvas([gazeXScaled, gazeYScaled, adjustedXScaled, adjustedYScaled]) {
  const canvas = document.getElementById("gaze-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "red";
  ctx.beginPath();
  ctx.arc(gazeXScaled, gazeYScaled, 10, 0, 2 * Math.PI);
  ctx.fill();

  ctx.fillStyle = "blue";
  ctx.beginPath();
  ctx.arc(adjustedXScaled, adjustedYScaled, 10, 0, 2 * Math.PI);
  ctx.fill();
}

ipcRenderer.on("gaze-prediction", (event, prediction) => {
  if (prediction[0] !== null) {
    updateCanvas(prediction);
  } else {
    console.error("No gaze detected.");
  }
});

document.addEventListener('DOMContentLoaded', initializeVideo);
