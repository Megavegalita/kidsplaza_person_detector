// Dashboard JavaScript
let hourlyChart = null;
let summaryChart = null;
let refreshInterval = null;
let countdownInterval = null;
let currentRefreshSeconds = 30;
let countdownSeconds = 30;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('start-date-filter').value = today;
    document.getElementById('end-date-filter').value = today;

    // Load refresh interval from localStorage
    const savedInterval = localStorage.getItem('dashboard_refresh_interval');
    if (savedInterval) {
        currentRefreshSeconds = parseInt(savedInterval);
        document.getElementById('refresh-interval').value = savedInterval;
    }

    // Load initial data
    loadSummary();
    loadRecentEvents();

    // Setup event listeners
    document.getElementById('apply-filters').addEventListener('click', function() {
        loadSummary();
        loadRecentEvents();
    });

    document.getElementById('reset-filters').addEventListener('click', function() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('start-date-filter').value = today;
        document.getElementById('end-date-filter').value = today;
        document.getElementById('channel-filter').value = '';
        document.getElementById('zone-filter').value = '';
        document.getElementById('refresh-interval').value = '30';
        currentRefreshSeconds = 30;
        localStorage.setItem('dashboard_refresh_interval', '30');
        updateRefreshInterval();
        loadSummary();
        loadRecentEvents();
    });

    // Refresh interval change handler
    document.getElementById('refresh-interval').addEventListener('change', function() {
        const newInterval = parseInt(this.value);
        currentRefreshSeconds = newInterval;
        localStorage.setItem('dashboard_refresh_interval', newInterval.toString());
        updateRefreshInterval();
    });

    // Manual refresh button
    document.getElementById('manual-refresh').addEventListener('click', function() {
        loadSummary();
        loadRecentEvents();
        resetCountdown();
    });

    // Load available channels and zones
    loadAvailableOptions();

    // Start auto-refresh
    updateRefreshInterval();
});

function loadAvailableOptions() {
    fetch('/api/summary')
        .then(response => response.json())
        .then(data => {
            // Populate channel filter
            const channelSelect = document.getElementById('channel-filter');
            data.available_channels.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel;
                option.textContent = `Channel ${channel}`;
                channelSelect.appendChild(option);
            });

            // Populate zone filter
            const zoneSelect = document.getElementById('zone-filter');
            data.available_zones.forEach(zone => {
                const option = document.createElement('option');
                option.value = zone;
                option.textContent = zone;
                zoneSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading options:', error);
        });
}

function loadSummary() {
    const startDate = document.getElementById('start-date-filter').value;
    const endDate = document.getElementById('end-date-filter').value;
    const channel = document.getElementById('channel-filter').value;
    const zone = document.getElementById('zone-filter').value;

    let url = `/api/summary?start_date=${startDate}&end_date=${endDate}`;
    if (channel) {
        url += `&channel_id=${channel}`;
    }
    if (zone) {
        url += `&zone_id=${zone}`;
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Update summary cards
            document.getElementById('total-enter').textContent = data.total_enter || 0;
            document.getElementById('total-exit').textContent = data.total_exit || 0;
            document.getElementById('unique-entered').textContent = data.unique_tracks_entered || 0;
            document.getElementById('unique-exited').textContent = data.unique_tracks_exited || 0;
            document.getElementById('net-count').textContent = data.net_count || 0;

            // Update charts - sử dụng số người (unique tracks) thay vì số lượt
            updateHourlyChart(data.hourly_data, startDate, endDate);
            updateSummaryChart(data.unique_tracks_entered, data.unique_tracks_exited);
        })
        .catch(error => {
            console.error('Error loading summary:', error);
            alert('Lỗi khi tải dữ liệu: ' + error.message);
        });
}

