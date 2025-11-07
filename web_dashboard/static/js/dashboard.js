// Dashboard JavaScript
let hourlyChart = null;
let summaryChart = null;
let refreshInterval = null;
let countdownInterval = null;
let currentRefreshSeconds = 30;
let countdownSeconds = 30;
let selectedChannelIds = [];
let allChannels = [];

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
        selectedChannelIds = [];
        updateChannelSelectButton();
        document.getElementById('zone-filter').value = '';
        document.getElementById('refresh-interval').value = '30';
        currentRefreshSeconds = 30;
        localStorage.setItem('dashboard_refresh_interval', '30');
        updateRefreshInterval();
        loadSummary();
        loadRecentEvents();
    });

    // Channel modal handlers
    setupChannelModal();

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

    // Toggle events table
    const toggleEventsBtn = document.getElementById('toggle-events');
    const eventsWrapper = document.getElementById('events-wrapper');
    const toggleIcon = document.getElementById('toggle-icon');
    let eventsExpanded = true;

    // Load collapsed state from localStorage
    const savedEventsState = localStorage.getItem('dashboard_events_expanded');
    if (savedEventsState === 'false') {
        eventsExpanded = false;
        eventsWrapper.classList.add('collapsed');
        toggleIcon.classList.add('collapsed');
    }

    toggleEventsBtn.addEventListener('click', function() {
        eventsExpanded = !eventsExpanded;
        if (eventsExpanded) {
            eventsWrapper.classList.remove('collapsed');
            toggleIcon.classList.remove('collapsed');
        } else {
            eventsWrapper.classList.add('collapsed');
            toggleIcon.classList.add('collapsed');
        }
        localStorage.setItem('dashboard_events_expanded', eventsExpanded.toString());
    });

    // Load available channels and zones
    loadAvailableOptions();

    // Start auto-refresh
    updateRefreshInterval();
});

function loadAvailableOptions() {
    // Load channels from API
    fetch('/api/channels')
        .then(response => response.json())
        .then(data => {
            allChannels = data.channels || [];
            renderChannelsList();
        })
        .catch(error => {
            console.error('Error loading channels:', error);
        });

    // Load zones from summary API
    fetch('/api/summary')
        .then(response => response.json())
        .then(data => {
            // Populate zone filter
            const zoneSelect = document.getElementById('zone-filter');
            // Clear existing options except "Tất cả"
            while (zoneSelect.options.length > 1) {
                zoneSelect.remove(1);
            }
            data.available_zones.forEach(zone => {
                const option = document.createElement('option');
                option.value = zone;
                option.textContent = zone;
                zoneSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading zones:', error);
        });
}

function setupChannelModal() {
    const modal = document.getElementById('channel-modal');
    const openBtn = document.getElementById('channel-select-btn');
    const closeBtn = document.getElementById('modal-close');
    const cancelBtn = document.getElementById('modal-cancel');
    const applyBtn = document.getElementById('modal-apply');
    const selectAllBtn = document.getElementById('select-all-channels');
    const deselectAllBtn = document.getElementById('deselect-all-channels');

    // Open modal
    openBtn.addEventListener('click', function() {
        modal.style.display = 'block';
        updateChannelsCheckboxes();
    });

    // Close modal
    function closeModal() {
        modal.style.display = 'none';
    }

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Click outside modal to close
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Select all
    selectAllBtn.addEventListener('click', function() {
        selectedChannelIds = allChannels.map(ch => ch.channel_id);
        updateChannelsCheckboxes();
    });

    // Deselect all
    deselectAllBtn.addEventListener('click', function() {
        selectedChannelIds = [];
        updateChannelsCheckboxes();
    });

    // Apply selection
    applyBtn.addEventListener('click', function() {
        updateChannelSelectButton();
        closeModal();
        loadSummary();
        loadRecentEvents();
    });
}

function renderChannelsList() {
    const channelsList = document.getElementById('channels-list');
    channelsList.innerHTML = '';

    allChannels.forEach(channel => {
        const channelItem = document.createElement('div');
        channelItem.className = 'channel-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `channel-${channel.channel_id}`;
        checkbox.value = channel.channel_id;
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!selectedChannelIds.includes(channel.channel_id)) {
                    selectedChannelIds.push(channel.channel_id);
                }
            } else {
                selectedChannelIds = selectedChannelIds.filter(id => id !== channel.channel_id);
            }
        });

        const label = document.createElement('label');
        label.htmlFor = `channel-${channel.channel_id}`;
        label.className = 'channel-label';
        
        const address = channel.address || '';
        const location = channel.location || '';
        const description = channel.description || `Channel ${channel.channel_id}`;
        
        label.innerHTML = `
            <span class="channel-info">
                <strong>Channel ${channel.channel_id}</strong>
                <span class="channel-details">${address} - ${location}</span>
                <span class="channel-description">${description}</span>
            </span>
        `;

        channelItem.appendChild(checkbox);
        channelItem.appendChild(label);
        channelsList.appendChild(channelItem);
    });
}

