/**
 * Keyboard and mouse input handling.
 * Sends commands to the backend via WebSocket.
 */
export class InputHandler {
    constructor(renderer, state, sendMessage) {
        this.renderer = renderer;
        this.state = state;
        this.sendMessage = sendMessage;

        // Designation mode
        this.designating = false;
        this.designStart = null;
        this.designationType = null;

        // Scroll speed
        this.scrollSpeed = 4;

        this._setupKeyboard();
        this._setupMouse();
    }

    _setupKeyboard() {
        document.addEventListener("keydown", (e) => {
            switch (e.key) {
                case "ArrowUp":
                case "w":
                    this.renderer.scroll(0, -this.scrollSpeed);
                    break;
                case "ArrowDown":
                case "s":
                    this.renderer.scroll(0, this.scrollSpeed);
                    break;
                case "ArrowLeft":
                case "a":
                    this.renderer.scroll(-this.scrollSpeed, 0);
                    break;
                case "ArrowRight":
                case "d":
                    this.renderer.scroll(this.scrollSpeed, 0);
                    break;
                case "<":
                case ",":
                    this._changeZLevel(1);
                    break;
                case ">":
                case ".":
                    this._changeZLevel(-1);
                    break;
                case " ":
                    this.sendMessage({ type: "pause" });
                    e.preventDefault();
                    break;
                case "Escape":
                    this.designating = false;
                    this.designStart = null;
                    this.designationType = null;
                    break;
            }
        });
    }

    _setupMouse() {
        this.renderer.canvas.addEventListener("mousemove", (e) => {
            const world = this.renderer.screenToWorld(e.clientX, e.clientY);
            const coordsEl = document.getElementById("coords");
            if (coordsEl) {
                coordsEl.textContent = `${world.x}, ${world.y}`;
            }
        });
    }

    _changeZLevel(delta) {
        const newZ = this.state.currentZ + delta;
        if (newZ >= 0 && newZ < this.state.depth) {
            this.sendMessage({
                type: "request_z_level",
                z: newZ,
            });
        }
    }
}
