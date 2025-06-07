import json
import logging
from typing import List, Dict, Tuple, Any
import os
from services.document_processor import DocumentProcessor
from models import Document
from config import Config

class AIService:
    """AI service for answer extraction and theme identification"""
    
    def __init__(self):
        # Try Google AI Studio first, then OpenRouter, then Anthropic, then OpenAI
        self.google_ai_key = os.environ.get('GOOGLE_AI_API_KEY')
        self.openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        self.anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        
        if self.google_ai_key:
            self._init_google_ai()
        elif self.openrouter_key:
            self._init_openrouter()
        elif self.anthropic_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.anthropic_key)
                self.ai_provider = 'anthropic'
                logging.info("Using Anthropic Claude API")
            except ImportError:
                logging.warning("Anthropic library not available, falling back to OpenAI")
                self._init_openai()
        else:
            self._init_openai()
            
        self.document_processor = DocumentProcessor()
    
    def _init_google_ai(self):
        """Initialize Google AI Studio client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.google_ai_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            self.ai_provider = 'google'
            logging.info("Using Google AI Studio API")
        except ImportError:
            logging.warning("Google AI library not available, falling back to OpenRouter")
            self._init_openrouter()
    
    def _init_openrouter(self):
        """Initialize OpenRouter client"""
        from openai import OpenAI
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_key
        )
        self.ai_provider = 'openrouter'
        logging.info("Using OpenRouter API")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        if self.openai_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.openai_key)
            self.ai_provider = 'openai'
            logging.info("Using OpenAI API")
        else:
            raise ValueError("No valid AI API key found")
    
    def process_query(self, question: str) -> Tuple[List[Dict], List[Dict]]:
        """Process a query and return individual answers and themes"""
        try:
            # Search for relevant document chunks
            relevant_chunks = self.document_processor.search_similar_chunks(
                question, 
                limit=Config.MAX_DOCUMENTS_PER_QUERY
            )
            
            if not relevant_chunks:
                return [], []
            
            # Filter by similarity threshold
            filtered_chunks = [
                (chunk, score) for chunk, score in relevant_chunks
                if score >= Config.SIMILARITY_THRESHOLD
            ]
            
            if not filtered_chunks:
                return [], []
            
            # Extract individual answers from each relevant chunk
            individual_answers = self._extract_individual_answers(question, filtered_chunks)
            
            # Identify themes across all answers
            themes = self._identify_themes(question, individual_answers)
            
            return individual_answers, themes
            
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            raise
    
    def _extract_individual_answers(self, question: str, chunks_with_scores: List[Tuple]) -> List[Dict]:
        """Extract answers from individual document chunks"""
        individual_answers = []
        
        for chunk, similarity_score in chunks_with_scores:
            try:
                # Prepare the prompt for answer extraction
                prompt = f"""
                You are an expert document analyst. Given the following question and document excerpt, 
                extract a precise answer if one exists. If no relevant answer exists, respond with "No relevant answer found."
                
                Question: {question}
                
                Document Content: {chunk.content}
                
                Provide your response in JSON format:
                {{
                    "answer": "extracted answer or 'No relevant answer found'",
                    "confidence": 0.0-1.0,
                    "relevant": true/false
                }}
                """
                
                if self.ai_provider == 'google':
                    response = self.client.generate_content(prompt)
                    try:
                        answer_data = json.loads(response.text)
                    except json.JSONDecodeError:
                        # Handle malformed JSON by extracting relevant parts
                        content = response.text
                        answer_data = {'answer': content, 'confidence': 0.5, 'relevant': True}
                elif self.ai_provider == 'openrouter':
                    response = self.client.chat.completions.create(
                        model="anthropic/claude-3.5-sonnet",  # Using Claude via OpenRouter
                        messages=[
                            {"role": "system", "content": "You are a precise document analyst that extracts specific answers from text."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                    try:
                        answer_data = json.loads(response.choices[0].message.content)
                    except json.JSONDecodeError:
                        # Handle malformed JSON by extracting relevant parts
                        content = response.choices[0].message.content
                        answer_data = {'answer': content, 'confidence': 0.5, 'relevant': True}
                elif self.ai_provider == 'anthropic':
                    response = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        max_tokens=500,
                        temperature=0.3,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    try:
                        answer_data = json.loads(response.content[0].text)
                    except json.JSONDecodeError:
                        content = response.content[0].text
                        answer_data = {'answer': content, 'confidence': 0.5, 'relevant': True}
                else:
                    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                    # do not change this unless explicitly requested by the user
                    response = self.client.chat.completions.create(
                        model=Config.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a precise document analyst that extracts specific answers from text."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    try:
                        answer_data = json.loads(response.choices[0].message.content)
                    except json.JSONDecodeError:
                        content = response.choices[0].message.content
                        answer_data = {'answer': content, 'confidence': 0.5, 'relevant': True}
                
                # Only include relevant answers
                if answer_data.get('relevant', False) and answer_data.get('answer', '').lower() != 'no relevant answer found':
                    answer_entry = {
                        'document_id': chunk.document.id,
                        'document_filename': chunk.document.original_filename,
                        'answer': answer_data['answer'],
                        'citation': f"Page {chunk.page_number}, Para {chunk.paragraph_number}",
                        'confidence': answer_data.get('confidence', 0.0),
                        'similarity_score': similarity_score,
                        'page_number': chunk.page_number,
                        'paragraph_number': chunk.paragraph_number
                    }
                    individual_answers.append(answer_entry)
                
            except Exception as e:
                logging.error(f"Error extracting answer from chunk {chunk.id}: {str(e)}")
                continue
        
        # Sort by confidence and similarity
        individual_answers.sort(key=lambda x: (x['confidence'], x['similarity_score']), reverse=True)
        
        return individual_answers
    
    def _identify_themes(self, question: str, individual_answers: List[Dict]) -> List[Dict]:
        """Identify common themes across individual answers"""
        if not individual_answers:
            return []
        
        try:
            # Prepare answers for theme analysis
            answers_text = ""
            document_references = {}
            
            for i, answer in enumerate(individual_answers):
                answers_text += f"Answer {i+1} (from {answer['document_filename']}): {answer['answer']}\n\n"
                doc_key = f"DOC{answer['document_id']:03d}"
                if doc_key not in document_references:
                    document_references[doc_key] = {
                        'filename': answer['document_filename'],
                        'document_id': answer['document_id']
                    }
            
            # Create theme identification prompt
            prompt = f"""
            You are an expert analyst tasked with identifying common themes across multiple document answers to a question.
            
            Original Question: {question}
            
            Individual Answers:
            {answers_text}
            
            Analyze these answers and identify the main themes. For each theme:
            1. Provide a clear theme title
            2. Give a synthesized summary of that theme
            3. List the supporting document references
            
            Respond in JSON format:
            {{
                "themes": [
                    {{
                        "title": "Theme Title",
                        "summary": "Comprehensive summary of this theme based on the evidence",
                        "supporting_documents": ["DOC001", "DOC002"],
                        "confidence": 0.0-1.0
                    }}
                ]
            }}
            
            Guidelines:
            - Only identify themes that are clearly supported by multiple sources or very strong single sources
            - Each theme should have a meaningful synthesis, not just a repetition
            - Be specific and actionable in your summaries
            - Minimum confidence threshold is 0.7
            """
            
            if self.ai_provider == 'google':
                response = self.client.generate_content(prompt)
                try:
                    result = json.loads(response.text)
                except json.JSONDecodeError:
                    # Handle malformed JSON
                    content = response.text
                    result = {'themes': [{'title': 'Analysis Result', 'summary': content, 'supporting_documents': [], 'confidence': 0.8}]}
            elif self.ai_provider == 'openrouter':
                response = self.client.chat.completions.create(
                    model="anthropic/claude-3.5-sonnet",
                    messages=[
                        {"role": "system", "content": "You are an expert thematic analyst who identifies patterns and synthesizes insights across multiple documents."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                try:
                    result = json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    content = response.choices[0].message.content
                    result = {'themes': [{'title': 'Analysis Result', 'summary': content, 'supporting_documents': [], 'confidence': 0.8}]}
            else:
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert thematic analyst who identifies patterns and synthesizes insights across multiple documents."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                try:
                    result = json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    content = response.choices[0].message.content
                    result = {'themes': [{'title': 'Analysis Result', 'summary': content, 'supporting_documents': [], 'confidence': 0.8}]}
            themes = result.get('themes', [])
            
            # Enhance themes with document details
            enhanced_themes = []
            for theme in themes:
                if theme.get('confidence', 0) >= 0.7:
                    # Add document details to supporting documents
                    supporting_docs_details = []
                    for doc_key in theme.get('supporting_documents', []):
                        if doc_key in document_references:
                            supporting_docs_details.append({
                                'document_key': doc_key,
                                'filename': document_references[doc_key]['filename'],
                                'document_id': document_references[doc_key]['document_id']
                            })
                    
                    enhanced_theme = {
                        'title': theme['title'],
                        'summary': theme['summary'],
                        'supporting_documents': supporting_docs_details,
                        'confidence': theme['confidence']
                    }
                    enhanced_themes.append(enhanced_theme)
            
            return enhanced_themes
            
        except Exception as e:
            logging.error(f"Error identifying themes: {str(e)}")
            return []
    
    def generate_follow_up_questions(self, question: str, themes: List[Dict]) -> List[str]:
        """Generate follow-up questions based on identified themes"""
        if not themes:
            return []
        
        try:
            themes_text = ""
            for theme in themes:
                themes_text += f"- {theme['title']}: {theme['summary']}\n"
            
            prompt = f"""
            Based on the original question and identified themes, suggest 3-5 relevant follow-up questions 
            that would help the user explore these topics deeper.
            
            Original Question: {question}
            
            Identified Themes:
            {themes_text}
            
            Provide response in JSON format:
            {{
                "follow_up_questions": ["question1", "question2", "question3"]
            }}
            """
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates insightful follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('follow_up_questions', [])
            
        except Exception as e:
            logging.error(f"Error generating follow-up questions: {str(e)}")
            return []
