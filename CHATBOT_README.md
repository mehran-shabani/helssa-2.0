# Medical Chatbot - Django + OpenAI Integration

A complete Django chatbot application powered by OpenAI's Responses API (v1+) with support for text, images, and PDF uploads. Designed for medical Q&A with strong safety guardrails.

## 🎯 Features

- **Ultra-fast streaming responses** using Server-Sent Events (SSE)
- **Multi-modal support**: text, images (via Vision API), and PDFs
- **Medical safety guardrails**: No diagnosis, no prescriptions, always advises consulting a physician
- **Per-user conversation history** with automatic summarization
- **Smart model selection**: Default `gpt-4o-mini`, supports `gpt-4o` and `o1`
- **Async/await** throughout for optimal performance
- **Production-ready**: Rate limiting, timeouts, proper error handling
- **Full test coverage**: Unit tests for API endpoints and services

## 📁 Project Structure

```
chatbot/
├── __init__.py
├── apps.py
├── models.py                    # Conversation and Message models
├── views.py                     # Async streaming chat view
├── urls.py                      # URL routing
├── forms.py                     # Django forms
├── admin.py                     # Admin interface
├── services/
│   ├── __init__.py
│   ├── openai_client.py        # OpenAI Responses API client
│   ├── message_builder.py      # Message payload builders
│   ├── pdf_utils.py            # PDF text extraction
│   └── image_utils.py          # Image to data URL conversion
├── templates/chatbot/
│   └── index.html              # Frontend UI
├── static/chatbot/
│   └── app.css                 # Styles
├── tests/
│   ├── __init__.py
│   ├── test_api.py             # API endpoint tests
│   └── test_services.py        # Service unit tests
└── migrations/
    ├── __init__.py
    └── 0001_initial.py
```

## ⚙️ Configuration

All chatbot settings are in `config/settings/base.py`:

```python
# OpenAI Chatbot Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
OPENAI_REASONING_MODEL = os.getenv("OPENAI_REASONING_MODEL", "o1")
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "15"))
CHAT_MAX_HISTORY_TURNS = int(os.getenv("CHAT_MAX_HISTORY_TURNS", "6"))
CHAT_SUMMARY_AFTER_TURNS = int(os.getenv("CHAT_SUMMARY_AFTER_TURNS", "10"))
ALLOWED_OPENAI_MODELS = {"gpt-4o-mini", "gpt-4o", "o1"}

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

## 🚀 Setup

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using poetry/pip with pyproject.toml
pip install -e .
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_BASE_URL=
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_REASONING_MODEL=o1
OPENAI_TIMEOUT=15
CHAT_MAX_HISTORY_TURNS=6
CHAT_SUMMARY_AFTER_TURNS=10

# Django settings
DEBUG=1
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Start Development Server

```bash
python manage.py runserver
```

The chatbot UI will be available at: **http://localhost:8000/chatbot/**

## 🧪 Testing

Run all chatbot tests:

```bash
# Run all tests
python manage.py test chatbot

# Run specific test modules
python manage.py test chatbot.tests.test_api
python manage.py test chatbot.tests.test_services

# Run with verbose output
python manage.py test chatbot --verbosity=2
```

### Test Coverage

- **API Tests** (`test_api.py`):
  - Text-only streaming
  - Image upload handling
  - PDF upload handling
  - Invalid model fallback
  - Conversation persistence
  - Model operations

- **Service Tests** (`test_services.py`):
  - Message builder utilities
  - OpenAI client initialization
  - PDF text extraction
  - Image to data URL conversion

## 📡 API Endpoints

### POST `/chatbot/api/chat/`

Stream chat responses using Server-Sent Events.

**Parameters:**
- `message` (required): User's text message
- `model` (optional): Model name (`gpt-4o-mini`, `gpt-4o`, `o1`)
- `conversation_id` (optional): UUID for conversation continuity
- `files` (optional): Uploaded files (images or PDFs)

**Response:**
- Content-Type: `text/event-stream`
- Events:
  - `conversation`: Contains conversation ID
  - `data`: Text deltas from the response
  - `done`: Marks completion
  - `error`: Error messages

**Example with curl:**

```bash
curl -X POST http://localhost:8000/chatbot/api/chat/ \
  -F "message=What is diabetes?" \
  -F "model=gpt-4o-mini"
