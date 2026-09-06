// Statistics page — Overview time-distribution chart.
// All three time-frame series are pre-computed server-side and embedded via
// json_script; switching frames only swaps chart.data, no round-trip.
(function () {
    const dataEl = document.getElementById("time-distribution-data");
    const canvas = document.getElementById("time-distribution-chart");
    if (!dataEl || !canvas) return;

    const series = JSON.parse(dataEl.textContent);
    const BAR_COLOR = "#c9a961";

    function seriesToChartData(frame) {
        return {
            labels: series[frame].labels,
            datasets: [
                {
                    data: series[frame].data,
                    backgroundColor: BAR_COLOR,
                    borderRadius: 4,
                },
            ],
        };
    }

    const chart = new Chart(canvas, {
        type: "bar",
        data: seriesToChartData("month"),
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });

    document.querySelectorAll(".stats-timeframe-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const frame = btn.dataset.timeframe;
            document
                .querySelectorAll(".stats-timeframe-btn")
                .forEach((b) => b.classList.toggle("is-active", b === btn));
            chart.data = seriesToChartData(frame);
            chart.update();
        });
    });
})();
