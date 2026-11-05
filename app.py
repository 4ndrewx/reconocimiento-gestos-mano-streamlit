import streamlit as st
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(
    page_title="Reconocimiento de Gestos con la Mano",
    page_icon="✋",
    layout="wide",
)

st.title("✋ Reconocimiento de Gestos con la Mano en Tiempo Real")
st.write(
    "Utiliza tu cámara web para detectar gestos estáticos mediante MediaPipe y"
    " transmitirlos vía MQTT."
)

# Componente HTML y JavaScript incrustado para ejecutar la cámara y MediaPipe Hands
html_code = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js" type="text/javascript"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0E1117; color: white; text-align: center; margin: 0; padding-top: 10px; }
        .video-container { position: relative; width: 640px; height: 480px; margin: 0 auto; border-radius: 12px; overflow: hidden; box-shadow: 0px 4px 20px rgba(0,0,0,0.6); background: #1A1C23; }
        video, canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform: scaleX(-1); }
        canvas { pointer-events: none; }
        .info-box { margin-top: 15px; background: #1A1C23; padding: 12px; border-radius: 8px; border: 1px solid #333; display: inline-block; width: 600px; }
        #gesture-output { color: #10B981; font-size: 22px; font-weight: bold; }
        #mqtt-status { color: orange; font-weight: bold; }
    </style>
</head>
<body>
    <div class="video-container">
        <video id="webcam" autoplay playsinline></video>
        <canvas id="output_canvas" width="640" height="480"></canvas>
    </div>
    <div class="info-box">
        <p>Estado MQTT: <span id="mqtt-status">Conectando...</span> | Gesto: <span id="gesture-output">Esperando...</span></p>
    </div>

    <script>
        const videoElement = document.getElementById('webcam');
        const canvasElement = document.getElementById('output_canvas');
        const canvasCtx = canvasElement.getContext('2d');
        const gestureOutput = document.getElementById('gesture-output');
        const mqttStatus = document.getElementById('mqtt-status');

        const client = new Paho.MQTT.Client("broker.hivemq.com", Number(8000), "web_client_" + Math.random());
        client.onConnectionLost = (res) => { mqttStatus.innerText = "Desconectado"; mqttStatus.style.color = "red"; };
        client.connect({
            onSuccess: () => { mqttStatus.innerText = "Conectado"; mqttStatus.style.color = "#10B981"; },
            onFailure: () => { mqttStatus.innerText = "Error"; mqttStatus.style.color = "red"; }
        });

        let lastGesture = "";

        function onResults(results) {
            canvasCtx.save();
            canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
            canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
            
            if (results.multiHandLandmarks) {
                for (const landmarks of results.multiHandLandmarks) {
                    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 4});
                    drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 1, radius: 5});

                    const thumbTip = landmarks[4], thumbIp = landmarks[3];
                    const indexTip = landmarks[8], indexMcp = landmarks[5];
                    const middleTip = landmarks[12], middleMcp = landmarks[9];
                    const ringTip = landmarks[16], ringMcp = landmarks[13];
                    const pinkyTip = landmarks[20], pinkyMcp = landmarks[17];

                    let openHand = (indexTip.y < indexMcp.y) && (middleTip.y < middleMcp.y) && (ringTip.y < ringMcp.y) && (pinkyTip.y < pinkyMcp.y);
                    let thumbUp = (thumbTip.y < thumbIp.y) && (indexTip.y > indexMcp.y);
                    let thumbDown = (thumbTip.y > thumbIp.y) && (indexTip.y > indexMcp.y);

                    let currentGesture = "Desconocido";
                    if (openHand) currentGesture = "open_hand";
                    else if (thumbUp) currentGesture = "thumbs_up";
                    else if (thumbDown) currentGesture = "thumbs_down";

                    gestureOutput.innerText = currentGesture;

                    if (currentGesture !== lastGesture && currentGesture !== "Desconocido" && client.isConnected()) {
                        client.send(new Paho.MQTT.Message(currentGesture), "gestos/control/eafit");
                        lastGesture = currentGesture;
                    }
                }
            } else {
                gestureOutput.innerText = "No se detecta mano";
            }
            canvasCtx.restore();
        }

        const hands = new Hands({locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`});
        hands.setOptions({maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.6, minTrackingConfidence: 0.6});
        hands.onResults(onResults);

        const camera = new Camera(videoElement, {
            onFrame: async () => { await hands.send({image: videoElement}); },
            width: 640, height: 480
        });
        camera.start();
    </script>
</body>
</html>
"""

components.html(html_code, height=600)
