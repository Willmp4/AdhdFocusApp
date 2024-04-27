const { screen } = require("electron");
const ioHook = require("iohook");
const robot = require("robotjs");
const cv = require("opencv4nodejs");
const { GazePredictor } = require("./gazePredictor");
const os = require("os");
const { EventEmitter } = require("events");

class ActivityMonitor extends EventEmitter {
  constructor(dataUploader) {
    super();
    this.dataUploader = dataUploader;
    this.userId = os.userInfo().username;
    this.events = [];
    this.lastMouseEventTime = Date.now();
    this.mouseStartPosition = null;
    this.keyboardActivityBuffer = [];
    this.lastKeyboardActivityTime = null;
    this.gazePredictor = new GazePredictor();
  }

  logEvent(eventType, data) {
    const timestamp = new Date().toISOString();
    const event = { timestamp, eventType, data };
    this.events.push(event);
  }

  onKeyPress(event) {
    const currentTime = Date.now();
    if (!this.keyboardActivityBuffer.length || currentTime - this.lastKeyboardActivityTime > 1000) {
      if (this.keyboardActivityBuffer.length) {
        this.endKeyboardSession();
      }
      this.keyboardActivityBuffer = [{ timestamp: new Date().toISOString(), key: event.keycode }];
    } else {
      this.keyboardActivityBuffer.push({ timestamp: new Date().toISOString(), key: event.keycode });
    }
    this.lastKeyboardActivityTime = currentTime;
    setTimeout(() => this.endKeyboardSession(), 1000);
  }

  endKeyboardSession() {
    if (this.keyboardActivityBuffer.length) {
      this.logEvent("keyboard_session", {
        start_time: this.keyboardActivityBuffer[0].timestamp,
        end_time: this.keyboardActivityBuffer[this.keyboardActivityBuffer.length - 1].timestamp,
        key_strokes: this.keyboardActivityBuffer.length,
      });
      this.keyboardActivityBuffer = [];
    }
  }

  onMouseDown(event) {
    this.logEvent("mouse_click", { position: [event.x, event.y], button: event.button });
    this.mouseStartPosition = [event.x, event.y];
  }

  onMouseUp(event) {
    if (this.mouseStartPosition) {
      this.logEvent("mouse_movement", { start_position: this.mouseStartPosition, end_position: [event.x, event.y] });
      this.mouseStartPosition = null;
    }
  }

  onMouseMove(event) {
    const currentTime = Date.now();
    if (currentTime - this.lastMouseEventTime > 500) {
      this.lastMouseEventTime = currentTime;
      if (!this.mouseStartPosition) {
        this.mouseStartPosition = [event.x, event.y];
      }
    }
  }

  monitorGaze() {
    const cap = new cv.VideoCapture(0);
    setInterval(() => {
      let frame = cap.read();
      frame = frame.bgrToGray();
      const { gaze_x, gaze_y, adjusted_x, adjusted_y } = this.gazePredictor.predictGaze(frame);
      if (gaze_x !== null) {
        this.logEvent("gaze_data", {
          gaze_start_position: [gaze_x, gaze_y],
          adjusted_gaze_start_position: [adjusted_x, adjusted_y],
        });
      }
    }, 300);
  }

  uploadEventsBatch() {
    const response = this.dataUploader.sendData(this.userId, this.events);
    console.log(`Upload response: ${response}`);
    this.events = [];
  }

  startMonitoring() {
    ioHook.on("keydown", this.onKeyPress.bind(this));
    ioHook.on("mousedown", this.onMouseDown.bind(this));
    ioHook.on("mouseup", this.onMouseUp.bind(this));
    ioHook.on("mousemove", this.onMouseMove.bind(this));
    ioHook.start();

    this.monitorGaze();
  }

  stopMonitoring() {
    ioHook.stop();
  }
}

module.exports = ActivityMonitor;
