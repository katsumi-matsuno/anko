class TimerCore {
    constructor(durationSec) {
        this._totalSec = durationSec;
        this._remainingSec = durationSec;
    }

    tick() {
        if (this._remainingSec > 0) {
            this._remainingSec--;
        }
        return this._remainingSec;
    }

    isFinished() {
        return this._remainingSec <= 0;
    }

    reset(durationSec) {
        if (durationSec !== undefined) {
            this._totalSec = durationSec;
        }
        this._remainingSec = this._totalSec;
    }

    getRemaining() {
        return this._remainingSec;
    }

    getTotal() {
        return this._totalSec;
    }

    getProgress() {
        if (this._totalSec === 0) return 1;
        return this._remainingSec / this._totalSec;
    }
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = TimerCore;
}
