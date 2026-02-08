/**
 * Canvas-based tile renderer using ASCII characters.
 * Renders tiles as colored text on a black background.
 */

// Tile type to display character and color mappings
const WALL_DISPLAY = {
    0: { ch: " ", fg: "#000" },           // AIR
    1: { ch: ".", fg: "#8B4513" },         // SOIL
    2: { ch: "#", fg: "#888" },            // STONE
    3: { ch: "#", fg: "#aaa" },            // GRANITE
    4: { ch: "~", fg: "#00f" },            // WATER
    5: { ch: "~", fg: "#f80" },            // MAGMA
    6: { ch: ".", fg: "#0a0" },            // GRASS
    7: { ch: "$", fg: "#b44" },            // IRON_ORE
    8: { ch: "$", fg: "#c84" },            // COPPER_ORE
    9: { ch: "$", fg: "#ff0" },            // GOLD_ORE
};

// Floor material display (used when tile is open air + has floor)
const FLOOR_DISPLAY = {
    0: { ch: "·", fg: "#444" },           // AIR (unknown floor)
    1: { ch: "·", fg: "#8B4513" },         // SOIL
    2: { ch: "·", fg: "#888" },            // STONE
    3: { ch: "·", fg: "#aaa" },            // GRANITE
    4: { ch: "≈", fg: "#00f" },            // WATER
    5: { ch: "≈", fg: "#f80" },            // MAGMA
    6: { ch: ",", fg: "#0a0" },            // GRASS
    7: { ch: "·", fg: "#b44" },            // IRON_ORE
    8: { ch: "·", fg: "#c84" },            // COPPER_ORE
    9: { ch: "·", fg: "#ff0" },            // GOLD_ORE
};

// Tile flags
const FLAG_WALKABLE = 1;
const FLAG_DIGGABLE = 2;
const FLAG_HAS_FLOOR = 4;
const FLAG_HAS_STAIR_UP = 8;
const FLAG_HAS_STAIR_DOWN = 16;
const FLAG_HAS_RAMP = 32;
const FLAG_HAS_BUILDING = 64;
const FLAG_DESIGNATED = 128;

export class Renderer {
    constructor(canvas, state) {
        this.canvas = canvas;
        this.ctx = canvas.getContext("2d");
        this.state = state;

        // Viewport offset in tiles
        this.viewX = 0;
        this.viewY = 0;

        // Tile size in pixels
        this.tileW = 12;
        this.tileH = 16;

        // Tiles visible on screen
        this.tilesWide = 0;
        this.tilesHigh = 0;

        this.resize();
        window.addEventListener("resize", () => this.resize());
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height - 24; // minus status bar

        this.tilesWide = Math.ceil(this.canvas.width / this.tileW);
        this.tilesHigh = Math.ceil(this.canvas.height / this.tileH);

        this.ctx.font = `${this.tileH - 2}px monospace`;
        this.ctx.textBaseline = "top";
    }

    /**
     * Center the viewport on a position.
     */
    centerOn(x, y) {
        this.viewX = x - Math.floor(this.tilesWide / 2);
        this.viewY = y - Math.floor(this.tilesHigh / 2);
    }

    scroll(dx, dy) {
        this.viewX += dx;
        this.viewY += dy;
        // Clamp
        if (this.state.width > 0) {
            this.viewX = Math.max(0, Math.min(this.viewX, this.state.width - this.tilesWide));
            this.viewY = Math.max(0, Math.min(this.viewY, this.state.height - this.tilesHigh));
        }
    }

