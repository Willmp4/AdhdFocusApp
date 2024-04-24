const { ipcRenderer } = require('electron');
const { keyboard, mouse } = require('@nut-tree/nut-js');

keyboard.config.autoDelayMs = 100;
mouse.config.autoDelayMs = 100;

let activityBuffer = [];
let lastActivityTime = Date.now();

async function monitorActivities() {
  keyboard.addListener('keydown', (event) => {
    const now = Date.now();
    if (now - lastActivityTime > 1000) {
      uploadActivities();  // Upload and clear buffer if more than 1 sec between events
    }
    activityBuffer.push({
      type: 'keyboard',
      key: event.key,
      timestamp: new Date().toISOString()
    });
    lastActivityTime = now;
  });

  mouse.addListener('click', (event) => {
    activityBuffer.push({
      type: 'mouse',
      action: 'click',
      position: event.position,
      button: event.button,
      timestamp: new Date().toISOString()
    });
  });

  mouse.addListener('mousemove', (event) => {
    activityBuffer.push({
      type: 'mouse',
      action: 'move',
      position: event.position,
      timestamp: new Date().toISOString()
    });
  });
}

function uploadActivities() {
  if (activityBuffer.length > 0) {
    ipcRenderer.send('upload-activity', { activities: activityBuffer });
    activityBuffer = [];  // Clear buffer after sending
  }
}

// Call this function when you want to start monitoring
monitorActivities();

// Handle responses from main process
ipcRenderer.on('activity-upload-response', (event, response) => {
  console.log('Upload response:', response);
});

// Ensure activities are uploaded before app quits
window.addEventListener('beforeunload', uploadActivities);
