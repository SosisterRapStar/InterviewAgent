import asyncio
import sys
from typing import Optional


class LoadingSpinner:
    
    def __init__(self, text: str = ""):
        self.text = text
        self._task: Optional[asyncio.Task] = None
        
    async def _animate(self):
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

        idx = 0
        
        while True:
            frame = frames[idx % len(frames)]
            sys.stderr.write(f'\r{frame} {self.text}')
            sys.stderr.flush()
            await asyncio.sleep(0.1)
            idx += 1
    
    async def __aenter__(self):
        self._task = asyncio.create_task(self._animate())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            # Очищаем строку
            sys.stderr.write('\r' + ' ' * (len(self.text) + 5) + '\r')
            sys.stderr.flush()
        
        return False


def get_spinner() -> LoadingSpinner:
    return LoadingSpinner()


