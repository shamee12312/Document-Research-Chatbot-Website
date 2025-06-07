import os

class Config:
    """Configuration class for the application"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-openai-api-key")
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIRECTORY = os.environ.get("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    CHROMA_COLLECTION_NAME = "document_embeddings"
    
    # OCR Configuration
    TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "tesseract")
    
    # Processing Configuration
    CHUNK_SIZE = 1000  # Characters per chunk for embeddings
    CHUNK_OVERLAP = 200  # Overlap between chunks
    
    # Supported file types
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'txt', 'docx'}
    
    # AI Model Configuration
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    OPENAI_MODEL = "gpt-4o"  # The newest OpenAI model released May 13, 2024
    
    # Query Configuration
    MAX_DOCUMENTS_PER_QUERY = 20  # Maximum documents to process per query
    SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score for relevant chunks
    
    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        errors = []
        
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your-openai-api-key":
            errors.append("OPENAI_API_KEY environment variable is not set")
        
        return errors
