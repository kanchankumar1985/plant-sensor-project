"""
Ollama API client for local VLM inference
Provides a clean interface to Ollama's REST API
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Ollama configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
# Use a VISION-CAPABLE default model. Can be overridden via env OLLAMA_MODEL.
# Examples: 'llava:7b' (recommended), 'llava-phi:3.8b', 'moondream:latest'
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llava:7b') 
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '600'))  # seconds
VLM_FORCE_JSON = os.getenv('VLM_FORCE_JSON', 'true').lower() in ('1', 'true', 'yes', 'y')

class OllamaClient:
    """Client for interacting with local Ollama VLM"""
    
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
        self.timeout = OLLAMA_TIMEOUT
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 for Ollama API
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def generate(self, prompt: str, image_path: str, stream: bool = False) -> Dict[str, Any]:
        """
        Generate response from VLM
        
        Args:
            prompt: Text prompt for the model
            image_path: Path to image file
            stream: Whether to stream the response
            
        Returns:
            Response dictionary with 'response' key containing the model output
        """
        try:
            # Encode image
            image_b64 = self._encode_image(image_path)
            
            # Prepare request
            url = f"{self.host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": stream,
                # Ask Ollama to produce strict JSON if supported by the model/server
                **({"format": "json"} if VLM_FORCE_JSON else {}),
                "options": {
                    "temperature": 0.1,  # Low temperature for more deterministic output
                    "top_p": 0.9,
                }
            }
            
            # Make request
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            if stream:
                # For streaming, we'd need to handle chunks
                # For now, we use non-streaming
                raise NotImplementedError("Streaming not implemented yet")
            else:
                result = response.json()
                return result
                
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.host}. "
                "Make sure Ollama is running: 'ollama serve'"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Ollama request timed out after {self.timeout} seconds. "
                "Try a smaller model or increase OLLAMA_TIMEOUT."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
    
    def chat(self, messages: list, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Chat-style interaction with VLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            image_path: Optional path to image file
            
        Returns:
            Response dictionary
        """
        try:
            url = f"{self.host}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                **({"format": "json"} if VLM_FORCE_JSON else {}),
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                }
            }
            
            # Add image if provided
            if image_path:
                image_b64 = self._encode_image(image_path)
                # Add image to the last user message
                for msg in reversed(messages):
                    if msg.get('role') == 'user':
                        msg['images'] = [image_b64]
                        break
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise RuntimeError(f"Ollama chat API error: {str(e)}")
    
    def check_health(self) -> bool:
        """
        Check if Ollama is running and model is available
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get('models', [])
            model_names = [m.get('name') for m in models]
            
            if self.model not in model_names:
                print(f"⚠️  Model {self.model} not found. Available models: {model_names}")
                print(f"   Run: ollama pull {self.model}")
                print("   Note: Ensure you are using a vision-capable model (e.g., 'llava:7b').")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ollama health check failed: {e}")
            print(f"   Make sure Ollama is running: ollama serve")
            return False
    
    def pull_model(self, model: Optional[str] = None) -> bool:
        """
        Pull a model from Ollama registry
        
        Args:
            model: Model name to pull (defaults to self.model)
            
        Returns:
            True if successful
        """
        model_name = model or self.model
        
        try:
            url = f"{self.host}/api/pull"
            payload = {"name": model_name}
            
            print(f"📥 Pulling model {model_name}... (this may take a few minutes)")
            
            response = requests.post(url, json=payload, timeout=600, stream=True)
            response.raise_for_status()
            
            # Stream progress
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get('status', '')
                    if status:
                        print(f"   {status}")
            
            print(f"✅ Model {model_name} pulled successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to pull model: {e}")
            return False


# Singleton instance
_client = None

def get_ollama_client() -> OllamaClient:
    """Get or create singleton Ollama client"""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
