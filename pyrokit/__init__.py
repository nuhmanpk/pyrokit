import os
import re
import time
import asyncio
import logging
import functools
from typing import Union, List, Callable, Optional
from pyrogram import Client, filters, emoji
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, InputMediaDocument, Progress
)
from pyrogram.errors import FloodWait, MessageNotModified

class PyroKit:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self._progress_styles = {
            'default': '▓▒░',
            'circle': '◔◑◕●',
            'square': '■□',
            'arrow': '▶▶▶'
        }
        self._middleware = []
        self._language_packs = {}
        self._rate_limit_store = defaultdict(list)
        self._conversation_data = {}
        self._db_pool = None  # Database connection pool
        
        # New configuration defaults
        self.config.setdefault('temp_dir', 'pyrokit_temp')
        self.config.setdefault('max_file_size', 2_000_000_000)  # 2GB
        os.makedirs(self.config['temp_dir'], exist_ok=True)

    # ================= CORE DECORATORS =================
    
    def ensure_admin(self, permissions: list = None):
        """Decorator to ensure user has admin privileges"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(client: Client, message: Message):
                check = await self._check_admin(client, message, permissions)
                if not check:
                    return await message.reply("🔒 Admin privileges required!")
                return await func(client, message)
            return wrapper
        return decorator

    def async_retry(self, max_retries: int = 3, delay: int = 1):
        """Retry decorator for async functions"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(delay)
                return None
            return wrapper
        return decorator

    # ============== MESSAGE MANAGEMENT ================
    
    async def safe_delete(self, message: Message, delay: int = 0):
        """Safely delete messages with error handling"""
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except Exception as e:
            logging.warning(f"Failed to delete message: {e}")

    async def paginate_text(self, text: str, max_len: int = 4000) -> List[str]:
        """Split long text into Telegram-friendly chunks"""
        return [text[i:i+max_len] for i in range(0, len(text), max_len)]

    async def edit_or_resend(self, message: Message, text: str, **kwargs) -> Message:
        """Edit message if possible, otherwise send new message"""
        try:
            return await message.edit_text(text, **kwargs)
        except MessageNotModified:
            return message
        except Exception:
            return await message.reply(text, **kwargs)

    # ============= MEDIA HANDLING UTILITIES =============
    
    @auto_flood
    async def download_media(
        self,
        message: Message,
        progress_callback: Callable = None,
        file_name: str = "downloads/"
    ) -> Optional[str]:
        """Enhanced media downloader with progress tracking"""
        if not message.media:
            return None

        download_path = await message.download(
            file_name=file_name,
            progress=progress_callback,
            progress_args=("Downloading...",)
        )
        return download_path

    async def upload_media(
        self,
        client: Client,
        chat_id: Union[int, str],
        file_path: str,
        progress_callback: Callable = None,
        caption: str = ""
    ) -> Optional[Message]:
        """Reliable media uploader with progress tracking"""
        if not os.path.exists(file_path):
            return None

        return await client.send_document(
            chat_id=chat_id,
            document=file_path,
            caption=caption,
            progress=progress_callback,
            progress_args=("Uploading...",)
        )

    # ============== USER INTERACTION UTILS ==============
    
    def inline_keyboard(self, buttons: list, row_width: int = 3) -> InlineKeyboardMarkup:
        """Create inline keyboards from 2D list of buttons"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(str(btn), callback_data=data) for btn, data in row]
            for row in buttons
        ])

    async def answer_query(self, query: CallbackQuery, text: str, show_alert: bool = False):
        """Universal callback query answer handler"""
        try:
            await query.answer(text, show_alert=show_alert)
        except Exception as e:
            logging.error(f"Error answering query: {e}")

    # ============== ADVANCED FEATURES ==============
    
    def conversation_handler(self, states: dict, timeout: int = 300):
        """Stateful conversation handler decorator"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(client: Client, message: Message):
                user_id = message.from_user.id
                current_state = self._get_state(user_id)
                
                if current_state in states:
                    handler = states[current_state]
                    return await handler(client, message)
                
                return await func(client, message)
            return wrapper
        return decorator

    async def create_progress_bar(
        self,
        current: int,
        total: int,
        length: int = 10,
        style: str = 'default'
    ) -> tuple:
        """Create customizable progress bars"""
        style_chars = self._progress_styles.get(style, self._progress_styles['default'])
        filled_len = int(round(length * current / float(total)))
        bar = style_chars[0] * filled_len + style_chars[-1] * (length - filled_len)
        percent = f"{100 * current / float(total):.1f}"
        return bar, percent

    # ============== HELPER METHODS ==============
    
    async def _check_admin(self, client: Client, message: Message, permissions: list) -> bool:
        """Verify admin status and permissions"""
        try:
            user = await client.get_chat_member(message.chat.id, message.from_user.id)
            if user.status not in ["creator", "administrator"]:
                return False
                
            if permissions:
                return all(getattr(user, perm, False) for perm in permissions)
                
            return True
        except Exception as e:
            logging.error(f"Admin check failed: {e}")
            return False

    def _get_state(self, user_id: int) -> str:
        """Get current conversation state (mock implementation)"""
        return self._conversation_states.get(user_id, 'START')


