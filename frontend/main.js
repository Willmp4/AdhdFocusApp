const { app, BrowserWindow, ipcMain } = require("electron");
const axios = require("axios");
const GazePredictor = require("./GazePredictor");
const { createFromBuffer } = require("image-js");

let win;
let gazePredictor;

function createWindow() {
  win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // Security warning noted
    },
  });

  win.loadFile("main.html");
  win.webContents.openDevTools(); // Open developer tools for debugging
  gazePredictor = new GazePredictor(); // Initialize the GazePredictor
}

app.whenReady().then(createWindow);

// Authentication routes
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
});

// Gaze Prediction route
// In main.js
ipcMain.on("predict-gaze", async (event, buffer, dimensions) => {
  try {
    const image = await createFromBuffer(buffer, {width: dimensions.width, height: dimensions.height});
    const prediction = await gazePredictor.predictGaze(image);
    event.reply("gaze-prediction", prediction);
  } catch (error) {
    console.error("Error in gaze prediction:", error);
    event.reply("gaze-prediction", [null, null, null, null]);
  }
});

