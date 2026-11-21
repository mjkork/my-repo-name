// Statistics page — Overview time-distribution chart.
// All three time-frame series cover the archer's FULL history and are
// pre-computed server-side, embedded via json_script. The frontend only
// slices a fixed-size window out of that history and swaps chart.data —
// no AJAX, no round-trip, even when paging through Earlier/Later.
(function () {
    const dataEl = document.getElementById("time-distribution-data");
    const canvas = document.getElementById("time-distribution-chart");
    const earlierBtn = document.getElementById("stats-chart-earlier");
    const laterBtn = document.getElementById("stats-chart-later");
    const rangeLabel = document.getElementById("stats-chart-range");
    if (!dataEl || !canvas || !earlierBtn || !laterBtn || !rangeLabel) return;

    const series = JSON.parse(dataEl.textContent);
    const BAR_COLOR = "#c9a961";
    const MONTH_ABBR = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];

    let frame = "month";
    let windowIndex = 0; // 0 = latest window; increases moving back in time

    // Windows are fixed-size slices of the full history, aligned to the
    // present: index 0 always ends at the current period. The earliest
    // window may hold fewer periods than window_size.
    function windowBounds(f, idx) {
        const length = series[f].labels.length;
        const size = series[f].window_size;
        const end = Math.max(0, length - idx * size);
        const start = Math.max(0, end - size);
        return { start, end };
    }

    function formatBoundary(f, iso, withYear) {
        const d = new Date(`${iso}T00:00:00`);
        if (f === "year") return String(d.getFullYear());
        const monthDay =
            f === "week"
                ? `${d.getDate()} ${MONTH_ABBR[d.getMonth()]}`
                : MONTH_ABBR[d.getMonth()];
        return withYear ? `${monthDay} ${d.getFullYear()}` : monthDay;
    }

    function rangeText(f, start, end) {
        const s = series[f];
        const startIso = s.period_starts[start];
        const endIso = s.period_starts[end - 1];
        const sameYear = startIso.slice(0, 4) === endIso.slice(0, 4);
        const startStr = formatBoundary(f, startIso, !sameYear);
        const endStr = formatBoundary(f, endIso, true);
        return startStr === endStr ? endStr : `${startStr} – ${endStr}`;
    }

    function sliceData(f, start, end) {
        return {
            labels: series[f].labels.slice(start, end),
            datasets: [
                {
                    data: series[f].data.slice(start, end),
                    backgroundColor: BAR_COLOR,
                    borderRadius: 4,
                },
            ],
        };
    }

    const initialBounds = windowBounds(frame, windowIndex);

    const chart = new Chart(canvas, {
        type: "bar",
        data: sliceData(frame, initialBounds.start, initialBounds.end),
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    max: series[frame].axis_max,
                    ticks: { precision: 0 },
                },
            },
        },
    });

    function syncControls(start, end) {
        rangeLabel.textContent = rangeText(frame, start, end);
        laterBtn.disabled = windowIndex === 0;
        earlierBtn.disabled = start === 0;
    }

    function applyWindow() {
        const { start, end } = windowBounds(frame, windowIndex);
        chart.data = sliceData(frame, start, end);
        chart.options.scales.y.max = series[frame].axis_max;
        chart.update();
        syncControls(start, end);
    }

    syncControls(initialBounds.start, initialBounds.end);

    document.querySelectorAll(".stats-timeframe-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            frame = btn.dataset.timeframe;
            windowIndex = 0;
            document
                .querySelectorAll(".stats-timeframe-btn")
                .forEach((b) => b.classList.toggle("is-active", b === btn));
            applyWindow();
        });
    });

    earlierBtn.addEventListener("click", () => {
        windowIndex += 1;
        applyWindow();
    });

    laterBtn.addEventListener("click", () => {
        windowIndex = Math.max(0, windowIndex - 1);
        applyWindow();
    });
})();
