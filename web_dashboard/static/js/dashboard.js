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

    // Setup mobile config modal
    setupMobileConfigModal();

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

    // Time interval apply button handler
    const timeIntervalSelect = document.getElementById('time-interval');
    const applyIntervalBtn = document.getElementById('apply-interval-btn');
    
    console.log('Setting up interval controls:', {
        timeIntervalSelect: !!timeIntervalSelect,
        applyIntervalBtn: !!applyIntervalBtn
    });
    
    if (applyIntervalBtn) {
        applyIntervalBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅ Apply interval button clicked');
            const selectedInterval = timeIntervalSelect ? timeIntervalSelect.value : '60';
            console.log('Selected interval:', selectedInterval);
            console.log('Calling loadSummary()...');
            loadSummary();
        });
        console.log('✅ Apply interval button event listener attached');
    } else {
        console.error('❌ apply-interval-btn not found in DOM!');
    }
    
    // Optional: Auto-apply on change (can be disabled if user prefers button only)
    if (timeIntervalSelect) {
        timeIntervalSelect.addEventListener('change', function() {
            console.log('Interval changed to:', this.value);
            // Auto-apply when interval changes
            loadSummary();
        });
        console.log('✅ Time interval select event listener attached');
    } else {
        console.error('❌ time-interval select not found in DOM!');
    }

    document.getElementById('reset-filters').addEventListener('click', function() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('start-date-filter').value = today;
        document.getElementById('end-date-filter').value = today;
        // Reset to default channels (10 and 11)
        selectedChannelIds = [10, 11];
        localStorage.setItem('dashboard_default_channels', JSON.stringify(selectedChannelIds));
        updateChannelSelectButton();
        updateChannelsCheckboxes();
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
    // Set default channels (10 and 11 for HCM) if no saved selection
    const savedChannelIds = localStorage.getItem('dashboard_default_channels');
    if (savedChannelIds) {
        try {
            selectedChannelIds = JSON.parse(savedChannelIds);
        } catch (e) {
            // If parse fails, use default
            selectedChannelIds = [10, 11];
        }
    } else {
        // Default to HCM channels 10 and 11
        selectedChannelIds = [10, 11];
        localStorage.setItem('dashboard_default_channels', JSON.stringify(selectedChannelIds));
    }
    
    // Load options and auto-load data after channels are selected
    loadAvailableOptions(false); // false = initial load, will auto-load data

    // Start auto-refresh
    updateRefreshInterval();
});

