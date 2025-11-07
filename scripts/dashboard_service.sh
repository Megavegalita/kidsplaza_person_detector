#!/usr/bin/env bash
# Dashboard Service Manager

DASHBOARD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DASHBOARD_SCRIPT="$DASHBOARD_DIR/web_dashboard/app.py"
LOG_DIR="$DASHBOARD_DIR/logs"
PORT=8000

case "$1" in
    start)
        echo "🚀 Starting Counter Events Dashboard..."
        
        # Check if already running
        if pgrep -f "web_dashboard/app.py" > /dev/null; then
            echo "⚠️  Dashboard đã đang chạy"
            ps aux | grep "web_dashboard/app.py" | grep -v grep
            exit 1
        fi
        
        # Start dashboard
        cd "$DASHBOARD_DIR"
        source venv/bin/activate
        nohup python "$DASHBOARD_SCRIPT" > "$LOG_DIR/dashboard_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
        
        sleep 3
        
        if pgrep -f "web_dashboard/app.py" > /dev/null; then
            echo "✅ Dashboard đã khởi động thành công"
            echo "🌐 URL nội bộ: http://localhost:$PORT"
            echo "🌐 URL mạng: http://192.168.0.243:$PORT"
            echo "📝 Log: $LOG_DIR/dashboard_*.log"
            ps aux | grep "web_dashboard/app.py" | grep -v grep | awk '{print "   PID:", $2}'
        else
            echo "❌ Không thể khởi động dashboard"
            exit 1
        fi
        ;;
    
    stop)
        echo "🛑 Stopping Counter Events Dashboard..."
        pkill -f "web_dashboard/app.py"
        sleep 2
        if pgrep -f "web_dashboard/app.py" > /dev/null; then
            echo "⚠️  Vẫn còn process đang chạy, force kill..."
            pkill -9 -f "web_dashboard/app.py"
        fi
        echo "✅ Dashboard đã dừng"
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if pgrep -f "web_dashboard/app.py" > /dev/null; then
            echo "✅ Dashboard đang chạy"
            echo "🌐 URL nội bộ: http://localhost:$PORT"
            echo "🌐 URL mạng: http://192.168.0.243:$PORT"
            ps aux | grep "web_dashboard/app.py" | grep -v grep
            echo ""
            # Test API
            if curl -s http://localhost:$PORT/api/summary > /dev/null 2>&1; then
                echo "✅ API đang phản hồi"
            else
                echo "⚠️  API không phản hồi"
            fi
        else
            echo "❌ Dashboard không chạy"
        fi
        ;;
    
    logs)
        if [ -n "$2" ]; then
            tail -f "$LOG_DIR/dashboard_$2.log" 2>/dev/null || echo "Log file không tồn tại"
        else
            ls -t "$LOG_DIR"/dashboard_*.log 2>/dev/null | head -1 | xargs tail -f
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Khởi động dashboard"
        echo "  stop    - Dừng dashboard"
        echo "  restart - Khởi động lại dashboard"
        echo "  status  - Kiểm tra trạng thái"
        echo "  logs    - Xem log (real-time)"
        exit 1
        ;;
esac

