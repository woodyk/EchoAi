#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: api.py
# Author: Wadih Khairallah
# Description: RESTful API interface for the Interactor class
#              Exposes AI interaction functionality for web applications
# Created: 2025-04-07 10:00:00
# Modified: 2025-05-12 16:08:18

import os
import json
from typing import Dict, Any, Optional, List, Union
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from queue import Queue, Empty
import threading
import time

from interactor import Interactor, Session

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Global interactor instance
interactor = None


def get_interactor() -> Interactor:
    """Get or initialize the global interactor instance.
    
    Returns:
        Interactor: The global interactor instance
    """
    global interactor
    if interactor is None:
        interactor = Interactor(stream=True, tools=True)
    return interactor


@app.route('/api/interact', methods=['POST'])
def api_interact():
    """Interact with the AI model and get a response.
    
    Request JSON parameters:
        message (str): The user's input message
        stream (bool, optional): Whether to stream the response (default: True)
        tools (bool, optional): Whether to enable tool calling (default: True)
        model (str, optional): Model to use for this interaction (e.g., "openai:gpt-4o")
        markdown (bool, optional): Whether to render markdown (default: False)
    
    Returns:
        If streaming is enabled: A streaming response with chunks of the AI's response
        If streaming is disabled: A JSON response with the AI's complete response
    """
    data = request.json
    user_input = data.get('message')
    stream_enabled = data.get('stream', True)
    tools_enabled = data.get('tools', True)
    model = data.get('model')
    markdown = data.get('markdown', False)
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    ai = get_interactor()
    
    if stream_enabled:
        def generate():
            q = Queue()
            
            def stream_callback(token):
                q.put(token)
            
            def generate_response():
                try:
                    ai.interact(
                        user_input, 
                        output_callback=stream_callback, 
                        stream=True, 
                        tools=tools_enabled,
                        model=model,
                        markdown=markdown
                    )
                finally:
                    q.put(None)  # Signal end of stream
            
            threading.Thread(target=generate_response, daemon=True).start()
            
            while True:
                try:
                    token = q.get(timeout=0.25)
                    if token is None:
                        break
                    yield token
                except Empty:
                    continue
        
        return Response(stream_with_context(generate()), content_type="text/plain")
    else:
        response = ai.interact(
            user_input, 
            stream=False, 
            tools=tools_enabled,
            model=model,
            markdown=markdown,
            quiet=True
        )
        return jsonify({"response": response})


@app.route('/api/models', methods=['GET'])
def list_models():
    """List available AI models.
    
    Query parameters:
        provider (str, optional): Filter models by provider
        filter (str, optional): Regex pattern to filter model names
    
    Returns:
        JSON response with list of available models
    """
    provider = request.args.get('provider')
    filter_pattern = request.args.get('filter')
    
    ai = get_interactor()
    models = ai.list(providers=provider, filter=filter_pattern)
    
    return jsonify({"models": models})


