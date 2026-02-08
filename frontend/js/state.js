/**
 * Client-side game state. Stores world data received from the server
 * and applies deltas.
 */
export class GameState {
    constructor() {
        this.width = 0;
        this.height = 0;
        this.depth = 0;
        this.surfaceZ = 0;
        this.currentZ = 0;

        // Current z-level tile data: tiles[y][x] = {w, f, fl}
        this.tiles = null;

        // Creatures: id -> {x, y, z, type, name, char, color}
        this.creatures = new Map();

        // Items: id -> {x, y, z, type, char, color}
        this.items = new Map();

        this.paused = false;
    }

    handleMessage(data) {
        switch (data.type) {
            case "snapshot":
                this.width = data.width;
                this.height = data.height;
                this.depth = data.depth;
                this.surfaceZ = data.surface_z;
                this.currentZ = data.surface_z;
                if (data.creatures) {
                    this.creatures.clear();
                    for (const c of data.creatures) {
                        this.creatures.set(c.id, c);
                    }
                }
                break;

            case "z_level":
                this.tiles = data.tiles;
                this.currentZ = data.z;
                break;

            case "delta":
                this.applyDelta(data);
                break;

            case "pause_state":
                this.paused = data.paused;
                break;
        }
    }

    applyDelta(delta) {
        if (delta.tiles) {
            for (const tile of delta.tiles) {
                if (tile.z === this.currentZ && this.tiles) {
                    this.tiles[tile.y][tile.x] = {
                        w: tile.wall,
                        f: tile.floor,
                        fl: tile.flags,
                    };
                }
            }
        }

        if (delta.creatures) {
            for (const c of delta.creatures) {
                if (c.removed) {
                    this.creatures.delete(c.id);
                } else {
                    this.creatures.set(c.id, c);
                }
            }
        }

        if (delta.items) {
            for (const item of delta.items) {
                if (item.removed) {
                    this.items.delete(item.id);
                } else {
                    this.items.set(item.id, item);
                }
            }
        }
    }
}
