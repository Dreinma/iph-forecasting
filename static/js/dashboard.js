let modelMetricsCache = null;
let modelMetricsCacheTime = 0;

class ForecastingDashboard {
    constructor() {
        this.isLoading = false;
        this.currentData = null;
        this.currentForecast = null;
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Forecasting Dashboard...');
        this.bindEvents();
        this.loadDashboardData();
    }
    
    bindEvents() {
        // Auto refresh every 5 minutes
        setInterval(() => {
            if (!this.isLoading) {
                this.loadDashboardData();
            }
        }, 300000);
        
        // Manual refresh button
        const refreshBtn = safeGetElement('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDashboardData());
        }
    }
    
    async loadDashboardData() {
        if (this.isLoading) {
            console.log('⏳ Dashboard already loading, skipping...');
            return;
        }
        
        this.isLoading = true;
        console.log('🔄 Loading dashboard data...');
        
        try {
            // Show loading indicators
            this.showLoadingIndicators();
            
            // Load components in parallel where possible
            const promises = [
                this.loadHistoricalChart(),
                this.loadModelPerformance(),
                this.loadForecastTable(),
                loadStatisticalAlerts() // Use the fixed function
            ];
            
            await Promise.allSettled(promises);
            
            console.log('✅ Dashboard data loaded successfully');
            
        } catch (error) {
            console.error('❌ Error loading dashboard:', error);
            this.showErrorState();
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicators();
        }
    }
    
