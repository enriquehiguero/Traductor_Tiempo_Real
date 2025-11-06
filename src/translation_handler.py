"""
Translation Handler Module
Handles text translation using local LLM models for the real-time translation app
"""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import threading
import queue
from typing import Optional, Callable
import time
import re


class TranslationHandler:
    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-es-en", use_gpu: bool = True):
        self.model_name = model_name
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        
        # Translation parameters - DEFINIR ANTES de llamar a load_model()
        self.max_length = 512  # Increased for better quality (full sentences)
        self.truncation = True
        self.optimized_batch_size = 1  # Process one at a time for lower latency

        # Quality parameters
        self.num_beams = 5  # Beam search for better quality (default=1)
        self.early_stopping = True  # Stop when all beams finish
        self.no_repeat_ngram_size = 3  # Avoid repetitions
        self.length_penalty = 1.0  # Neutral length penalty
        
        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None
        self.translation_pipeline = None
        
        # Threading and queues for processing
        self.translation_queue = queue.Queue()
        self.result_callbacks = {}  # Store callbacks for async processing
        self.request_counter = 0
        
        self.load_model()  # Ahora load_model puede usar self.max_length
        
        # Callback for translation results
        self.translation_callback: Optional[Callable] = None
    
    def load_model(self):
        """Load the translation model"""
        try:
            print(f"Loading translation model: {self.model_name} (Device: {self.device})")
            
            # Load model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            
            # Move model to device
            self.model.to(self.device)
            
            # Create translation pipeline
            self.translation_pipeline = pipeline(
                "translation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.use_gpu else -1,  # -1 for CPU
                max_length=self.max_length,
                truncation=self.truncation
            )
            
            print(f"Translation model {self.model_name} loaded successfully on {self.device}!")
            
        except Exception as e:
            print(f"Error loading translation model: {e}")
            # Fallback to a more common model
            try:
                fallback_model = "Helsinki-NLP/opus-mt-en-es"  # English to Spanish
                print(f"Falling back to {fallback_model}...")
                
                self.model_name = fallback_model
                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(fallback_model)
                self.model.to(self.device)
                
                self.translation_pipeline = pipeline(
                    "translation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if self.use_gpu else -1,
                    max_length=self.max_length,
                    truncation=self.truncation
                )
                
                print(f"Fallback model {fallback_model} loaded successfully!")
            except Exception as e2:
                print(f"Fallback model also failed: {e2}")
                raise
    
    def translate_text(self, text: str, src_lang: str = None, tgt_lang: str = None) -> str:
        """Translate text using the loaded model with quality parameters"""
        if not text or not text.strip():
            return ""

        if self.translation_pipeline is None:
            return f"[Translation model not loaded: {text}]"

        try:
            # Preprocess text for better quality
            text = self.preprocess_text(text)

            # Perform the translation with quality parameters
            result = self.translation_pipeline(
                text,
                max_length=self.max_length,
                num_beams=self.num_beams,
                early_stopping=self.early_stopping,
                no_repeat_ngram_size=self.no_repeat_ngram_size,
                length_penalty=self.length_penalty
            )

            # Extract the translated text
            if isinstance(result, list) and len(result) > 0:
                translated_text = result[0].get('translation_text', text)
            elif isinstance(result, dict):
                translated_text = result.get('translation_text', text)
            else:
                translated_text = str(result)

            # Postprocess for better output
            translated_text = self.postprocess_text(translated_text)

            return translated_text

        except Exception as e:
            print(f"Error during translation: {e}")
            return f"[Translation error: {text}]"
    
    def translate_text_async(self, text: str, callback: Optional[Callable] = None) -> int:
        """Asynchronously translate text with callback"""
        request_id = self.request_counter
        self.request_counter += 1
        
        # Store the callback if provided
        if callback:
            self.result_callbacks[request_id] = callback
        
        # Create a thread to process the translation
        thread = threading.Thread(
            target=self._translate_worker,
            args=(text, request_id)
        )
        thread.daemon = True
        thread.start()
        
        return request_id
    
    def _translate_worker(self, text: str, request_id: int):
        """Worker thread for performing translation"""
        try:
            result = self.translate_text(text)
            
            # Call the registered callback if it exists
            if request_id in self.result_callbacks:
                callback = self.result_callbacks.pop(request_id)
                callback(result)
            elif self.translation_callback:
                self.translation_callback(result)
                
        except Exception as e:
            print(f"Error in translation worker: {e}")
            error_msg = f"[Translation error: {text}]"
            
            # Call the registered callback if it exists
            if request_id in self.result_callbacks:
                callback = self.result_callbacks.pop(request_id)
                callback(error_msg)
            elif self.translation_callback:
                self.translation_callback(error_msg)
    
    def set_translation_callback(self, callback: Callable[[str], None]):
        """Set callback function to handle translation results"""
        self.translation_callback = callback
    
    def change_model(self, model_name: str, use_gpu: bool = None):
        """Change the translation model"""
        if use_gpu is not None:
            self.use_gpu = use_gpu and torch.cuda.is_available()
            self.device = "cuda" if self.use_gpu else "cpu"
        
        if model_name != self.model_name:
            self.model_name = model_name
            self.model = None
            self.tokenizer = None
            self.translation_pipeline = None
            self.load_model()
    
    def get_supported_languages(self):
        """Return a list of supported language pairs for the model"""
        # This is a simplified implementation
        # In a production system, you would check the specific model's capabilities
        model_name_lower = self.model_name.lower()
        
        if "es-en" in model_name_lower:
            return {"source": "Spanish", "target": "English"}
        elif "en-es" in model_name_lower:
            return {"source": "English", "target": "Spanish"}
        elif "fr-en" in model_name_lower:
            return {"source": "French", "target": "English"}
        elif "en-fr" in model_name_lower:
            return {"source": "English", "target": "French"}
        elif "de-en" in model_name_lower:
            return {"source": "German", "target": "English"}
        elif "en-de" in model_name_lower:
            return {"source": "English", "target": "German"}
        else:
            return {"source": "Unknown", "target": "Unknown"}
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text before translation for better quality"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove filler words and speech artifacts
        fillers = [r'\buh+\b', r'\bum+\b', r'\blike\b(?!\s+to\b)', r'\byou know\b']
        for filler in fillers:
            text = re.sub(filler, '', text, flags=re.IGNORECASE)

        # Clean up again after removing fillers
        text = re.sub(r'\s+', ' ', text.strip())

        # Ensure proper capitalization for better model understanding
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]

        # Add period if missing for complete sentences
        if text and text[-1] not in '.!?':
            text = text + '.'

        return text

    def postprocess_text(self, text: str) -> str:
        """Postprocess translated text for better output"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Capitalize first letter
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]

        # Fix common spacing issues
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.,!?;:])(?=[^\s])', r'\1 ', text)  # Add space after punctuation

        # Remove duplicate punctuation
        text = re.sub(r'([.!?])\1+', r'\1', text)

        return text