    render() {
        const ctx = this.ctx;
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        if (!this.state.tiles) return;

        const tiles = this.state.tiles;

        // Draw tiles
        for (let sy = 0; sy < this.tilesHigh; sy++) {
            const wy = this.viewY + sy;
            if (wy < 0 || wy >= this.state.height) continue;
            const row = tiles[wy];
            if (!row) continue;

            for (let sx = 0; sx < this.tilesWide; sx++) {
                const wx = this.viewX + sx;
                if (wx < 0 || wx >= this.state.width) continue;

                const tile = row[wx];
                if (!tile) continue;

                const px = sx * this.tileW;
                const py = sy * this.tileH;

                this.drawTile(ctx, tile, px, py);
            }
        }

        // Draw creatures on current z-level
        for (const creature of this.state.creatures.values()) {
            if (creature.z !== this.state.currentZ) continue;

            const sx = creature.x - this.viewX;
            const sy = creature.y - this.viewY;
            if (sx < 0 || sx >= this.tilesWide || sy < 0 || sy >= this.tilesHigh) continue;

            const px = sx * this.tileW;
            const py = sy * this.tileH;

            // Draw background
            ctx.fillStyle = "#000";
            ctx.fillRect(px, py, this.tileW, this.tileH);

            // Draw creature char
            ctx.fillStyle = creature.color || "#fff";
            ctx.fillText(creature.char || "@", px + 1, py + 1);
        }

        // Draw items on current z-level
        for (const item of this.state.items.values()) {
            if (item.z !== this.state.currentZ) continue;

            const sx = item.x - this.viewX;
            const sy = item.y - this.viewY;
            if (sx < 0 || sx >= this.tilesWide || sy < 0 || sy >= this.tilesHigh) continue;

            // Only draw if no creature is at this position
            let hasCreature = false;
            for (const c of this.state.creatures.values()) {
                if (c.x === item.x && c.y === item.y && c.z === item.z) {
                    hasCreature = true;
                    break;
                }
            }
            if (hasCreature) continue;

            const px = sx * this.tileW;
            const py = sy * this.tileH;

            ctx.fillStyle = "#000";
            ctx.fillRect(px, py, this.tileW, this.tileH);

            ctx.fillStyle = item.color || "#888";
            ctx.fillText(item.char || "*", px + 1, py + 1);
        }
    }

    drawTile(ctx, tile, px, py) {
        const wallType = tile.w;
        const flags = tile.fl;

        // Determine what to display
        let ch, fg;

        if (flags & FLAG_HAS_STAIR_UP && flags & FLAG_HAS_STAIR_DOWN) {
            ch = "X";
            fg = "#aaa";
        } else if (flags & FLAG_HAS_STAIR_UP) {
            ch = "<";
            fg = "#aaa";
        } else if (flags & FLAG_HAS_STAIR_DOWN) {
            ch = ">";
            fg = "#aaa";
        } else if (flags & FLAG_HAS_RAMP) {
            ch = "▲";
            fg = "#888";
        } else if (flags & FLAG_HAS_BUILDING) {
            ch = "Ω";
            fg = "#c84";
        } else if (wallType !== 0) {
            // Has a wall
            const display = WALL_DISPLAY[wallType] || { ch: "?", fg: "#f0f" };
            ch = display.ch;
            fg = display.fg;
        } else if (flags & FLAG_HAS_FLOOR) {
            // Open space with floor - show floor material
            const groundType = tile.f;
            const floorDisplay = FLOOR_DISPLAY[groundType] || { ch: "·", fg: "#444" };
            ch = floorDisplay.ch;
            fg = floorDisplay.fg;
        } else {
            // Empty space (no floor, no wall)
            ch = " ";
            fg = "#000";
        }

        // Designation highlight
        let bg = "#000";
        if (flags & FLAG_DESIGNATED) {
            bg = "#330";
        }

        // Draw background
        if (bg !== "#000") {
            ctx.fillStyle = bg;
            ctx.fillRect(px, py, this.tileW, this.tileH);
        }

        // Draw character
        if (ch !== " ") {
            ctx.fillStyle = fg;
            ctx.fillText(ch, px + 1, py + 1);
        }
    }

    /**
     * Convert screen pixel coordinates to world tile coordinates.
     */
    screenToWorld(screenX, screenY) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = screenX - rect.left;
        const canvasY = screenY - rect.top;
        return {
            x: Math.floor(canvasX / this.tileW) + this.viewX,
            y: Math.floor(canvasY / this.tileH) + this.viewY,
        };
    }
}
