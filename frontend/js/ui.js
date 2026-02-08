/**
 * UI panels - build menus, creature inspection, etc.
 * Will be expanded in later phases.
 */
export class UI {
    constructor(state) {
        this.state = state;
    }

    update() {
        // Update status bar elements
        const zEl = document.getElementById("z-level");
        if (zEl) {
            zEl.textContent = `Z: ${this.state.currentZ}`;
        }

        const pauseEl = document.getElementById("pause-status");
        if (pauseEl) {
            pauseEl.textContent = this.state.paused ? "PAUSED" : "";
        }
    }
}
