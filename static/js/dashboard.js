(() => {
    const dataElement = document.getElementById("dashboard-chart-data");

    if (!dataElement || typeof Chart === "undefined") {
        return;
    }

    const chartData = JSON.parse(dataElement.textContent || "{}");

    const hasValues = (dataset) =>
        Array.isArray(dataset?.values) && dataset.values.some((value) => value > 0);

    const emptyPlugin = {
        id: "emptyState",
        afterDraw(chart) {
            const values = chart.data.datasets?.[0]?.data || [];
            if (values.some((value) => Number(value) > 0)) {
                return;
            }

            const { ctx, chartArea } = chart;
            ctx.save();
            ctx.fillStyle = "#64748b";
            ctx.font = "600 14px system-ui, -apple-system, BlinkMacSystemFont, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(
                "Add transactions to see this chart.",
                (chartArea.left + chartArea.right) / 2,
                (chartArea.top + chartArea.bottom) / 2
            );
            ctx.restore();
        },
    };

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: "bottom" },
        },
    };

    const createChart = (id, config) => {
        const canvas = document.getElementById(id);
        if (!canvas) {
            return;
        }
        new Chart(canvas, config);
    };

    createChart("incomeExpenseChart", {
        type: "doughnut",
        data: {
            labels: chartData.incomeVsExpense?.labels || [],
            datasets: [{
                data: chartData.incomeVsExpense?.values || [],
                backgroundColor: ["#16a34a", "#dc2626"],
            }],
        },
        options: commonOptions,
        plugins: hasValues(chartData.incomeVsExpense) ? [] : [emptyPlugin],
    });

    createChart("expenseCategoriesChart", {
        type: "bar",
        data: {
            labels: chartData.expenseCategories?.labels || [],
            datasets: [{
                label: "Expenses",
                data: chartData.expenseCategories?.values || [],
                backgroundColor: "#f97316",
            }],
        },
        options: commonOptions,
        plugins: hasValues(chartData.expenseCategories) ? [] : [emptyPlugin],
    });

    createChart("monthlySpendingChart", {
        type: "line",
        data: {
            labels: chartData.monthlySpending?.labels || [],
            datasets: [{
                label: "Monthly spending",
                data: chartData.monthlySpending?.values || [],
                borderColor: "#2563eb",
                backgroundColor: "rgba(37, 99, 235, .16)",
                fill: true,
                tension: .35,
            }],
        },
        options: commonOptions,
        plugins: hasValues(chartData.monthlySpending) ? [] : [emptyPlugin],
    });

    createChart("weeklySpendingChart", {
        type: "line",
        data: {
            labels: chartData.weeklySpending?.labels || [],
            datasets: [{
                label: "Weekly spending",
                data: chartData.weeklySpending?.values || [],
                borderColor: "#7c3aed",
                backgroundColor: "rgba(124, 58, 237, .16)",
                fill: true,
                tension: .35,
            }],
        },
        options: commonOptions,
        plugins: hasValues(chartData.weeklySpending) ? [] : [emptyPlugin],
    });
})();
