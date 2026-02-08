/**
 * Entry point - WebSocket connection and render loop.
 */
import { GameState } from "./state.js";
import { Renderer } from "./renderer.js";
import { InputHandler } from "./input.js";
import { UI } from "./ui.js";

const WS_URL = `ws://${window.location.hostname}:8000/ws`;

const state = new GameState();
const canvas = document.getElementById("game-canvas");
const renderer = new Renderer(canvas, state);
const ui = new UI(state);

let ws = null;
let reconnectTimer = null;

function sendMessage(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
    }
}

const input = new InputHandler(renderer, state, sendMessage);

function connect() {
    const statusEl = document.getElementById("connection-status");

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        statusEl.textContent = "Connected";
        statusEl.className = "connected";
        if (reconnectTimer) {
            clearInterval(reconnectTimer);
            reconnectTimer = null;
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        state.handleMessage(data);

        // Center viewport when we first get world data
        if (data.type === "snapshot" && state.width > 0) {
            renderer.centerOn(
                Math.floor(state.width / 2),
                Math.floor(state.height / 2)
            );
        }
    };

    ws.onclose = () => {
        statusEl.textContent = "Disconnected";
        statusEl.className = "disconnected";
        if (!reconnectTimer) {
            reconnectTimer = setInterval(() => connect(), 3000);
        }
    };

    ws.onerror = () => {
        ws.close();
    };
}

// Render loop
let lastTime = 0;
let frameCount = 0;
let fpsTime = 0;

function renderLoop(timestamp) {
    // FPS counter
    frameCount++;
    if (timestamp - fpsTime > 1000) {
        const fpsEl = document.getElementById("fps");
        if (fpsEl) {
            fpsEl.textContent = `FPS: ${frameCount}`;
        }
        frameCount = 0;
        fpsTime = timestamp;
    }

    renderer.render();
    ui.update();

    requestAnimationFrame(renderLoop);
}

// Start
connect();
requestAnimationFrame(renderLoop);