@app.route('/api/add_function', methods=['POST'])
def add_function():
    """Register a function for tool calling.
    
    Request JSON parameters:
        module_path (str): Path to the Python module containing the function
        function_name (str): Name of the function to register
        custom_name (str, optional): Custom name for the function
        description (str, optional): Custom description for the function
    
    Returns:
        JSON response indicating success or failure
    """
    data = request.json
    module_path = data.get('module_path')
    function_name = data.get('function_name')
    custom_name = data.get('custom_name')
    description = data.get('description')
    
    if not module_path or not function_name:
        return jsonify({"error": "Module path and function name are required"}), 400
    
    try:
        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the function from the module
        func = getattr(module, function_name)
        
        # Register the function with the interactor
        ai = get_interactor()
        ai.add_function(func, name=custom_name, description=description)
        
        return jsonify({"success": True, "message": f"Function {function_name} registered successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/functions', methods=['GET'])
def get_functions():
    """Get the list of registered functions for tool calling.
    
    Returns:
        JSON response with list of registered functions
    """
    ai = get_interactor()
    functions = ai.get_functions()
    
    return jsonify({"functions": functions})


@app.route('/api/system_prompt', methods=['POST'])
def set_system_prompt():
    """Set the system prompt for the conversation.
    
    Request JSON parameters:
        prompt (str): The system prompt to set
    
    Returns:
        JSON response with the updated system prompt
    """
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    ai = get_interactor()
    system_prompt = ai.messages_system(prompt)
    
    return jsonify({"system_prompt": system_prompt})


@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get the current conversation history.
    
    Returns:
        JSON response with the conversation history
    """
    ai = get_interactor()
    messages = ai.messages()
    
    return jsonify({"messages": messages})


@app.route('/api/messages', methods=['DELETE'])
def clear_messages():
    """Clear the conversation history while preserving the system prompt.
    
    Returns:
        JSON response indicating success
    """
    ai = get_interactor()
    ai.messages_flush()
    
    return jsonify({"success": True, "message": "Conversation history cleared"})


@app.route('/api/messages', methods=['POST'])
def add_message():
    """Add a message to the conversation history.
    
    Request JSON parameters:
        role (str): The role of the message (e.g., 'user', 'system', 'assistant')
        content (str): The content of the message
    
    Returns:
        JSON response with the updated conversation history
    """
    data = request.json
    role = data.get('role')
    content = data.get('content')
    
    if not role or not content:
        return jsonify({"error": "Role and content are required"}), 400
    
    ai = get_interactor()
    messages = ai.messages_add(role, content)
    
    return jsonify({"messages": messages})


@app.route('/api/model', methods=['GET'])
def get_model():
    """Get the currently configured model.
    
    Returns:
        JSON response with the current model information
    """
    ai = get_interactor()
    
    return jsonify({
        "provider": ai.provider,
        "model": ai.model,
        "full_model": f"{ai.provider}:{ai.model}",
        "tools_supported": ai.tools_supported
    })


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get the current settings for the Interactor class.
    
    Returns:
        JSON response with all configuration options except API keys
    """
    ai = get_interactor()
    
    settings = {
        "model": ai.model,
        "provider": ai.provider,
        "stream": ai.stream,
        "tools_enabled": ai.tools_enabled,
        "tools_supported": ai.tools_supported,
        "context_length": ai.context_length,
        "system_prompt": ai.system,
        "message_count": len(ai.history),
        "token_count": ai.messages_length()
    }
    
    # Include base URLs for providers but exclude API keys for security
    provider_configs = {}
    for provider, config in ai.providers.items():
        provider_configs[provider] = {
            "base_url": config["base_url"]
        }
    
    settings["providers"] = provider_configs
    
    return jsonify(settings)


@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch to a different AI model.
    
    Request JSON parameters:
        model (str): Model identifier in format "provider:model_name"
        base_url (str, optional): Base URL for the API
        api_key (str, optional): API key for the provider
    
    Returns:
        JSON response indicating success or failure
    """
    data = request.json
    model = data.get('model')
    base_url = data.get('base_url')
    api_key = data.get('api_key')
    
    if not model:
        return jsonify({"error": "Model identifier is required"}), 400
    
    try:
        ai = get_interactor()
        ai._setup_client(model, base_url, api_key)
        ai._setup_encoding()
        
        return jsonify({
            "success": True, 
            "message": f"Switched to model {model}",
            "provider": ai.provider,
            "model": ai.model,
            "tools_supported": ai.tools_supported
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/context_length', methods=['GET'])
def get_context_length():
    """Get the currently configured maximum context length.
    
    Returns:
        JSON response with the current context length
    """
    ai = get_interactor()
    
    return jsonify({
        "context_length": ai.context_length
    })


@app.route('/api/context_length', methods=['POST'])
def set_context_length():
    """Set the maximum context length for the conversation.
    
    Request JSON parameters:
        context_length (int): The maximum context length in tokens
    
    Returns:
        JSON response with the updated context length
    """
    data = request.json
    context_length = data.get('context_length')
    
    if not context_length or not isinstance(context_length, int) or context_length <= 0:
        return jsonify({"error": "Valid context length (positive integer) is required"}), 400
    
    try:
        ai = get_interactor()
        ai.context_length = context_length
        
        return jsonify({
            "success": True,
            "message": f"Context length updated to {context_length} tokens",
            "context_length": ai.context_length
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_app(test_config=None):
    """Create and configure the Flask application.
    
    Args:
        test_config: Test configuration to use instead of the default configuration
        
    Returns:
        Flask application instance
    """
    if test_config:
        app.config.update(test_config)
    
    # Initialize the interactor
    get_interactor()
    
    return app


def run_api(host='127.0.0.1', port=5000, debug=False):
    """Run the API server.
    
    Args:
        host (str): Host to run the server on
        port (int): Port to run the server on
        debug (bool): Whether to run in debug mode
    """
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    run_api(debug=True)


# ----------------------------------------------------------------------
# Example curl commands for testing API functionality
# ----------------------------------------------------------------------

# Interact with the AI (non-streaming)
# Replace 'your message here' with your input text
# curl -X POST http://127.0.0.1:5000/api/interact -H "Content-Type: application/json" -d '{"message": "your message here", "stream": false}'

# Interact with the AI (streaming)
# curl -N -X POST http://127.0.0.1:5000/api/interact -H "Content-Type: application/json" -d '{"message": "hello"}'

# List available models
# curl http://127.0.0.1:5000/api/models

# Add a tool function dynamically
# curl -X POST http://127.0.0.1:5000/api/add_function -H "Content-Type: application/json" -d '{"module_path": "/path/to/your/module.py", "function_name": "your_function"}'

# Get registered functions
# curl http://127.0.0.1:5000/api/functions

# Set system prompt
# curl -X POST http://127.0.0.1:5000/api/system_prompt -H "Content-Type: application/json" -d '{"prompt": "You are a helpful assistant."}'

# Get conversation history
# curl http://127.0.0.1:5000/api/messages

# Add message to conversation history
# curl -X POST http://127.0.0.1:5000/api/messages -H "Content-Type: application/json" -d '{"role": "user", "content": "What is the weather today?"}'

# Clear conversation history
# curl -X DELETE http://127.0.0.1:5000/api/messages

# Get current model info
# curl http://127.0.0.1:5000/api/model

# Get interactor settings (excludes API keys)
# curl http://127.0.0.1:5000/api/settings

# Switch model (replace with actual values)
# curl -X POST http://127.0.0.1:5000/api/switch_model -H "Content-Type: application/json" -d '{"model": "openai:gpt-4", "api_key": "your_api_key"}'

# Get current context length
# curl http://127.0.0.1:5000/api/context_length

# Set context length
# curl -X POST http://127.0.0.1:5000/api/context_length -H "Content-Type: application/json" -d '{"context_length": 64000}'