```

**Example with JavaScript:**

```javascript
const formData = new FormData();
formData.append('message', 'What is diabetes?');
formData.append('model', 'gpt-4o-mini');

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
}
```

### GET `/chatbot/`

Serves the chatbot web interface.

## 🩺 Medical Safety Features

The chatbot includes several safety guardrails:

1. **System Prompt**: Every request includes a medical disclaimer prompt that:
   - Prohibits providing diagnosis
   - Prohibits prescribing treatments or medications
   - Requires recommending consultation with licensed physicians
   - Detects and responds to emergency mentions

2. **Educational Focus**: Responses are framed as educational information only

3. **Conversation Context**: Maintains context while respecting safety boundaries

Example system prompt:
```
You are a careful medical information assistant. 
Never provide diagnosis, prescriptions, or treatments. 
Provide general educational info only and always advise consulting a doctor. 
If the user mentions an emergency, tell them to seek emergency help immediately.
```

## 🔧 Advanced Usage

### Custom Model Selection

```python
# In views or services
from django.conf import settings

model = "gpt-4o"  # or "gpt-4o-mini", "o1"
if model in settings.ALLOWED_OPENAI_MODELS:
    # Use the model
    pass
```

### Conversation Summarization

Automatic summarization triggers after `CHAT_SUMMARY_AFTER_TURNS`:

```python
convo = await Conversation.objects.aget(id=conversation_id)
await convo.maybe_summarize()
```

### File Upload Handling

```python
# PDF extraction
from chatbot.services.pdf_utils import extract_text
pdf_text = await asyncio.to_thread(extract_text, pdf_file, max_pages=8)

# Image to data URL
from chatbot.services.image_utils import to_data_url_if_needed
data_url = await asyncio.to_thread(to_data_url_if_needed, image_file)
```

## 🛠️ Development Notes

### Using the Responses API

This project uses OpenAI's **Responses API (v1+)**, not the deprecated `chat.completions` API.

**Key differences:**
- Uses `client.responses.create()` and `client.responses.stream()`
- Message format includes `input` parameter with structured content types
- Content types: `input_text`, `input_image`
- Streaming events: `response.output_text.delta`

Example:
```python
response = client.responses.stream(
    model="gpt-4o-mini",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Hello"}
            ]
        }
    ]
)
```

### Async Best Practices

- All views use `async def` for non-blocking I/O
- File operations use `asyncio.to_thread()` for CPU-bound work
- Database queries use `aget()`, `acreate()`, `arefresh_from_db()`
- Streaming uses async generators

## 📚 References

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [Vision API Guide](https://platform.openai.com/docs/guides/images-vision)
- [Production Best Practices](https://platform.openai.com/docs/guides/production-best-practices)
- [Reasoning Models (o1)](https://platform.openai.com/docs/models/o1)

## 🐛 Troubleshooting

### Common Issues

1. **"pdfminer.six not installed"**
   - Run: `pip install pdfminer.six>=20231228`

2. **"Pillow not available"**
   - Run: `pip install Pillow>=10.4`

3. **OpenAI API errors**
   - Check `OPENAI_API_KEY` is set correctly
   - Verify model names are in `ALLOWED_OPENAI_MODELS`
   - Check API quota and billing

4. **Migration errors**
   - Run: `python manage.py migrate chatbot`

5. **Static files not loading**
   - Run: `python manage.py collectstatic`

## 📄 License

MIT License - See project root LICENSE file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## ✅ Checklist

- [x] Four-part settings structure (base, dev, prod, test)
- [x] OpenAI Responses API v1+ integration
- [x] Streaming responses via SSE
- [x] Text, image, and PDF support
- [x] Medical safety guardrails
- [x] Conversation history management
- [x] Auto-summarization
- [x] Model whitelisting
- [x] Async/await throughout
- [x] Full test coverage
- [x] Admin interface
- [x] Modern responsive UI
- [x] Production-ready error handling
- [x] Comprehensive documentation