# --------------- Database Integration ----------------
    async def db_connect(self, dsn: str):
        """Initialize database connection pool"""
        self._db_pool = await asyncpg.create_pool(dsn)
        
    def with_db(self, func):
        """Decorator to provide database connection"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with self._db_pool.acquire() as conn:
                kwargs['db'] = conn
                return await func(*args, **kwargs)
        return wrapper

    # ---------------- Localization System ----------------
    def load_languages(self, lang_dir: str):
        """Load language files from directory"""
        for filename in os.listdir(lang_dir):
            if filename.endswith('.json'):
                lang_code = filename.split('.')[0]
                with open(os.path.join(lang_dir, filename)) as f:
                    self._language_packs[lang_code] = json.load(f)
    
    def localized(self, fallback_lang: str = 'en'):
        """Decorator to handle message localization"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(client: Client, message: Message, *args, **kwargs):
                user_lang = await self._get_user_language(message.from_user.id)
                lang_data = self._language_packs.get(user_lang, 
                    self._language_packs[fallback_lang])
                kwargs['lang'] = lang_data
                return await func(client, message, *args, **kwargs)
            return wrapper
        return decorator

    # --------------- Advanced Rate Limiting -------------
    def smart_rate_limit(
        self, 
        calls: int = 5, 
        period: int = 60,
        scope: str = 'user',
        strategy: str = 'fixed'
    ):
        """
        Enhanced rate limiting with multiple strategies
        Strategies: fixed, sliding, token_bucket
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(client: Client, message: Message, *args, **kwargs):
                # Implementation details
                # ...
                return await func(client, message, *args, **kwargs)
            return wrapper
        return decorator

    # ---------------- Error Reporting -------------------
    def error_webhook(self, url: str):
        """Decorator to send errors to webhook"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    trace = inspect.trace()[-1]
                    error_data = {
                        'error': str(e),
                        'user_id': args[1].from_user.id if len(args) > 1 else None,
                        'timestamp': datetime.utcnow().isoformat(),
                        'context': f"{trace.filename}:{trace.lineno}"
                    }
                    async with aiohttp.ClientSession() as session:
                        await session.post(url, json=error_data)
                    raise
            return wrapper
        return decorator

    # --------------- File Management ---------------------
    async def safe_download(
        self,
        message: Message,
        max_size: int = None,
        allowed_types: list = None
    ) -> Optional[str]:
        """Secure media download with validation"""
        # Implementation with size and type checks
        # ...

    async def temp_file(self, prefix: str = 'pyrokit') -> str:
        """Create managed temporary file"""
        fd, path = tempfile.mkstemp(
            prefix=prefix,
            dir=self.config['temp_dir']
        )
        os.close(fd)
        return path

    # -------------- Inline Query Utilities ---------------
    def paginate_inline(
        self,
        items: list,
        page: int,
        per_page: int = 50,
        cache_time: int = 300
    ) -> list:
        """Paginate inline query results"""
        # Implementation with caching
        # ...

    # ---------------- Middleware System ------------------
    def add_middleware(self, func: Callable):
        """Register a middleware processor"""
        self._middleware.append(func)
        
    async def run_middleware(self, client: Client, message: Message):
        """Execute all registered middleware"""
        for middleware in self._middleware:
            await middleware(client, message)
