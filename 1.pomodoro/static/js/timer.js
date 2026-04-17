(function () {
    "use strict";

    // --- 定数 ---
    var WORK_SEC = 25 * 60;
    var SHORT_BREAK_SEC = 5 * 60;
    var LONG_BREAK_SEC = 15 * 60;
    var POMODOROS_BEFORE_LONG = 4;

    // --- 状態 ---
    var Mode = { WORKING: "WORKING", SHORT_BREAK: "SHORT_BREAK", LONG_BREAK: "LONG_BREAK" };
    var currentMode = Mode.WORKING;
    var completedWorkCount = 0;
    var timer = new TimerCore(WORK_SEC);
    var intervalId = null;
    var running = false;

    // --- DOM 要素 ---
    var timerDisplay = document.getElementById("timer-display");
    var statusEl = document.getElementById("status");
    var progressCircle = document.getElementById("progress-circle");
    var btnStart = document.getElementById("btn-start");
    var btnReset = document.getElementById("btn-reset");
    var completedCountEl = document.getElementById("completed-count");
    var totalTimeEl = document.getElementById("total-time");

    // --- SVG プログレスリング ---
    var RADIUS = 85;
    var CIRCUMFERENCE = 2 * Math.PI * RADIUS;
    progressCircle.style.strokeDasharray = CIRCUMFERENCE;

    // --- ヘルパー ---
    function formatTime(sec) {
        var m = Math.floor(sec / 60);
        var s = sec % 60;
        return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
    }

    function formatTotalTime(minutes) {
        if (minutes < 60) return minutes + "分";
        var h = Math.floor(minutes / 60);
        var m = minutes % 60;
        return m === 0 ? h + "時間" : h + "時間" + m + "分";
    }

    function updateDisplay() {
        timerDisplay.textContent = formatTime(timer.getRemaining());
        var progress = timer.getProgress();
        var offset = CIRCUMFERENCE * (1 - progress);
        progressCircle.style.strokeDashoffset = offset;
    }

    function updateStatus() {
        if (currentMode === Mode.WORKING) {
            statusEl.textContent = "作業中";
            progressCircle.style.stroke = "#6C63FF";
        } else if (currentMode === Mode.SHORT_BREAK) {
            statusEl.textContent = "休憩中";
            progressCircle.style.stroke = "#38c97a";
        } else {
            statusEl.textContent = "休憩中（ロング）";
            progressCircle.style.stroke = "#f5a623";
        }
    }

    function updateStats(data) {
        completedCountEl.textContent = data.completed_count;
        totalTimeEl.textContent = formatTotalTime(data.total_minutes);
    }

    // --- API ---
    function postComplete(durationMinutes) {
        fetch("/api/complete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ duration_minutes: durationMinutes }),
        })
            .then(function (res) { return res.json(); })
            .then(updateStats);
    }

    function fetchStats() {
        fetch("/api/stats")
            .then(function (res) { return res.json(); })
            .then(updateStats);
    }

    // --- 状態遷移 ---
    function transitionToNextMode() {
        if (currentMode === Mode.WORKING) {
            completedWorkCount++;
            postComplete(25);
            if (completedWorkCount % POMODOROS_BEFORE_LONG === 0) {
                currentMode = Mode.LONG_BREAK;
                timer.reset(LONG_BREAK_SEC);
            } else {
                currentMode = Mode.SHORT_BREAK;
                timer.reset(SHORT_BREAK_SEC);
            }
        } else {
            currentMode = Mode.WORKING;
            timer.reset(WORK_SEC);
        }
        updateStatus();
        updateDisplay();
        // 自動的に次のタイマーを開始
        startTimer();
    }

    // --- タイマー制御 ---
    function onTick() {
        timer.tick();
        updateDisplay();
        if (timer.isFinished()) {
            stopTimer();
            transitionToNextMode();
        }
    }

    function startTimer() {
        if (running) return;
        running = true;
        btnStart.textContent = "停止";
        intervalId = setInterval(onTick, 1000);
    }

    function stopTimer() {
        running = false;
        btnStart.textContent = "開始";
        if (intervalId !== null) {
            clearInterval(intervalId);
            intervalId = null;
        }
    }

    function resetTimer() {
        stopTimer();
        currentMode = Mode.WORKING;
        completedWorkCount = 0;
        timer.reset(WORK_SEC);
        updateStatus();
        updateDisplay();
    }

    // --- イベント ---
    btnStart.addEventListener("click", function () {
        if (running) {
            stopTimer();
        } else {
            startTimer();
        }
    });

    btnReset.addEventListener("click", resetTimer);

    // --- 初期化 ---
    updateStatus();
    updateDisplay();
    fetchStats();
})();
