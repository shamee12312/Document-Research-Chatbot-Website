# Document Research & Theme Identification Chatbot
An advanced AI-powered document research system that processes multiple document types, extracts precise answers, and identifies cross-document themes for the Wasserstoff AI internship task.

Github Link : [https://github.com/shamee12312/Document-Research-Chatbot-Website]
Site Link :[]
Video Link : []

## Features

- **Multi-format Document Support**: Upload PDFs, images (PNG, JPG, TIFF, BMP), and text files
- **AI-Powered Analysis**: Intelligent query processing with multiple AI provider support
- **Theme Identification**: Cross-document pattern recognition and synthesis
- **Precise Citations**: Document references with page and paragraph numbers
- **Scalable Architecture**: Supports 75+ documents with PostgreSQL database
- **Real-time Processing**: Live upload status and processing indicators

## Technology Stack

- **Backend**: Flask web framework with Python
- **Database**: PostgreSQL for robust data storage
- **AI Providers**: Google AI Studio (Gemini), OpenRouter, Anthropic Claude, OpenAI GPT-4
- **Document Processing**: PyPDF2 for PDF extraction, OCR support for images
- **Vector Search**: Custom implementation for document similarity matching
- **Frontend**: Vanilla JavaScript with Bootstrap CSS

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export DATABASE_URL="your_postgresql_url"
   export GOOGLE_AI_API_KEY="your_google_ai_key"
   export OPENROUTER_API_KEY="your_openrouter_key" # Optional
   export ANTHROPIC_API_KEY="your_anthropic_key"   # Optional
   export OPENAI_API_KEY="your_openai_key"         # Optional
   ```

3. **Initialize Database**:
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

4. **Run Application**:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## API Key Setup

### Google AI Studio (Recommended - Free Tier)
1. Visit [aistudio.google.com](https://aistudio.google.com)
2. Create account and get API key
3. Set as `GOOGLE_AI_API_KEY`

### OpenRouter (Alternative)
1. Visit [openrouter.ai](https://openrouter.ai)
2. Create account and get API key
3. Set as `OPENROUTER_API_KEY`

## Usage

1. **Upload Documents**: Drag and drop or select files up to 50MB each
2. **Wait for Processing**: Documents are automatically processed and indexed
3. **Ask Questions**: Use natural language queries about your documents
4. **View Results**: Get individual answers with citations and identified themes
5. **Export Data**: Download results or view detailed analysis

## Project Structure

```
├── app.py                 # Flask application setup
├── main.py               # Application entry point
├── routes.py             # Web routes and API endpoints
├── models.py             # Database models
├── config.py             # Configuration settings
├── services/
│   ├── ai_service.py     # AI provider integration
│   ├── document_processor.py # Document processing pipeline
│   ├── vector_store.py   # Document similarity search
│   └── ocr_service.py    # OCR text extraction
├── utils/
│   └── file_utils.py     # File handling utilities
├── templates/            # HTML templates
├── static/              # CSS, JavaScript, images
└── uploads/             # Document storage directory
```

## Key Components

### Document Processing Pipeline
1. **Upload & Validation**: File type and size validation
2. **Text Extraction**: PDF parsing and OCR for images
3. **Chunking**: Smart text segmentation for better analysis
4. **Vector Storage**: Document embedding and indexing
5. **Status Tracking**: Real-time processing updates

### AI Query System
1. **Document Search**: Vector similarity matching
2. **Answer Extraction**: AI-powered content analysis
3. **Theme Identification**: Cross-document pattern recognition
4. **Citation Generation**: Precise source references

## API Endpoints

- `GET /` - Home page with system overview
- `POST /upload` - Document upload endpoint
- `GET /documents` - Document management interface
- `POST /query` - Submit research questions
- `GET /results/<id>` - View query results
- `GET /api/document-status/<id>` - Check processing status

## Configuration

Key settings in `config.py`:
- `CHUNK_SIZE`: Text chunk size for embeddings (default: 1000)
- `SIMILARITY_THRESHOLD`: Minimum relevance score (default: 0.7)
- `MAX_DOCUMENTS_PER_QUERY`: Query result limit (default: 20)
- `ALLOWED_EXTENSIONS`: Supported file types

## Performance

- Supports 75+ documents simultaneously
- Real-time processing with status updates
- Efficient vector search for fast query responses
- Robust error handling and recovery

## Security

- File type validation and sanitization
- Secure filename handling
- Environment variable configuration
- Database connection pooling

## Troubleshooting

**Rate Limiting**: Google AI Studio free tier has 15 requests/minute limit
**Large Files**: Increase `MAX_CONTENT_LENGTH` for files > 50MB
**Database Issues**: Check PostgreSQL connection and permissions
**Processing Errors**: Review logs in application console

## License

Built for the Wasserstoff AI internship task demonstration.
