import os
import logging
from typing import Optional
import PyPDF2
from config import Config

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_file_type(filename: str) -> str:
    """Determine file type based on extension"""
    if not filename or '.' not in filename:
        return 'unknown'
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension == 'pdf':
        return 'pdf'
    elif extension in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
        return 'image' 
    elif extension in ['txt', 'docx']:
        return 'text'
    else:
        return 'unknown'

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    logging.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    continue
        
        return text.strip()
        
    except Exception as e:
        logging.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from text file"""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    text = file.read()
                    return text.strip()
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, try with error handling
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
            logging.warning(f"Used UTF-8 with error handling for {file_path}")
            return text.strip()
            
    except Exception as e:
        logging.error(f"Error extracting text from file {file_path}: {str(e)}")
        return ""

def get_file_size_human(size_bytes: int) -> str:
    """Convert file size to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext
    
    return sanitized

def ensure_directory(directory_path: str):
    """Ensure directory exists, create if it doesn't"""
    try:
        os.makedirs(directory_path, exist_ok=True)
    except Exception as e:
        logging.error(f"Error creating directory {directory_path}: {str(e)}")
        raise

def delete_file_safe(file_path: str) -> bool:
    """Safely delete a file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {str(e)}")
        return False

def get_file_info(file_path: str) -> Optional[dict]:
    """Get comprehensive file information"""
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        
        return {
            'size': stat.st_size,
            'size_human': get_file_size_human(stat.st_size),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'is_file': os.path.isfile(file_path),
            'is_readable': os.access(file_path, os.R_OK),
            'extension': os.path.splitext(file_path)[1].lower()
        }
    except Exception as e:
        logging.error(f"Error getting file info for {file_path}: {str(e)}")
        return None
