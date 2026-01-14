# 根目录 Makefile - 统一启动多服务开发环境
# 使用: make help 查看所有命令

.PHONY: help db java crag frontend start stop status logs clean all

# 默认目标
help:
	@echo "使用方法:"
	@echo "  make all      - 启动所有服务 (DB + Java + CRAG + Frontend)"
	@echo "  make start    - 启动所有后端服务 (DB + Java + CRAG)"
	@echo "  make stop     - 停止所有服务"
	@echo "  make status   - 查看服务状态"
	@echo "  make db       - 仅启动 PostgreSQL"
	@echo "  make java     - 仅启动 Java 后端"
	@echo "  make crag     - 仅启动 CRAG Python API"
	@echo "  make frontend - 仅启动前端 (后台)"
	@echo "  make logs     - 查看服务日志"
	@echo "  make clean    - 清理日志和临时文件"

# 启动 PostgreSQL
db:
	@echo "Starting PostgreSQL..."
	cd AITripPlanner && docker-compose up -d
	@echo "PostgreSQL running on port 5434"

# 启动 Java 后端 (后台)
java:
	@echo "Starting Java backend..."
	cd AITripPlanner && ./gradlew bootRun > /tmp/java-backend.log 2>&1 &
	@sleep 8 && lsof -i :8080 | grep LISTEN && echo "Java running on port 8080"

# 启动 CRAG Python API (后台)
crag:
	@echo "Starting CRAG Python API..."
	cd CRAG-travelplanner && mkdir -p logs && nohup uvicorn seekdb_agent.api.main:app --reload --port 8000 > logs/crag-api.log 2>&1 &
	@sleep 3 && lsof -i :8000 | grep LISTEN && echo "CRAG running on port 8000"

# 启动前端 (后台)
frontend:
	@echo "Starting Frontend..."
	cd trip-mate && nohup npm start > /tmp/frontend.log 2>&1 &
	@sleep 5 && lsof -i :3000 | grep LISTEN && echo "Frontend running on port 3000"

# 一键启动所有后端服务
start: db
	@sleep 3
	@make java
	@sleep 5
	@make crag
	@echo "\n=== All backend services started ==="
	@make status

# 一键启动所有服务 (后端 + 前端)
all: start
	@make frontend
	@echo "\n=== All services started ==="
	@make status

# 停止所有服务
stop:
	@echo "Stopping services..."
	-pkill -f "gradlew bootRun" 2>/dev/null
	-pkill -f "uvicorn.*8000" 2>/dev/null
	-pkill -f "react-scripts start" 2>/dev/null
	-kill -9 $$(lsof -t -i :8080) 2>/dev/null
	-kill -9 $$(lsof -t -i :8000) 2>/dev/null
	-kill -9 $$(lsof -t -i :3000) 2>/dev/null
	cd AITripPlanner && docker-compose down
	@echo "All services stopped"

# 查看服务状态
status:
	@echo "=== Service Status ==="
	@printf "PostgreSQL (5434): " && (lsof -i :5434 | grep LISTEN > /dev/null && echo "✅ Running" || echo "❌ Stopped")
	@printf "Java (8080):       " && (lsof -i :8080 | grep LISTEN > /dev/null && echo "✅ Running" || echo "❌ Stopped")
	@printf "CRAG (8000):       " && (lsof -i :8000 | grep LISTEN > /dev/null && echo "✅ Running" || echo "❌ Stopped")
	@printf "Frontend (3000):   " && (lsof -i :3000 | grep LISTEN > /dev/null && echo "✅ Running" || echo "❌ Stopped")

# 查看日志
logs:
	@echo "=== Java Backend Log ===" && tail -20 /tmp/java-backend.log 2>/dev/null || echo "No log"
	@echo "\n=== CRAG API Log ===" && tail -20 CRAG-travelplanner/logs/crag-api.log 2>/dev/null || echo "No log"
	@echo "\n=== Frontend Log ===" && tail -20 /tmp/frontend.log 2>/dev/null || echo "No log"

# 清理
clean:
	rm -f /tmp/java-backend.log CRAG-travelplanner/logs/crag-api.log /tmp/frontend.log
	cd CRAG-travelplanner && make clean
