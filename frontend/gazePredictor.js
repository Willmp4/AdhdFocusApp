import * as faceapi from "face-api.js";
import * as tf from "@tensorflow/tfjs-node";
import { screen } from "electron";
import path from "path";

export class GazePredictor {
  constructor(screenDimensions = screen.getPrimaryDisplay().size) {
    this.screenWidth = screenDimensions.width;
    this.screenHeight = screenDimensions.height;
    this.loadModels();
  }

  async loadModels() {
    // Load the face-api.js models
    await faceapi.nets.ssdMobilenetv1.loadFromUri("/models");
    await faceapi.nets.faceLandmark68Net.loadFromUri("/models");

    // Load the TensorFlow.js eye gaze model
    const gazeModelUrl = path.join(__dirname, "gaze_model", "model.json");
    this.model = await tf.loadGraphModel(`file://${gazeModelUrl}`);

    // Load the adjustment model from the 'adjustment_model' folder
    const adjustmentModelUrl = path.join(__dirname, "adjustment_model", "model.json");
    this.adjustmentModel = await tf.loadGraphModel(`file://${adjustmentModelUrl}`);
  }

  async extractEyeRegion(image, landmarks) {
    const eyePoints = landmarks.getLeftEye().concat(landmarks.getRightEye());
    const noseBridgePoints = landmarks.getNose();
    const allPoints = eyePoints.concat(noseBridgePoints);
    const region = allPoints.map((pt) => ({ x: pt.x, y: pt.y }));
    const min_x = Math.min(...region.map((pt) => pt.x));
    const max_x = Math.max(...region.map((pt) => pt.x));
    const min_y = Math.min(...region.map((pt) => pt.y));
    const max_y = Math.max(...region.map((pt) => pt.y));

    const croppedRegion = image.getRegion(new faceapi.Rect(min_x, min_y, max_x - min_x, max_y - min_y));
    return croppedRegion;
  }

  async getCombinedEyes(frame) {
    const detections = await faceapi.detectAllFaces(frame).withFaceLandmarks();
    if (!detections.length) return null;

    for (let detection of detections) {
      const landmarks = detection.landmarks;
      const combinedEyeRegion = await this.extractEyeRegion(frame, landmarks);
      if (combinedEyeRegion) {
        const resized = tf.image.resizeBilinear(tf.browser.fromPixels(combinedEyeRegion), [200, 100]);
        return resized.div(tf.scalar(255.0));
      }
    }
    return null;
  }

  async predictGaze(frame) {
    const combinedEyes = await this.getCombinedEyes(frame);
    if (combinedEyes) {
      const predictedGaze = this.model.predict(tf.expandDims(combinedEyes, 0));
      const [gazeX, gazeY] = predictedGaze.dataSync();
      const gazeXScaled = gazeX * this.screenWidth;
      const gazeYScaled = gazeY * this.screenHeight;

      const adjustedPred = this.adjustmentModel.predict(tf.tensor2d([gazeX, gazeY], [1, 2]));
      const [adjustedX, adjustedY] = adjustedPred.dataSync();
      const adjustedXScaled = adjustedX * this.screenWidth;
      const adjustedYScaled = adjustedY * this.screenHeight;

      return [gazeXScaled, gazeYScaled, adjustedXScaled, adjustedYScaled];
    }
    return [null, null, null, null];
  }
}
