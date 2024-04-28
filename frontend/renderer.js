const { ipcRenderer } = require("electron");

// User Authentication Handlers
document.getElementById("register-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const username = document.getElementById("register-username").value;
  const password = document.getElementById("register-password").value;

  console.log("Registering:", username); // Debug log
  ipcRenderer.send("register", { username, password });
});

document.getElementById("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  console.log("Logging in:", username); // Debug log
  ipcRenderer.send("login", { username, password });
});

ipcRenderer.on("register-reply", (event, response) => {
  console.log("Register response:", response); // Enhanced debug log
  if (response.success) {
    initializeVideo(); // Starts video feed on successful registration
  }
});

ipcRenderer.on("login-reply", (event, response) => {
  console.log("Login response:", response); // Enhanced debug log
  if (response.success) {
    initializeVideo(); // Starts video feed on successful login
  }
});

// Gaze Tracking and Visualization
function initializeVideo() {
  const video = document.getElementById("video-input");
  if (!video) return; // Ensure video element exists
  navigator.mediaDevices.getUserMedia({ video: true })
    .then((stream) => {
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
      const imageData = canvas.toDataURL('image/jpeg');
      ipcRenderer.send("predict-gaze", imageData);

      requestAnimationFrame(updateFrame);
    })();
  });
}

// Update canvas with gaze points
function updateCanvas([gazeXScaled, gazeYScaled, adjustedXScaled, adjustedYScaled]) {
  const canvas = document.getElementById("gaze-canvas");
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