function loadRecentEvents() {
    const channel = document.getElementById('channel-filter').value;
    const zone = document.getElementById('zone-filter').value;

    let url = `/api/recent-events?limit=50`;
    if (channel) {
        url += `&channel_id=${channel}`;
    }
    if (zone) {
        url += `&zone_id=${zone}`;
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('events-tbody');
            tbody.innerHTML = '';

            if (data.events && data.events.length > 0) {
                data.events.forEach(event => {
                    const row = document.createElement('tr');
                    const timestamp = new Date(event.timestamp);
                    const timeStr = timestamp.toLocaleString('vi-VN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });

                    row.innerHTML = `
                        <td>${timeStr}</td>
                        <td>Ch${event.channel_id}</td>
                        <td>${event.zone_id}</td>
                        <td class="event-${event.event_type}">${event.event_type.toUpperCase()}</td>
                        <td>${event.track_id}</td>
                        <td>${event.person_id || 'None'}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="loading">Không có dữ liệu</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading recent events:', error);
            document.getElementById('events-tbody').innerHTML = 
                '<tr><td colspan="6" class="loading">Lỗi khi tải dữ liệu</td></tr>';
        });
}

function updateHourlyChart(hourlyData, startDate, endDate) {
    const ctx = document.getElementById('hourly-chart').getContext('2d');
    
    // Prepare data - số người vào/ra theo giờ
    const hours = Object.keys(hourlyData).sort();
    const enterData = hours.map(h => hourlyData[h].enter || 0);
    const exitData = hours.map(h => hourlyData[h].exit || 0);

    if (hourlyChart) {
        hourlyChart.destroy();
    }

    // Format date range for title
    let dateRangeText = '';
    if (startDate && endDate) {
        const start = new Date(startDate).toLocaleDateString('vi-VN');
        const end = new Date(endDate).toLocaleDateString('vi-VN');
        if (start === end) {
            dateRangeText = ` - ${start}`;
        } else {
            dateRangeText = ` - ${start} đến ${end}`;
        }
    }

    // Update HTML title
    const chartTitleElement = document.getElementById('hourly-chart-title');
    if (chartTitleElement) {
        chartTitleElement.textContent = `Số người vào/ra theo giờ${dateRangeText}`;
    }

    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [
                {
                    label: 'Số người vào',
                    data: enterData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Số người ra',
                    data: exitData,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function updateSummaryChart(peopleEntered, peopleExited) {
    const ctx = document.getElementById('summary-chart').getContext('2d');

    if (summaryChart) {
        summaryChart.destroy();
    }

    summaryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Số người vào', 'Số người ra'],
            datasets: [{
                label: 'Số người',
                data: [peopleEntered, peopleExited],
                backgroundColor: [
                    '#28a745',
                    '#dc3545'
                ],
                borderColor: [
                    '#1e7e34',
                    '#c82333'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function updateRefreshInterval() {
    // Clear existing intervals
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }

    // Update display
    const refreshTimeSpan = document.getElementById('refresh-time');
    const refreshStatusDiv = document.querySelector('.refresh-status');

    if (currentRefreshSeconds === 0) {
        // Auto-refresh disabled
        refreshTimeSpan.textContent = 'Tắt';
        if (refreshStatusDiv) {
            refreshStatusDiv.style.opacity = '0.6';
        }
        return;
    }

    refreshTimeSpan.textContent = currentRefreshSeconds.toString();
    if (refreshStatusDiv) {
        refreshStatusDiv.style.opacity = '1';
    }

    // Reset countdown
    resetCountdown();

    // Start countdown timer
    countdownInterval = setInterval(function() {
        countdownSeconds--;
        document.getElementById('countdown').textContent = countdownSeconds.toString();
        
        if (countdownSeconds <= 0) {
            resetCountdown();
        }
    }, 1000);

    // Start auto-refresh
    refreshInterval = setInterval(function() {
        loadSummary();
        loadRecentEvents();
        resetCountdown();
    }, currentRefreshSeconds * 1000);
}

function resetCountdown() {
    countdownSeconds = currentRefreshSeconds;
    if (currentRefreshSeconds > 0) {
        document.getElementById('countdown').textContent = countdownSeconds.toString();
    }
}

