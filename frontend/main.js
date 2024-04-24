const { app, BrowserWindow, ipcMain } = require("electron");
const axios = require("axios");

function createWindow() {
  let win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // Security warning noted
    },
  });

  win.loadFile("main.html");
  win.webContents.openDevTools(); // Open developer tools for debugging
}

app.whenReady().then(createWindow);

ipcMain.on("register", async (event, args) => {
  console.log("Received register event:", args); // Debug log
  try {
    const response = await axios.post("http://localhost:5000/register", {
      username: args.username,
      password: args.password,
    });
    console.log("Register success:", response.data); // Debug log
    event.reply("register-reply", response.data);
  } catch (error) {
    console.error("Register error:", error); // Error log
    event.reply("register-reply", { message: "Registration failed", error: error.message });
  }
});

ipcMain.on("login", async (event, args) => {
  console.log("Received login event:", args); // Debug log
  try {
    const response = await axios.post("http://localhost:5000/login", {
      username: args.username,
      password: args.password,
    });
    console.log("Login success:", response.data); // Debug log
    event.reply("login-reply", response.data);
  } catch (error) {
    console.error("Login error:", error); // Error log
    event.reply("login-reply", { message: "Login failed", error: error.message });
  }
  
  ipcMain.on('upload-activity', async (event, args) => {
    try {
      const response = await axios.post('http://localhost:5000/activity', args);
      event.reply('activity-upload-response', { message: 'Data uploaded successfully' });
    } catch (error) {
      event.reply('activity-upload-response', { message: 'Upload failed', error: error.message });
    }
  });
  
});
