import argparse
from aiohttp import web
import aiofiles
from datetime import datetime

HOST = None
PORT = 8080

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
filename = f"received_{timestamp}.csv"

voice_lines = {}
sb_placeholders = ['speaker', '']

with open('misc/VoiceLines.csv', 'r', encoding='utf8') as f:
    for line in f.readlines():
        els = line.split(' ')
        voice_lines[els[0]] = els[2]

async def process(request):
    try:
        text_data = await request.text()
        sb = text_data.split(';')[-1]
        if sb not in sb_placeholders:
            speaker = voice_lines.get(sb, sb)
            text_data = text_data.replace(sb, speaker)

        text_data += f';{sb}'

        async with aiofiles.open(filename, mode='a+') as f:
            await f.write(f'{text_data}\n')
        
        return web.Response(text="ok", status=200)
    
    except Exception as e:
        print(f'Error: {e}')
        return web.Response(text="ok", status=500)


async def create_app():
    app = web.Application()
    app.router.add_post('/', process)
    return app


def parse_args():
    parser = argparse.ArgumentParser(description="Simple game logging")
    parser.add_argument("--host", type=str, default=HOST, help="Host address (default: all interfaces)")
    parser.add_argument("--port", type=int, default=PORT, help="Port number (default: 8080)")
    args = parser.parse_args()

    if args.port < 1 or args.port > 65535:
        parser.error("Port must be between 1 and 65535")
    
    return args.host, args.port


def run_server():
    web.run_app(create_app(), host=HOST, port=PORT)


if __name__ == '__main__':
    try:
        HOST, PORT = parse_args()
        print(f"Data will be saved to {filename}\nServer starting on http://{HOST or '0.0.0.0'}:{PORT}")
        run_server()
    except Exception as e:
        print(e)
