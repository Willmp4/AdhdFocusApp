const { ipcRenderer } = require("electron");

document.getElementById("register-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const username = document.getElementById("register-username").value;
  const password = document.getElementById("register-password").value;

  ipcRenderer.send("register", { username, password });
});

ipcRenderer.on("register-reply", (event, response) => {
  if (response.success) {
    // Redirect to login or show success message
    console.log("Registration successful");
  } else {
    console.error("Registration failed:", response.message);
  }
});