function updateChannelsCheckboxes() {
    allChannels.forEach(channel => {
        const checkbox = document.getElementById(`channel-${channel.channel_id}`);
        if (checkbox) {
            checkbox.checked = selectedChannelIds.includes(channel.channel_id);
        }
    });
}

function updateChannelSelectButton() {
    const selectText = document.getElementById('channel-select-text');
    const countBadge = document.getElementById('channel-count-badge');
    
    if (selectedChannelIds.length === 0) {
        selectText.textContent = 'Chọn channels...';
        countBadge.style.display = 'none';
    } else if (selectedChannelIds.length === allChannels.length) {
        selectText.textContent = 'Tất cả channels';
        countBadge.style.display = 'none';
    } else {
        const selectedChannels = allChannels
            .filter(ch => selectedChannelIds.includes(ch.channel_id))
            .map(ch => `Ch${ch.channel_id}`)
            .join(', ');
        selectText.textContent = selectedChannels;
        countBadge.textContent = selectedChannelIds.length;
        countBadge.style.display = 'inline-block';
    }
}

function loadSummary() {
    const startDate = document.getElementById('start-date-filter').value;
    const endDate = document.getElementById('end-date-filter').value;
    const zone = document.getElementById('zone-filter').value;

    let url = `/api/summary?start_date=${startDate}&end_date=${endDate}`;
    if (selectedChannelIds.length > 0) {
        url += `&channel_ids=${selectedChannelIds.join(',')}`;
    }
    if (zone) {
        url += `&zone_id=${zone}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if data is valid
            if (!data) {
                throw new Error('Không có dữ liệu trả về');
            }

            // Update summary cards
            document.getElementById('total-enter').textContent = data.total_enter || 0;
            document.getElementById('total-exit').textContent = data.total_exit || 0;
            document.getElementById('unique-entered').textContent = data.unique_tracks_entered || 0;
            document.getElementById('unique-exited').textContent = data.unique_tracks_exited || 0;
            document.getElementById('net-count').textContent = data.net_count || 0;

            // Update charts - sử dụng số người (unique tracks) thay vì số lượt
            if (data.hourly_data) {
                updateHourlyChart(data.hourly_data, startDate, endDate);
            }
            updateSummaryChart(data.unique_tracks_entered || 0, data.unique_tracks_exited || 0);
        })
        .catch(error => {
            console.error('Error loading summary:', error);
            console.error('URL:', url);
            alert('Lỗi khi tải dữ liệu: ' + error.message);
        });
}

function loadRecentEvents() {
    const zone = document.getElementById('zone-filter').value;

    let url = `/api/recent-events?limit=50`;
    if (selectedChannelIds.length > 0) {
        url += `&channel_ids=${selectedChannelIds.join(',')}`;
    }
    if (zone) {
        url += `&zone_id=${zone}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const tbody = document.getElementById('events-tbody');
            tbody.innerHTML = '';

            if (data && data.events && data.events.length > 0) {
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
            console.error('URL:', url);
            document.getElementById('events-tbody').innerHTML = 
                '<tr><td colspan="6" class="loading">Lỗi khi tải dữ liệu: ' + error.message + '</td></tr>';
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

