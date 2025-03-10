# pyrokit

<p align="center">
  <img src="https://github.com/nuhmanpk/pyrokit/blob/main/images/logo.jpeg?raw=true" width="400" height="400" />
</p>

## Usecase

```py
API_ID = 123456           # Replace with your API_ID
API_HASH = "your_api_hash"  # Replace with your API_HASH
TOKEN = "my_bot_session"

app = Client(TOKEN, API_ID, API_HASH)

kit = PyroKit()

@app.on_message(filters.command("clean"))
@kit.ensure_admin(permissions=["can_delete_messages"])
@auto_flood
@rate_limit(5, 60)
async def clean_command(client: Client, message: Message):
    """Delete multiple messages with progress"""
    progress_msg = await message.reply("🧹 Cleaning...")
    
    async def progress(current, total):
        bar, perc = await kit.create_progress_bar(current, total)
        await kit.edit_or_resend(progress_msg, f"Cleaning: {bar} {perc}%")
    
    await client.delete_messages(
        chat_id=message.chat.id,
        message_ids=range(message.message_id-10, message.message_id),
        progress=progress
    )
    await kit.safe_delete(progress_msg)

@app.on_callback_query(filters.regex(r"^page_\d+"))
@kit.async_retry(max_retries=3)
async def handle_pagination(client: Client, query: CallbackQuery):
    """Handle inline keyboard pagination"""
    page = int(query.data.split("_")[1])
    content = f"Page {page} content"
    buttons = kit.inline_keyboard([
        [("Previous", f"page_{page-1}"), ("Next", f"page_{page+1}")]
    ])
    await kit.answer_query(query, f"Switched to page {page}")
    await kit.edit_or_resend(query.message, content, reply_markup=buttons)

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run()
```


## PyroKit Documentation
    
    A comprehensive utility toolkit for Pyrogram bot development
    
    1. Core Features:
    -----------------
    - Automated flood control
    - Rate limiting with multiple strategies
    - Admin permission verification
    - Async error retry mechanism
    - Smart message management
    
    2. Advanced Features:
    ---------------------
    - Database integration with connection pooling
    - Multi-language localization support
    - Error reporting to webhooks
    - File validation and temp file management
    - Inline query pagination
    - Middleware processing pipeline
    - Stateful conversation handlers
    
    3. Usage Examples:
    ------------------
    3.1 Database Integration:
    @app.on_message(filters.command("stats"))
    @kit.with_db
    async def show_stats(client, message, db):
        count = await db.fetchval("SELECT COUNT(*) FROM users")
        await message.reply(f"Total users: {count}")
    
    3.2 Localization:
    @app.on_message(filters.command("help"))
    @kit.localized(fallback_lang='en')
    async def help_command(client, message, lang):
        await message.reply(lang['help_text'])
    
    3.3 Error Reporting:
    @app.on_message(filters.command("danger"))
    @kit.error_webhook("https://errors.example.com")
    async def risky_command(client, message):
        # Potentially error-prone code
        ...
    
    4. Configuration:
    -----------------
    Initialize with custom config:
    config = {
        'temp_dir': 'my_temp_files',
        'max_file_size': 5_000_000_000,
        'db_dsn': 'postgres://user:pass@localhost/db'
    }
    kit = PyroKit(config)
    
    5. Best Practices:
    ------------------
    - Use @safe_delete for message cleanup
    - Always validate downloaded files
    - Use middleware for analytics tracking
    - Implement rate limiting on public endpoints
    - Store user-specific data in conversation states
