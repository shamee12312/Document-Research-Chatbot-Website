import os
import logging
import time
from typing import List, Tuple
from app import db
from models import Document, DocumentChunk
from services.vector_store import VectorStore
from services.ocr_service import OCRService
from utils.file_utils import extract_text_from_pdf, extract_text_from_txt
from config import Config

class DocumentProcessor:
    """Service for processing and indexing documents"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.ocr_service = OCRService()
        
    def process_document(self, document_id: int):
        """Process a document: extract text, create chunks, generate embeddings"""
        document = Document.query.get(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        try:
            document.processing_status = 'processing'
            db.session.commit()
            
            logging.info(f"Processing document: {document.original_filename}")
            
            # Extract text based on file type
            extracted_text = self._extract_text(document)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from the document")
            
            # Update document with extracted text
            document.extracted_text = extracted_text
            
            # Create text chunks with better citation tracking
            chunks = self._create_chunks(extracted_text, document.id)
            
            # Generate embeddings and store in vector database
            vector_ids = self._store_embeddings(chunks)
            
            # Update document with vector IDs
            document.set_vector_ids(vector_ids)
            document.processing_status = 'completed'
            from datetime import datetime
            document.processed_at = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"Successfully processed document: {document.original_filename}")
            
        except Exception as e:
            logging.error(f"Error processing document {document.original_filename}: {str(e)}")
            document.processing_status = 'failed'
            document.error_message = str(e)
            db.session.commit()
            raise
    
    def _extract_text(self, document: Document) -> str:
        """Extract text from document based on file type"""
        file_path = document.file_path
        
        if document.file_type == 'pdf':
            text = extract_text_from_pdf(file_path)
            
            # If PDF text extraction fails or returns minimal text, try OCR
            if len(text.strip()) < 50:
                logging.info(f"PDF text extraction minimal, attempting OCR for {document.original_filename}")
                text = self.ocr_service.extract_text_from_pdf(file_path)
                
        elif document.file_type == 'image':
            text = self.ocr_service.extract_text_from_image(file_path)
            
        elif document.file_type == 'text':
            text = extract_text_from_txt(file_path)
            
        else:
            raise ValueError(f"Unsupported file type: {document.file_type}")
        
        return text
    
    def _create_chunks(self, text: str, document_id: int) -> List[DocumentChunk]:
        """Create text chunks for better citation and embedding"""
        chunks = []
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_index = 0
        page_number = 1  # Simple page estimation
        paragraph_number = 1
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > Config.CHUNK_SIZE and current_chunk:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    page_number=page_number,
                    paragraph_number=paragraph_number,
                    content=current_chunk.strip()
                )
                chunks.append(chunk)
                db.session.add(chunk)
                
                chunk_index += 1
                current_chunk = paragraph
                
                # Simple page estimation (every 10 chunks = new page)
                if chunk_index % 10 == 0:
                    page_number += 1
                    paragraph_number = 1
                else:
                    paragraph_number += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                page_number=page_number,
                paragraph_number=paragraph_number,
                content=current_chunk.strip()
            )
            chunks.append(chunk)
            db.session.add(chunk)
        
        db.session.commit()
        return chunks
    
    def _store_embeddings(self, chunks: List[DocumentChunk]) -> List[str]:
        """Generate embeddings and store in vector database"""
        vector_ids = []
        
        for chunk in chunks:
            # Create metadata for the chunk
            metadata = {
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index,
                'page_number': chunk.page_number,
                'paragraph_number': chunk.paragraph_number,
                'document_filename': chunk.document.original_filename
            }
            
            # Store in vector database
            vector_id = self.vector_store.add_document(
                content=chunk.content,
                metadata=metadata
            )
            
            # Update chunk with vector ID
            chunk.vector_id = vector_id
            vector_ids.append(vector_id)
        
        db.session.commit()
        return vector_ids
    
    def search_similar_chunks(self, query: str, limit: int = 20) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks across all documents"""
        try:
            # Search in vector store
            results = self.vector_store.search(query, limit=limit)
            
            chunk_results = []
            for result in results:
                metadata = result.get('metadata', {})
                document_id = metadata.get('document_id')
                chunk_index = metadata.get('chunk_index')
                
                if document_id and chunk_index is not None:
                    chunk = DocumentChunk.query.filter_by(
                        document_id=document_id,
                        chunk_index=chunk_index
                    ).first()
                    
                    if chunk:
                        similarity_score = result.get('score', 0.0)
                        chunk_results.append((chunk, similarity_score))
            
            return chunk_results
            
        except Exception as e:
            logging.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    def get_document_stats(self) -> dict:
        """Get processing statistics"""
        return {
            'total': Document.query.count(),
            'pending': Document.query.filter_by(processing_status='pending').count(),
            'processing': Document.query.filter_by(processing_status='processing').count(),
            'completed': Document.query.filter_by(processing_status='completed').count(),
            'failed': Document.query.filter_by(processing_status='failed').count(),
        }
