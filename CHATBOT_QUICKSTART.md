# 🚀 Medical Chatbot - Quick Start Guide

Get the chatbot up and running in 5 minutes!

## Prerequisites

- Python 3.12+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Step 1: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install the project
pip install -e .
```

## Step 2: Configure Environment

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-key-here
DEBUG=1
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
```

**Minimum required:**
```env
OPENAI_API_KEY=sk-...
```

## Step 3: Run Migrations

```bash
python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: chatbot, ...
Running migrations:
  Applying chatbot.0001_initial... OK
```

## Step 4: Start the Server

```bash
python manage.py runserver
```

## Step 5: Open the Chatbot

Open your browser to:

👉 **http://localhost:8000/chatbot/**

You should see a beautiful purple-gradient chat interface!

## 🎉 You're Done!

Try asking:
- "What is diabetes?"
- "Explain how vaccines work"
- Upload an image and ask "What's in this image?"

## 🧪 Run Tests (Optional)

```bash
python manage.py test chatbot
```

Expected: **All tests pass** ✅

## 📖 Learn More

- Full documentation: `CHATBOT_README.md`
- Implementation details: `CHATBOT_IMPLEMENTATION_SUMMARY.md`
- API reference: See docs in `CHATBOT_README.md`

## 🐛 Troubleshooting

### Issue: "No module named 'openai'"
**Solution:** `pip install openai>=1.40`

### Issue: "OPENAI_API_KEY not set"
**Solution:** Check your `.env` file has `OPENAI_API_KEY=sk-...`

### Issue: "pdfminer.six not installed"
**Solution:** `pip install pdfminer.six>=20231228`

### Issue: "Pillow not available"
**Solution:** `pip install Pillow>=10.4`

### Issue: Migrations not applied
**Solution:** `python manage.py migrate chatbot`

## 🔑 Environment Variables Explained

### Required
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional (have sensible defaults)
- `OPENAI_DEFAULT_MODEL` - Default: `gpt-4o-mini`
- `OPENAI_TIMEOUT` - Default: `15` seconds
- `CHAT_MAX_HISTORY_TURNS` - Default: `6` messages
- `DEBUG` - Default: `False` (set to `1` for development)

## 📋 Quick Commands Reference

```bash
# Run server
python manage.py runserver

# Run tests
python manage.py test chatbot

# Create admin user
python manage.py createsuperuser

# Access admin
# http://localhost:8000/admin/

# Collect static files (for production)
python manage.py collectstatic

# Run with different settings
python manage.py runserver --settings=config.settings.dev
```

## 🎯 Using the API

### cURL Example
```bash
curl -X POST http://localhost:8000/chatbot/api/chat/ \
  -F "message=What is hypertension?" \
  -F "model=gpt-4o-mini"
```

### Python Example
```python
import httpx
import json

async def chat(message: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/chatbot/api/chat/",
            data={"message": message}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "delta" in data:
                        print(data["delta"], end="", flush=True)
```

### JavaScript Example
```javascript
const formData = new FormData();
formData.append('message', 'What is diabetes?');

const response = await fetch('/chatbot/api/chat/', {
  method: 'POST',
  body: formData,
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  // Process SSE events...
  console.log(chunk);
}
```

## 🎨 Customization Quick Tips

### Change Default Model
In `.env`:
```env
OPENAI_DEFAULT_MODEL=gpt-4o
```

### Change Conversation History Limit
In `.env`:
```env
CHAT_MAX_HISTORY_TURNS=10
```

### Add Custom System Prompt
Edit `chatbot/services/message_builder.py`:
```python
MEDICAL_SYSTEM_PROMPT = "Your custom prompt here..."
```

### Change UI Theme
Edit `chatbot/templates/chatbot/index.html` - look for gradient colors:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

## 📊 Check Your Setup

Run this Python script to verify everything:

```python
import os
import sys

checks = {
    "Django": False,
    "OpenAI SDK": False,
    "Pillow": False,
    "pdfminer": False,
    "API Key": False,
}

try:
    import django
    checks["Django"] = True
except ImportError:
    pass

try:
    import openai
    checks["OpenAI SDK"] = True
except ImportError:
    pass

try:
    import PIL
    checks["Pillow"] = True
except ImportError:
    pass

try:
    import pdfminer
    checks["pdfminer"] = True
except ImportError:
    pass

# Check for .env file
if os.path.exists(".env"):
    with open(".env") as f:
        if "OPENAI_API_KEY" in f.read():
            checks["API Key"] = True

print("\n🔍 Setup Check Results:\n")
for name, status in checks.items():
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")

if all(checks.values()):
    print("\n🎉 All checks passed! You're ready to go!")
else:
    print("\n⚠️  Some checks failed. See troubleshooting above.")
```

Save as `check_setup.py` and run:
```bash
python check_setup.py
```

## 🚀 Production Deployment

### Quick Production Checklist

```bash
# 1. Set production environment variables
export DEBUG=0
export DJANGO_SECRET_KEY=your-very-long-random-secret-key
export OPENAI_API_KEY=sk-...
export DATABASE_URL=postgresql://user:pass@host/db
export ALLOWED_HOSTS=yourdomain.com

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run migrations
python manage.py migrate

# 4. Start with gunicorn
gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

### Using Docker (if available)

```dockerfile
# Example Dockerfile snippet
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 💡 Pro Tips

1. **Use gpt-4o-mini for development** - It's fast and cheap
2. **Enable conversation history** - Better context, better responses
3. **Monitor your OpenAI usage** - Check the OpenAI dashboard regularly
4. **Test with images** - Upload medical diagrams, charts, etc.
5. **Test with PDFs** - Upload research papers, reports

## 🎓 Next Steps

Once you have the basic setup working:

1. 📖 Read the full documentation: `CHATBOT_README.md`
2. 🧪 Explore the tests: `chatbot/tests/`
3. 🎨 Customize the UI: `chatbot/templates/chatbot/index.html`
4. 🔧 Adjust settings: `config/settings/base.py`
5. 📊 Try the admin interface: `/admin/`

## 🤝 Need Help?

1. Check `CHATBOT_README.md` - Comprehensive documentation
2. Check `CHATBOT_IMPLEMENTATION_SUMMARY.md` - Technical details
3. Review tests in `chatbot/tests/` - Working examples
4. Check Django logs - Usually shows the error clearly

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] `.env` file created with API key
- [ ] Migrations applied
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000/chatbot/
- [ ] Can send a test message
- [ ] Response streams in real-time
- [ ] Tests pass

If all checked ✅ - **You're all set!** 🎉

---

**Quick Reference URLs:**
- UI: http://localhost:8000/chatbot/
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/chatbot/api/chat/
- Health: http://localhost:8000/health
- API Docs: http://localhost:8000/api/docs/
