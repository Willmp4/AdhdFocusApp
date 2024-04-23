const { ipcRenderer } = require("electron");

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
});

ipcRenderer.on("login-reply", (event, response) => {
  console.log("Login response:", response); // Enhanced debug log
});
