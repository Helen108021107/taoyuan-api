
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

function initDashboard() {
    const dataObj = window.DASHBOARD_DATA;

    if (!dataObj) {
        // Fallback or Empty State
        document.getElementById('page-title').textContent = "無資料";
        document.getElementById('metrics-cards').innerHTML = '<div class="stat-card">請使用 API 查詢資料</div>';
        return;
    }

    // 1. Process Metadata
    const title = dataObj.EffectiveComplexName || dataObj.Header || "統計資料";
    document.getElementById('page-title').textContent = title;

    const rawData = dataObj.Data || [];
    if (rawData.length === 0) {
        document.getElementById('table-body').innerHTML = '<tr><td colspan="5">無詳細資料</td></tr>';
        return;
    }

    document.getElementById('total-records').textContent = rawData.length.toLocaleString();

    // Get Year Range
    const years = [...new Set(rawData.map(d => d.DataDate))].sort();
    if (years.length > 0) {
        document.getElementById('year-range').textContent = years.length > 1
            ? `${years[0]} - ${years[years.length - 1]}`
            : years[0];
    }

    // 2. Identify Metrics (ComplexName1)
    // Sometimes ComplexName1 is the Metric, ComplexName2 is the District/Category.
    const metrics = [...new Set(rawData.map(d => d.ComplexName1))].filter(Boolean);

    // Setup Dropdown if multiple metrics
    const metricSelect = document.getElementById('metric-select');
    const controlsPanel = document.getElementById('controls-panel');

    let currentMetric = metrics[0] || "Value";

    if (metrics.length > 1) {
        controlsPanel.style.display = 'block';
        metricSelect.innerHTML = '';
        metrics.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            metricSelect.appendChild(opt);
        });
        metricSelect.addEventListener('change', (e) => {
            currentMetric = e.target.value;
            renderView(rawData, currentMetric, years);
        });
    }

    // Initial Render
    renderView(rawData, currentMetric, years);
}

let chartInstance = null;

function renderView(allData, metric, years) {
    // Filter data for current metric
    const filteredData = allData.filter(d => d.ComplexName1 === metric);

    // Update Chart Title
    document.getElementById('chart-title').textContent = metric;

    // --- Table Render ---
    const tableHead = document.getElementById('table-header');
    const tableBody = document.getElementById('table-body');

    // Dynamic Columns
    const columns = [
        { key: 'DataDate', label: '年度' },
        { key: 'PlaceName', label: '地點' },
        { key: 'ComplexName2', label: '細項/地區' },
        { key: 'FValue', label: '數值' }
    ];

    tableHead.innerHTML = columns.map(c => `<th>${c.label}</th>`).join('');

    tableBody.innerHTML = filteredData.map(row => `
        <tr>
            ${columns.map(c => `<td>${row[c.key] || '-'}</td>`).join('')}
        </tr>
    `).join('');

    // --- Stats & Ranking Calculation ---
    // Calculate based on the filtered data set

    // 1. Sort by Value for Ranking
    // Create a copy to avoid affecting other views if needed, though here we want mostly sorted data
    const sortedData = [...filteredData].sort((a, b) => b.FValue - a.FValue);

    // 2. Calculate Stats
    const totalVal = sortedData.reduce((acc, curr) => acc + curr.FValue, 0);
    const avgVal = sortedData.length > 0 ? totalVal / sortedData.length : 0;
    const maxItem = sortedData.length > 0 ? sortedData[0] : null;

    // Render Stats
    document.getElementById('stat-sum').textContent = totalVal.toLocaleString(undefined, { maximumFractionDigits: 1 });
    document.getElementById('stat-avg').textContent = avgVal.toLocaleString(undefined, { maximumFractionDigits: 1 });
    if (maxItem) {
        document.getElementById('stat-max').textContent = `${maxItem.FValue.toLocaleString()} (${maxItem.ComplexName2} - ${maxItem.DataDate})`;
    } else {
        document.getElementById('stat-max').textContent = '-';
    }

    // Render Ranking Table (Top 10)
    const rankingBody = document.getElementById('ranking-body');
    const top10 = sortedData.slice(0, 10);

    rankingBody.innerHTML = top10.map((d, index) => {
        // Highlight top 3
        let icon = '';
        if (index === 0) icon = '🥇 ';
        if (index === 1) icon = '🥈 ';
        if (index === 2) icon = '🥉 ';

        return `
            <tr>
                <td>${icon}${index + 1}</td>
                <td>${d.ComplexName2} <span style="font-size:0.8em; color:#64748b">(${d.DataDate})</span></td>
                <td style="text-align: right; font-family: monospace;">${d.FValue.toLocaleString()}</td>
            </tr>
        `;
    }).join('');

    // --- Chart Render ---
    const ctx = document.getElementById('mainChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    // Determine Chart Type
    // If multiple years, use Line chart of trend
    // If single year, use Bar chart of distribution (ComplexName2)

    const isMultiYear = years.length > 1;

    if (isMultiYear) {
        // Line Chart: X = Year, Series = ComplexName2 (District)
        const districts = [...new Set(filteredData.map(d => d.ComplexName2))];

        // Limit series to top 10 to avoid clutter? Or show all.
        // Let's show all for now, maybe filteredData is not too huge.

        const datasets = districts.map((dist, index) => {
            const distData = filteredData.filter(d => d.ComplexName2 === dist);
            // Sort by date
            distData.sort((a, b) => a.DataDate.localeCompare(b.DataDate));

            // Map years to values
            const dataPoints = years.map(y => {
                const record = distData.find(d => d.DataDate === y);
                return record ? record.FValue : null;
            });

            const color = getChartColor(index);
            return {
                label: dist,
                data: dataPoints,
                borderColor: color,
                backgroundColor: color,
                tension: 0.1,
                fill: false
            };
        });

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#f1f5f9' } }
                }
            }
        });

    } else {
        // Bar Chart: X = District (ComplexName2), Y = Value
        // Sort by Value DESC
        // Note: sortedData is already sorted, but filteredData might not be. 
        // Let's use sortedData for the chart to match the ranking table order.

        const labels = sortedData.map(d => d.ComplexName2);
        const values = sortedData.map(d => d.FValue);

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: metric,
                    data: values,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

function getChartColor(index) {
    const colors = [
        '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
        '#ec4899', '#6366f1', '#14b8a6', '#f97316', '#06b6d4'
    ];
    return colors[index % colors.length];
}
