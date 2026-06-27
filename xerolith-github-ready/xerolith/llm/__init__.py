"""
Gemini API Client — REST wrapper for Google Generative AI.
Handles function calling, chat sessions, and tool integration.
"""

import logging
import requests
import json
from typing import Optional, List, Dict, Any

logger = logging.getLogger("xerolith.llm.gemini")


class GeminiClient:
    """
    Gemini API client for text generation and function calling.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Generative AI API key
            base_url: API endpoint base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        logger.info("Gemini client initialized.")
    
    def create_chat(
        self,
        model_pool: List[str] = None,
        system_instruction: str = "",
        tools: List[Dict] = None,
        temperature: float = 0.8
    ) -> "GeminiChat":
        """
        Create a new chat session.
        
        Args:
            model_pool: List of model names to use
            system_instruction: System prompt
            tools: List of tool definitions
            temperature: Generation temperature (0.0-2.0)
        
        Returns:
            GeminiChat session
        """
        if not model_pool:
            model_pool = ["gemma-4-31b-it"]
        
        return GeminiChat(
            client=self,
            model_pool=model_pool,
            system_instruction=system_instruction,
            tools=tools,
            temperature=temperature
        )


class GeminiChat:
    """
    Single chat session with Gemini.
    Manages conversation history and function calling.
    """
    
    def __init__(
        self,
        client: GeminiClient,
        model_pool: List[str],
        system_instruction: str = "",
        tools: List[Dict] = None,
        temperature: float = 0.8
    ):
        """Initialize chat session."""
        self.client = client
        self.model_pool = model_pool
        self.model = model_pool[0] if model_pool else "gemma-4-31b-it"
        self.system_instruction = system_instruction
        self.tools = tools or []
        self.temperature = temperature
        self.messages = []
        
        if system_instruction:
            self.messages.append({
                "role": "user",
                "content": system_instruction
            })
            self.messages.append({
                "role": "assistant",
                "content": "System context loaded. Ready."
            })
    
    def send_message(self, message: str) -> "GeminiResponse":
        """
        Send a message and get response.
        
        Args:
            message: User message
        
        Returns:
            GeminiResponse with text and function calls
        """
        # Add user message
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        # Build request payload
        payload = {
            "model": f"models/{self.model}",
            "messages": self.messages,
            "temperature": self.temperature,
        }
        
        # Add tools if present
        if self.tools:
            payload["tools"] = self.tools
        
        try:
            # Call API
            response = requests.post(
                f"{self.client.base_url}chat/completions",
                headers=self.client.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract response
            choice = data["choices"][0] if data.get("choices") else {}
            content = choice.get("message", {}).get("content", "")
            
            # Parse function calls if present
            function_calls = []
            if "tool_calls" in choice.get("message", {}):
                for tool_call in choice["message"]["tool_calls"]:
                    function_calls.append({
                        "name": tool_call["function"]["name"],
                        "args": json.loads(tool_call["function"]["arguments"])
                    })
            
            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": content or ""
            })
            
            return GeminiResponse(text=content, function_calls=function_calls)
        
        except Exception as e:
            logger.error(f"API error: {e}")
            return GeminiResponse(text="", function_calls=[])
    
    def send_tool_result(self, tool_name: str, result: str) -> "GeminiResponse":
        """
        Send tool execution result back to LLM.
        
        Args:
            tool_name: Name of executed tool
            result: Tool output
        
        Returns:
            LLM response
        """
        # Add tool result to messages
        self.messages.append({
            "role": "user",
            "content": f"Tool '{tool_name}' result: {result}"
        })
        
        # Get next response
        return self.send_message("")


class GeminiResponse:
    """Response from Gemini API."""
    
    def __init__(self, text: str = "", function_calls: List[Dict] = None):
        """Initialize response."""
        self.text = text or ""
        self.function_calls = function_calls or []