function loadAvailableOptions(preserveSelection = true) {
    const previousSelection = preserveSelection ? [...selectedChannelIds] : [];

    // Load channels from API
    fetch('/api/channels')
        .then(response => response.json())
        .then(data => {
            const fetchedChannels = (data.channels || []).map(channel => ({
                channel_id: Number(channel.channel_id),
                name: channel.name || `channel_${channel.channel_id}`,
                description: channel.description || '',
                location: channel.location || '',
                address: channel.address || channel.location || ''
            }));

            fetchedChannels.sort((a, b) => a.channel_id - b.channel_id);

            allChannels = fetchedChannels;

            if (preserveSelection) {
                // Preserve selection: keep only channels that still exist
                selectedChannelIds = previousSelection.filter((id) =>
                    allChannels.some((channel) => channel.channel_id === id)
                );
                // If no valid selection after filtering, use default (10, 11)
                if (selectedChannelIds.length === 0) {
                    selectedChannelIds = [10, 11].filter((id) =>
                        allChannels.some((channel) => channel.channel_id === id)
                    );
                    if (selectedChannelIds.length > 0) {
                        localStorage.setItem('dashboard_default_channels', JSON.stringify(selectedChannelIds));
                    }
                }
            } else {
                // If not preserving, check for saved default or use 10, 11
                const savedChannelIds = localStorage.getItem('dashboard_default_channels');
                if (savedChannelIds) {
                    try {
                        selectedChannelIds = JSON.parse(savedChannelIds);
                        // Filter to only existing channels
                        selectedChannelIds = selectedChannelIds.filter((id) =>
                            allChannels.some((channel) => channel.channel_id === id)
                        );
                    } catch (e) {
                        selectedChannelIds = [10, 11].filter((id) =>
                            allChannels.some((channel) => channel.channel_id === id)
                        );
                    }
                } else {
                    // Default to HCM channels 10 and 11 if they exist
                    selectedChannelIds = [10, 11].filter((id) =>
                        allChannels.some((channel) => channel.channel_id === id)
                    );
                    if (selectedChannelIds.length > 0) {
                        localStorage.setItem('dashboard_default_channels', JSON.stringify(selectedChannelIds));
                    }
                }
            }

            renderChannelsList();
            updateChannelsCheckboxes();
            updateChannelSelectButton();
            
            // Auto-load data if channels are selected (only on initial load, not when preserving)
            if (selectedChannelIds.length > 0 && !preserveSelection) {
                // Small delay to ensure UI is updated
                setTimeout(() => {
                    loadSummary();
                    loadRecentEvents();
                }, 100);
            }
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

function setupMobileConfigModal() {
    const mobileConfigBtn = document.getElementById('mobile-config-btn');
    const mobileConfigModal = document.getElementById('mobile-config-modal');
    const mobileConfigClose = document.getElementById('mobile-config-close');
    const mobileConfigCancel = document.getElementById('mobile-config-cancel');
    const mobileConfigApply = document.getElementById('mobile-config-apply');
    const filtersContainer = document.getElementById('filters-container');
    const mobileFiltersContainer = document.getElementById('mobile-filters-container');

    if (!mobileConfigBtn || !mobileConfigModal || !mobileFiltersContainer) {
        return; // Elements not found, skip setup
    }

    // Clone filters to mobile modal
    function cloneFiltersToModal() {
        mobileFiltersContainer.innerHTML = filtersContainer.innerHTML;
        // Re-attach event listeners for cloned elements
        const clonedApplyBtn = mobileFiltersContainer.querySelector('#apply-filters');
        const clonedResetBtn = mobileFiltersContainer.querySelector('#reset-filters');
        const clonedRefreshInterval = mobileFiltersContainer.querySelector('#refresh-interval');
        
        if (clonedApplyBtn) {
            clonedApplyBtn.addEventListener('click', function() {
                applyFiltersFromModal();
                closeMobileConfigModal();
            });
        }
        
        if (clonedResetBtn) {
            clonedResetBtn.addEventListener('click', function() {
                resetFilters();
                closeMobileConfigModal();
            });
        }
        
        if (clonedRefreshInterval) {
            clonedRefreshInterval.addEventListener('change', function() {
                const newInterval = parseInt(this.value);
                currentRefreshSeconds = newInterval;
                localStorage.setItem('dashboard_refresh_interval', newInterval.toString());
                updateRefreshInterval();
            });
        }
        
        // Re-setup time interval selector for cloned element
        const clonedTimeInterval = mobileFiltersContainer.querySelector('#time-interval');
        if (clonedTimeInterval) {
            clonedTimeInterval.addEventListener('change', function() {
                // Update main time interval selector
                const mainTimeInterval = document.getElementById('time-interval');
                if (mainTimeInterval) {
                    mainTimeInterval.value = this.value;
                }
            });
        }
        
        // Re-setup channel modal for cloned button
        const clonedChannelBtn = mobileFiltersContainer.querySelector('#channel-select-btn');
        if (clonedChannelBtn) {
            clonedChannelBtn.addEventListener('click', function() {
                const modal = document.getElementById('channel-modal');
                if (modal) {
                    modal.style.display = 'block';
                    updateChannelsCheckboxes();
                }
            });
        }
    }

    function applyFiltersFromModal() {
        // Copy values from modal to main filters
        const mobileStartDate = mobileFiltersContainer.querySelector('#start-date-filter');
        const mobileEndDate = mobileFiltersContainer.querySelector('#end-date-filter');
        const mobileZone = mobileFiltersContainer.querySelector('#zone-filter');
        const mobileRefreshInterval = mobileFiltersContainer.querySelector('#refresh-interval');
        const mobileTimeInterval = mobileFiltersContainer.querySelector('#time-interval');
        
        if (mobileStartDate) {
            document.getElementById('start-date-filter').value = mobileStartDate.value;
        }
        if (mobileEndDate) {
            document.getElementById('end-date-filter').value = mobileEndDate.value;
        }
        if (mobileZone) {
            document.getElementById('zone-filter').value = mobileZone.value;
        }
        if (mobileRefreshInterval) {
            document.getElementById('refresh-interval').value = mobileRefreshInterval.value;
            currentRefreshSeconds = parseInt(mobileRefreshInterval.value);
            localStorage.setItem('dashboard_refresh_interval', mobileRefreshInterval.value);
            updateRefreshInterval();
        }
        if (mobileTimeInterval) {
            const mainTimeInterval = document.getElementById('time-interval');
            if (mainTimeInterval) {
                mainTimeInterval.value = mobileTimeInterval.value;
            }
        }
        
        // Apply filters
        loadSummary();
        loadRecentEvents();
    }

    function resetFilters() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('start-date-filter').value = today;
        document.getElementById('end-date-filter').value = today;
        selectedChannelIds = [10, 11];
        localStorage.setItem('dashboard_default_channels', JSON.stringify(selectedChannelIds));
        updateChannelSelectButton();
        updateChannelsCheckboxes();
        document.getElementById('zone-filter').value = '';
        document.getElementById('refresh-interval').value = '30';
        currentRefreshSeconds = 30;
        localStorage.setItem('dashboard_refresh_interval', '30');
        updateRefreshInterval();
        loadSummary();
        loadRecentEvents();
    }

    function openMobileConfigModal() {
        cloneFiltersToModal();
        mobileConfigModal.style.display = 'block';
        mobileConfigBtn.classList.add('active');
    }

    function closeMobileConfigModal() {
        mobileConfigModal.style.display = 'none';
        mobileConfigBtn.classList.remove('active');
    }

    mobileConfigBtn.addEventListener('click', openMobileConfigModal);
    
    if (mobileConfigClose) {
        mobileConfigClose.addEventListener('click', closeMobileConfigModal);
    }
    
    if (mobileConfigCancel) {
        mobileConfigCancel.addEventListener('click', closeMobileConfigModal);
    }
    
    if (mobileConfigApply) {
        mobileConfigApply.addEventListener('click', function() {
            applyFiltersFromModal();
            closeMobileConfigModal();
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === mobileConfigModal) {
            closeMobileConfigModal();
        }
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
        // Save selection to localStorage
        localStorage.setItem('dashboard_default_channels', JSON.stringify(selectedChannelIds));
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
        const channelId = Number(channel.channel_id);
        const channelItem = document.createElement('div');
        channelItem.className = 'channel-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `channel-${channelId}`;
        checkbox.value = channelId;
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!selectedChannelIds.includes(channelId)) {
                    selectedChannelIds.push(channelId);
                }
            } else {
                selectedChannelIds = selectedChannelIds.filter(id => id !== channelId);
            }
        });

        const label = document.createElement('label');
        label.htmlFor = `channel-${channelId}`;
        label.className = 'channel-label';
        
        const address = channel.address || channel.location || '';
        const location = channel.location || '';
        const description = channel.description || `Channel ${channelId}`;
        
        label.innerHTML = `
            <span class="channel-info">
                <strong>Channel ${channelId}</strong>
                <span class="channel-details">${address}${location ? ` - ${location}` : ''}</span>
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
    console.log('=== loadSummary() called ===');
    const startDate = document.getElementById('start-date-filter').value;
    const endDate = document.getElementById('end-date-filter').value;
    const zone = document.getElementById('zone-filter').value;
    const timeIntervalElement = document.getElementById('time-interval');
    const timeInterval = timeIntervalElement ? timeIntervalElement.value : '60';

    console.log('Parameters:', {
        startDate,
        endDate,
        zone,
        timeInterval,
        selectedChannelIds,
        timeIntervalElementFound: !!timeIntervalElement
    });

    let url = `/api/summary?start_date=${startDate}&end_date=${endDate}&time_interval=${timeInterval}`;
    if (selectedChannelIds.length > 0) {
        url += `&channel_ids=${selectedChannelIds.join(',')}`;
    }
    if (zone) {
        url += `&zone_id=${zone}`;
    }

    console.log('📡 Fetching URL:', url);

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

            console.log('✅ Summary data received:', {
                time_interval: timeInterval,
                hourly_data_keys: data.hourly_data ? Object.keys(data.hourly_data) : [],
                hourly_data_count: data.hourly_data ? Object.keys(data.hourly_data).length : 0,
                hourly_data: data.hourly_data
            });

            // Update summary cards
            document.getElementById('total-enter').textContent = data.total_enter || 0;
            document.getElementById('total-exit').textContent = data.total_exit || 0;
            document.getElementById('unique-entered').textContent = data.unique_tracks_entered || 0;
            document.getElementById('unique-exited').textContent = data.unique_tracks_exited || 0;
            document.getElementById('net-count').textContent = data.net_count || 0;

            // Update charts - sử dụng số người (unique tracks) thay vì số lượt
            if (data.hourly_data && Object.keys(data.hourly_data).length > 0) {
                console.log('📊 Updating hourly chart with', Object.keys(data.hourly_data).length, 'data points');
                updateHourlyChart(data.hourly_data, startDate, endDate);
            } else {
                console.warn('⚠️ No hourly_data or empty hourly_data:', data.hourly_data);
            }
            updateSummaryChart(data.unique_tracks_entered || 0, data.unique_tracks_exited || 0);

            // If summary reveals new channels, reload available options while preserving selection
            if (Array.isArray(data.available_channels)) {
                const summaryChannels = data.available_channels.map(id => Number(id));
                const knownChannels = allChannels.map(channel => Number(channel.channel_id));
                const hasNewChannel = summaryChannels.some(id => !knownChannels.includes(id));
                if (hasNewChannel) {
                    loadAvailableOptions(true);
                }
            }
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
                        <td>${event.track_id || 'N/A'}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="no-data">Không có sự kiện nào gần đây.</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading recent events:', error);
            console.error('URL:', url);
            document.getElementById('events-tbody').innerHTML = 
                '<tr><td colspan="5" class="error">Lỗi tải sự kiện: ' + error.message + '</td></tr>';
        });
}

function updateHourlyChart(hourlyData, startDate, endDate) {
    const ctx = document.getElementById('hourly-chart').getContext('2d');
    
    // Get selected interval to understand the data format
    const intervalSelect = document.getElementById('time-interval');
    const interval = intervalSelect ? parseInt(intervalSelect.value) : 60;
    
    console.log('updateHourlyChart called with interval:', interval, 'minutes');
    
    // Prepare data - số người ra/vào theo chu kỳ
    // Sort time slots properly (HH:MM format)
    const hours = Object.keys(hourlyData).sort((a, b) => {
        // Convert "HH:MM" to minutes for proper sorting
        const timeA = a.split(':').map(Number);
        const timeB = b.split(':').map(Number);
        const minutesA = timeA[0] * 60 + (timeA[1] || 0);
        const minutesB = timeB[0] * 60 + (timeB[1] || 0);
        return minutesA - minutesB;
    });
    
    // Map data according to sorted hours
    const enterData = hours.map(h => hourlyData[h].enter || 0);
    const exitData = hours.map(h => hourlyData[h].exit || 0);
    
    console.log('Chart will display', hours.length, 'time slots:', {
        first: hours[0],
        last: hours[hours.length - 1],
        interval: interval + ' minutes',
        sampleLabels: hours.slice(0, 5)
    });
    
    console.log('Chart data:', { 
        hours, 
        enterData, 
        exitData, 
        hourlyData,
        hoursCount: hours.length,
        enterDataSum: enterData.reduce((a, b) => a + b, 0),
        exitDataSum: exitData.reduce((a, b) => a + b, 0)
    });

    // Destroy existing chart if it exists
    if (hourlyChart) {
        console.log('Destroying existing chart');
        hourlyChart.destroy();
        hourlyChart = null;
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
        // interval already retrieved above
        let intervalText = '';
        if (interval === 15) {
            intervalText = ' (15 phút)';
        } else if (interval === 30) {
            intervalText = ' (30 phút)';
        } else {
            intervalText = ' (1 giờ)';
        }
        chartTitleElement.textContent = `Số người ra/vào${intervalText}${dateRangeText}`;
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
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Số người ra',
                    data: exitData,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 5
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
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0,
                        // Auto-adjust step size based on interval and data density
                        maxTicksLimit: interval === 15 ? 24 : interval === 30 ? 12 : 8,
                        callback: function(value, index, ticks) {
                            // Show all labels for 15/30 min intervals, skip some for 60 min if too many
                            if (interval === 60 && ticks.length > 12) {
                                // Show every 2nd label for hourly data if too dense
                                return index % 2 === 0 ? this.getLabelForValue(value) : '';
                            }
                            return this.getLabelForValue(value);
                        }
                    }
                }
            },
            animation: {
                duration: 500
            }
        }
    });
    
    console.log('Chart created successfully with', hours.length, 'data points for interval', interval, 'minutes');
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