    showLoadingIndicators() {
        const indicators = [
            'historicalChart',
            'modelPerformanceGrid',
            'forecastTable'
        ];
        
        indicators.forEach(id => {
            const element = safeGetElement(id);
            if (element) {
                element.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2 text-muted">Memuat data...</p>
                    </div>
                `;
            }
        });
    }
    
    hideLoadingIndicators() {
        // Loading indicators will be replaced by actual content
        console.log('🎯 Loading indicators hidden');
    }
    
    showErrorState() {
        const errorHtml = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Gagal memuat data dashboard. 
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="dashboard.loadDashboardData()">
                    Coba Lagi
                </button>
            </div>
        `;
        
        const mainContainer = safeGetElement('dashboardMainContent');
        if (mainContainer) {
            mainContainer.innerHTML = errorHtml;
        }
    }
    
    async loadHistoricalChart() {
        try {
            console.log('📊 Loading historical chart...');
            
            const response = await fetch('/api/dashboard/historical-chart');
            const data = await response.json();
            
            const chartContainer = safeGetElement('historicalChart');
            if (!chartContainer) {
                console.warn('⚠️ Historical chart container not found');
                return;
            }
            
            if (data.success && data.chart) {
                // Clear container
                chartContainer.innerHTML = '';
                
                // Create Plotly chart
                Plotly.newPlot('historicalChart', data.chart.data, data.chart.layout, {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
                });
                
                console.log('✅ Historical chart loaded');
            } else {
                chartContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-chart-line me-2"></i>
                        ${data.message || 'Tidak ada data historis'}
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('❌ Error loading historical chart:', error);
            
            const chartContainer = safeGetElement('historicalChart');
            if (chartContainer) {
                chartContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error memuat chart: ${error.message}
                    </div>
                `;
            }
        }
    }
    
    async loadModelPerformance() {
        try {
            console.log('🎯 Loading model performance...');
            
            const response = await fetch('/api/dashboard/model-performance');
            const data = await response.json();
            
            const performanceContainer = safeGetElement('modelPerformanceGrid');
            if (!performanceContainer) {
                console.warn('⚠️ Model performance container not found');
                return;
            }
            
            if (data.success && data.models) {
                const filteredModels = data.models.filter(m => m.name !== 'Ensemble');
                let performanceHtml = '';
                
                data.models.forEach(model => {
                    const statusClass = model.status === 'Best' ? 'success' : 
                                       model.status === 'Good' ? 'info' : 'secondary';
                    
                    performanceHtml += `
                        <div class="col-md-6 col-lg-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <h6 class="card-title mb-0">${model.name}</h6>
                                        <span class="badge bg-${statusClass}">${model.status}</span>
                                    </div>
                                    <div class="row g-2 text-center">
                                        <div class="col-6">
                                            <small class="text-muted d-block">MAE</small>
                                            <strong>${model.mae.toFixed(4)}</strong>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted d-block">RMSE</small>
                                            <strong>${model.rmse.toFixed(4)}</strong>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted d-block">R²</small>
                                            <strong>${model.r2.toFixed(3)}</strong>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted d-block">MAPE</small>
                                            <strong>${model.mape.toFixed(2)}%</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                performanceContainer.innerHTML = performanceHtml;
                console.log('✅ Model performance loaded');
                
            } else {
                performanceContainer.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-warning">
                            <i class="fas fa-tachometer-alt me-2"></i>
                            ${data.message || 'Tidak ada data performa model'}
                        </div>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('❌ Error loading model performance:', error);
            
            const performanceContainer = safeGetElement('modelPerformanceGrid');
            if (performanceContainer) {
                performanceContainer.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Error memuat performa model: ${error.message}
                        </div>
                    </div>
                `;
            }
        }
    }
    
    async loadForecastTable() {
        try {
            console.log('📋 Loading forecast table...');
            
            const response = await fetch('/api/dashboard/forecast-table');
            const data = await response.json();
            
            const tableContainer = safeGetElement('forecastTable');
            if (!tableContainer) {
                console.warn('⚠️ Forecast table container not found');
                return;
            }
            
            if (data.success && data.forecasts) {
                let tableHtml = `
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Minggu</th>
                                    <th>Tanggal</th>
                                    <th>Prediksi IPH</th>
                                    <th>Batas Bawah</th>
                                    <th>Batas Atas</th>
                                    <th>Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.forecasts.forEach((forecast, index) => {
                    const confidenceClass = forecast.confidence > 80 ? 'text-success' : 
                                           forecast.confidence > 60 ? 'text-warning' : 'text-danger';
                    
                    tableHtml += `
                        <tr>
                            <td><strong>W${index + 1}</strong></td>
                            <td>${forecast.date}</td>
                            <td><strong>${forecast.value.toFixed(3)}</strong></td>
                            <td>${forecast.lower_bound.toFixed(3)}</td>
                            <td>${forecast.upper_bound.toFixed(3)}</td>
                            <td><span class="${confidenceClass}">${forecast.confidence.toFixed(1)}%</span></td>
                        </tr>
                    `;
                });
                
                tableHtml += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                tableContainer.innerHTML = tableHtml;
                console.log('✅ Forecast table loaded');
                
            } else {
                tableContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-table me-2"></i>
                        ${data.message || 'Tidak ada data forecast'}
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('❌ Error loading forecast table:', error);
            
            const tableContainer = safeGetElement('forecastTable');
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error memuat tabel forecast: ${error.message}
                    </div>
                `;
            }
        }
    }
}

async function validateData() {
    showLoading('Validating data quality...');
    try {
        const response = await fetch('/api/validate-data');
        const result = await response.json();
        
        if (result.success) {
            showAlert(`Data validation complete. Quality score: ${result.quality_score}%`, 'info');
            updateDataQualityIndicators(result);
        }
    } catch (error) {
        showAlert('Validation failed: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}


function safeGetElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`⚠️ Element with id '${id}' not found`);
        return null;
    }
    return element;
}

async function loadStatisticalAlerts() {
    try {
        console.log('🔔 Loading statistical alerts...');
        
        // Safe element access
        const alertsContainer = safeGetElement('statisticalAlerts');
        if (!alertsContainer) {
            console.warn('⚠️ Statistical alerts container not found, skipping...');
            return;
        }
        
        const response = await fetch('/api/alerts/statistical');
        const data = await response.json();
        
        if (data.success && data.alerts) {
            let alertsHtml = '';
            
            data.alerts.forEach(alert => {
                const alertClass = alert.severity === 'high' ? 'alert-danger' : 
                                 alert.severity === 'medium' ? 'alert-warning' : 'alert-info';
                
                alertsHtml += `
                    <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>${alert.title}</strong><br>
                        ${alert.message}
                        <small class="d-block mt-1 text-muted">${alert.timestamp}</small>
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
            });
            
            alertsContainer.innerHTML = alertsHtml || '<p class="text-muted">Tidak ada peringatan statistik</p>';
        } else {
            alertsContainer.innerHTML = '<p class="text-muted">Tidak ada data peringatan</p>';
        }
        
        console.log('✅ Statistical alerts loaded');
        
    } catch (error) {
        console.error('❌ Error loading statistical alerts:', error);
        
        const alertsContainer = safeGetElement('statisticalAlerts');
        if (alertsContainer) {
            alertsContainer.innerHTML = '<p class="text-muted">Error memuat peringatan</p>';
        }
    }
}

function updateDataControlMetrics() {
    // Update semua metrics di panel
    // Call API untuk get latest status
    fetch('/api/data-control-status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('dataHealthScore').textContent = data.health_score + '%';
            document.getElementById('modelStatus').textContent = data.model_status;
            document.getElementById('processingSpeed').textContent = data.processing_speed;
            document.getElementById('forecastAccuracy').textContent = data.forecast_accuracy + '%';
        });
}

let dashboard;

document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new ForecastingDashboard();
    
    console.log('🎯 DOM Content Loaded - Initializing Dashboard');
    dashboard = new ForecastingDashboard();

    if (document.getElementById('forecastChart')) {
        dashboard.loadForecastChart();
    }
    
    if (document.getElementById('modelComparisonChart')) {
        dashboard.loadModelComparisonChart();
    }
});

window.ForecastingDashboard = ForecastingDashboard;