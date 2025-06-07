import os
import time
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, Query, DocumentChunk
from services.document_processor import DocumentProcessor
from services.ai_service import AIService
from utils.file_utils import allowed_file, get_file_type
from config import Config

# Initialize services
document_processor = DocumentProcessor()
ai_service = AIService()

@app.route('/')
def index():
    """Home page showing system status and overview"""
    # Get system statistics
    total_documents = Document.query.count()
    processed_documents = Document.query.filter_by(processing_status='completed').count()
    total_queries = Query.query.count()
    
    # Check configuration
    config_errors = Config.validate_config()
    
    return render_template('index.html', 
                         total_documents=total_documents,
                         processed_documents=processed_documents,
                         total_queries=total_queries,
                         config_errors=config_errors)

@app.route('/upload', methods=['GET', 'POST'])
def upload_documents():
    """Handle document upload"""
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            flash('No files selected', 'error')
            return redirect(request.url)
        
        uploaded_count = 0
        failed_files = []
        
        for file in files:
            if file and file.filename != '':
                if allowed_file(file.filename):
                    try:
                        # Save file
                        filename = secure_filename(file.filename)
                        # Add timestamp to avoid conflicts
                        timestamp = str(int(time.time()))
                        filename = f"{timestamp}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        
                        # Create document record
                        document = Document(
                            filename=filename,
                            original_filename=file.filename,
                            file_path=file_path,
                            file_type=get_file_type(file.filename),
                            file_size=os.path.getsize(file_path),
                            processing_status='pending'
                        )
                        
                        db.session.add(document)
                        db.session.commit()
                        
                        # Process document asynchronously (in background)
                        try:
                            document_processor.process_document(document.id)
                            uploaded_count += 1
                        except Exception as e:
                            logging.error(f"Error processing document {filename}: {str(e)}")
                            document.processing_status = 'failed'
                            document.error_message = str(e)
                            db.session.commit()
                            failed_files.append(file.filename)
                        
                    except Exception as e:
                        logging.error(f"Error uploading file {file.filename}: {str(e)}")
                        failed_files.append(file.filename)
                else:
                    failed_files.append(f"{file.filename} (unsupported format)")
        
        if uploaded_count > 0:
            flash(f'Successfully uploaded {uploaded_count} documents', 'success')
        
        if failed_files:
            flash(f'Failed to upload: {", ".join(failed_files)}', 'error')
        
        return redirect(url_for('documents'))
    
    return render_template('upload.html')

@app.route('/documents')
def documents():
    """Display all uploaded documents"""
    documents = Document.query.order_by(Document.uploaded_at.desc()).all()
    return render_template('documents.html', documents=documents)

@app.route('/documents/<int:doc_id>/delete', methods=['POST'])
def delete_document(doc_id):
    """Delete a document and its associated data"""
    document = Document.query.get_or_404(doc_id)
    
    try:
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from vector store
        if document.get_vector_ids():
            document_processor.vector_store.delete_vectors(document.get_vector_ids())
        
        # Delete document chunks
        DocumentChunk.query.filter_by(document_id=doc_id).delete()
        
        # Delete document record
        db.session.delete(document)
        db.session.commit()
        
        flash(f'Document "{document.original_filename}" deleted successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error deleting document {doc_id}: {str(e)}")
        flash('Error deleting document', 'error')
        db.session.rollback()
    
    return redirect(url_for('documents'))

@app.route('/query', methods=['GET', 'POST'])
def query_documents():
    """Handle document querying"""
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        
        if not question:
            flash('Please enter a question', 'error')
            return redirect(request.url)
        
        # Check if we have processed documents
        processed_docs = Document.query.filter_by(processing_status='completed').count()
        if processed_docs == 0:
            flash('No processed documents available. Please upload and wait for processing to complete.', 'error')
            return redirect(request.url)
        
        try:
            start_time = time.time()
            
            # Create query record
            query = Query(question=question)
            db.session.add(query)
            db.session.commit()
            
            # Process the query
            individual_answers, themes = ai_service.process_query(question)
            
            # Update query with results
            query.set_individual_answers(individual_answers)
            query.set_themes(themes)
            query.processing_time = time.time() - start_time
            db.session.commit()
            
            return redirect(url_for('query_results', query_id=query.id))
            
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            flash(f'Error processing query: {str(e)}', 'error')
            return redirect(request.url)
    
    # Get recent queries for display
    recent_queries = Query.query.order_by(Query.created_at.desc()).limit(5).all()
    processed_docs_count = Document.query.filter_by(processing_status='completed').count()
    
    return render_template('query.html', 
                         recent_queries=recent_queries,
                         processed_docs_count=processed_docs_count)

@app.route('/results/<int:query_id>')
def query_results(query_id):
    """Display query results"""
    query = Query.query.get_or_404(query_id)
    
    individual_answers = query.get_individual_answers()
    themes = query.get_themes()
    
    # Calculate unique document count
    unique_document_count = len(set(answer.get('document_id') for answer in individual_answers))
    
    return render_template('results.html', 
                         query=query,
                         individual_answers=individual_answers,
                         themes=themes,
                         unique_document_count=unique_document_count)

@app.route('/api/document-status/<int:doc_id>')
def document_status(doc_id):
    """API endpoint to check document processing status"""
    document = Document.query.get_or_404(doc_id)
    
    return jsonify({
        'id': document.id,
        'filename': document.original_filename,
        'status': document.processing_status,
        'error': document.error_message
    })

@app.route('/api/system-stats')
def system_stats():
    """API endpoint for system statistics"""
    return jsonify({
        'total_documents': Document.query.count(),
        'processed_documents': Document.query.filter_by(processing_status='completed').count(),
        'processing_documents': Document.query.filter_by(processing_status='processing').count(),
        'failed_documents': Document.query.filter_by(processing_status='failed').count(),
        'total_queries': Query.query.count()
    })

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 50MB.', 'error')
    return redirect(url_for('upload_documents'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500
