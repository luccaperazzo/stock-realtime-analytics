-- MySQL Database Schema for Stock Analytics

-- Create database
CREATE DATABASE IF NOT EXISTS stock_analytics;
USE stock_analytics;

-- Tabla de agregados diarios
CREATE TABLE IF NOT EXISTS daily_aggregates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    avg_price DECIMAL(10, 2),
    total_volume BIGINT,
    avg_volume BIGINT,
    price_volatility DECIMAL(10, 4),
    daily_change_pct DECIMAL(8, 4),
    sma_20 DECIMAL(10, 2),
    rsi DECIMAL(6, 2),
    num_trades INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date (symbol, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de resumen semanal
CREATE TABLE IF NOT EXISTS weekly_aggregates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    avg_close_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    total_volume BIGINT,
    weekly_change_pct DECIMAL(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol_week (symbol, week_start_date),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de métricas de performance
CREATE TABLE IF NOT EXISTS stock_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    period VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    period_date DATE NOT NULL,
    return_pct DECIMAL(8, 4),
    volatility DECIMAL(8, 4),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_period (symbol, period),
    INDEX idx_period_date (period_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de alertas enviadas (histórico)
CREATE TABLE IF NOT EXISTS alert_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'price_change', 'volume_spike', etc.
    trigger_value DECIMAL(10, 2),
    threshold_value DECIMAL(10, 2),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar datos de ejemplo (opcional)
-- INSERT INTO daily_aggregates (symbol, date, open_price, close_price, high_price, low_price, avg_price, total_volume, avg_volume, price_volatility, daily_change_pct, num_trades)
-- VALUES ('AAPL', CURDATE(), 150.00, 152.50, 153.00, 149.50, 151.25, 50000000, 500000, 1.25, 1.67, 100);
