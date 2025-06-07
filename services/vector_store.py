import os
import logging
import json
import hashlib
from typing import List, Dict, Any
from config import Config

class VectorStore:
    """Simple in-memory vector store for document embeddings using OpenAI embeddings"""
    
    def __init__(self):
        self.documents = {}  # Store documents with their metadata
        self.embeddings = {}  # Store embeddings
        self.storage_file = os.path.join(Config.CHROMA_PERSIST_DIRECTORY, "vector_store.json")
        self._initialize()
    
    def _initialize(self):
        """Initialize vector store"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
            # Load existing data if available
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', {})
                    logging.info(f"Loaded {len(self.documents)} documents from storage")
            
            logging.info("Vector store initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a document chunk to the vector store"""
        try:
            # Generate unique ID
            vector_id = f"doc_{metadata['document_id']}_chunk_{metadata['chunk_index']}"
            
            # Store document with metadata
            self.documents[vector_id] = {
                'content': content,
                'metadata': metadata
            }
            
            # Save to file
            self._save_to_file()
            
            return vector_id
            
        except Exception as e:
            logging.error(f"Error adding document to vector store: {str(e)}")
            raise
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for similar documents using simple text matching"""
        try:
            results = []
            query_lower = query.lower()
            
            # Simple text matching for now - in production would use embeddings
            for vector_id, doc_data in self.documents.items():
                content = doc_data['content'].lower()
                metadata = doc_data['metadata']
                
                # Calculate simple relevance score based on keyword matches
                score = self._calculate_relevance_score(query_lower, content)
                
                if score > 0:
                    results.append({
                        'id': vector_id,
                        'content': doc_data['content'],
                        'metadata': metadata,
                        'score': score
                    })
            
            # Sort by score and limit results
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logging.error(f"Error searching vector store: {str(e)}")
            return []
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """Calculate simple relevance score based on keyword matches"""
        import re
        
        # Normalize and extract words
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        
        # Count matching words
        matches = len(query_words.intersection(content_words))
        
        if matches == 0:
            # Check for partial matches (substring matching)
            partial_matches = 0
            for qword in query_words:
                for cword in content_words:
                    if qword in cword or cword in qword:
                        partial_matches += 1
                        break
            
            if partial_matches > 0:
                return 0.3 * (partial_matches / len(query_words))
            return 0.0
        
        # Simple scoring: matches / total query words
        base_score = matches / len(query_words)
        
        # Boost score for more matches
        if matches >= len(query_words):
            base_score = 1.0
        
        return min(base_score, 1.0)
    
    def delete_vectors(self, vector_ids: List[str]):
        """Delete vectors by IDs"""
        try:
            for vector_id in vector_ids:
                if vector_id in self.documents:
                    del self.documents[vector_id]
            
            self._save_to_file()
            logging.info(f"Deleted {len(vector_ids)} vectors from store")
        except Exception as e:
            logging.error(f"Error deleting vectors: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            return {
                'total_vectors': len(self.documents),
                'collection_name': Config.CHROMA_COLLECTION_NAME
            }
        except Exception as e:
            logging.error(f"Error getting collection stats: {str(e)}")
            return {'total_vectors': 0, 'collection_name': Config.CHROMA_COLLECTION_NAME}
    
    def reset_collection(self):
        """Reset the collection (delete all vectors)"""
        try:
            self.documents = {}
            self._save_to_file()
            logging.info("Vector store collection reset successfully")
        except Exception as e:
            logging.error(f"Error resetting collection: {str(e)}")
            raise
    
    def _save_to_file(self):
        """Save documents to file"""
        try:
            data = {
                'documents': self.documents
            }
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving to file: {str(e)}")
