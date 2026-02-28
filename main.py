import asyncio
import sys
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

async def main():
    ip = get_local_ip()
    
    print("🚀 Запуск систем AlmaTrack...")
    print(f"🌐 Сайт (Админ-панель): http://{ip}:5000")
    print(f"⚙️ API Сервер: http://{ip}:8000")
    print("🤖 Бот запускается...")

    # Start API
    api_process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"
    )
    
    # Start Web
    web_process = await asyncio.create_subprocess_exec(
        sys.executable, "web/app.py"
    )
    
    # Start Bot
    bot_process = await asyncio.create_subprocess_exec(
        sys.executable, "bot/main.py"
    )

    try:
        await asyncio.gather(
            api_process.wait(),
            web_process.wait(),
            bot_process.wait(),
        )
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 Остановка систем...")
        for p in (api_process, web_process, bot_process):
            try:
                p.terminate()
            except Exception:
                pass
        
        # Wait for them to actually terminate
        await asyncio.gather(
            api_process.wait(),
            web_process.wait(),
            bot_process.wait(),
            return_exceptions=True
        )
        print("✅ Все системы остановлены.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
