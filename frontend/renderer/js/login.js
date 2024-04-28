const { ipcRenderer } = require("electron");

document.getElementById("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  ipcRenderer.send("login", { username, password });
});

ipcRenderer.on("login-reply", (event, response) => {
  if (response.success) {
    // Redirect to dashboard or initialize video
    console.log("Login successful");
  } else {
    console.error("Login failed:", response.message);
  }
});
