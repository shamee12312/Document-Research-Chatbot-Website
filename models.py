from app import db
from datetime import datetime
import json

class Document(db.Model):
    """Model for storing document metadata and content"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, image, text
    file_size = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Content and processing status
    extracted_text = db.Column(db.Text)
    page_count = db.Column(db.Integer, default=1)
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    
    # Vector store reference
    vector_ids = db.Column(db.Text)  # JSON array of vector IDs for ChromaDB
    
    def __repr__(self):
        return f'<Document {self.filename}>'
    
    def get_vector_ids(self):
        """Get vector IDs as list"""
        if self.vector_ids:
            return json.loads(self.vector_ids)
        return []
    
    def set_vector_ids(self, ids):
        """Set vector IDs from list"""
        self.vector_ids = json.dumps(ids)

class Query(db.Model):
    """Model for storing user queries and results"""
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Query results
    individual_answers = db.Column(db.Text)  # JSON array of document answers
    themes = db.Column(db.Text)  # JSON array of identified themes
    processing_time = db.Column(db.Float)
    
    def __repr__(self):
        return f'<Query {self.id}: {self.question[:50]}...>'
    
    def get_individual_answers(self):
        """Get individual answers as list"""
        if self.individual_answers:
            return json.loads(self.individual_answers)
        return []
    
    def set_individual_answers(self, answers):
        """Set individual answers from list"""
        self.individual_answers = json.dumps(answers)
    
    def get_themes(self):
        """Get themes as list"""
        if self.themes:
            return json.loads(self.themes)
        return []
    
    def set_themes(self, themes):
        """Set themes from list"""
        self.themes = json.dumps(themes)

class DocumentChunk(db.Model):
    """Model for storing document chunks for better citation tracking"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    paragraph_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    vector_id = db.Column(db.String(100))  # ChromaDB vector ID
    
    # Relationship
    document = db.relationship('Document', backref=db.backref('chunks', lazy=True))
    
    def __repr__(self):
        return f'<DocumentChunk {self.document_id}-{self.chunk_index}>'
