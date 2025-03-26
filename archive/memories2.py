#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: memories.py
# Author: Wadih Khairallah (updated by Grok 3)
# Description: Enhanced memory module with real embeddings and efficient DB management
# Created: 2025-03-25 15:45:59
# Modified: 2025-03-25 (by original author), updated 2025-03-25 (by Grok 3)

import os
import sys
import time
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer  # For real embeddings
from interactor import Interactor  # Your provided interactor module

class Memory:
    def __init__(self, db: str):
        """
        Initialize the FAISS memory module with a real embedding model.
        Loads existing FAISS index and metadata if available, otherwise creates new ones.
        """
        self.db = db
        self.index_file = os.path.join(db, "index.faiss")
        self.meta_file = os.path.join(db, "metadata.json")
        self.embedding_dim = 384  # Dimension for 'all-MiniLM-L6-v2' model

        # Ensure the database directory exists
        if not os.path.exists(db):
            os.makedirs(db)

        # Load the embedding model (only once during initialization)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Load or create the FAISS index
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

        # Load metadata mapping from disk, or initialize an empty list
        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = []

    def get_embedding(self, text: str):
        """
        Generate a real embedding for the given text using SentenceTransformer.
        Returns a numpy array of shape (embedding_dim,).
        """
        return self.embedder.encode(text, convert_to_numpy=True, normalize_embeddings=True)

    def persist(self):
        """Persist the FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, "w") as f:
            json.dump(self.metadata, f)

    def create(self, memory_obj: dict):
        """
        Create a new memory entry.
        If no timestamp is provided, the current Unix time is added.
        The entry is embedded and added to the FAISS index, and metadata is saved.
        """
        if "timestamp" not in memory_obj:
            memory_obj["timestamp"] = time.time()
        content = memory_obj.get("content", "")
        embedding = self.get_embedding(content)
        # FAISS expects a 2D numpy array of shape (1, embedding_dim)
        vec = np.array([embedding])
        self.index.add(vec)
        self.metadata.append(memory_obj)
        self.persist()

    def search(self, query: str, limit: int = 3):
        """
        Perform a semantic search on memories based on the query.
        Returns the top 'limit' memory entries.
        """
        query_embedding = self.get_embedding(query)
        vec = np.array([query_embedding])
        distances, indices = self.index.search(vec, limit)
        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self.metadata):
                results.append(self.metadata[idx])
        return {"results": results}

    def add(self, messages: list):
        """
        Store the conversation as a new memory entry.
        Combines messages into a single text block and adds to the database.
        """
        memory_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)
        memory_obj = {
            "role": "conversation",
            "content": memory_text,
            "timestamp": time.time()
        }
        self.create(memory_obj)

    def import_jsonl(self, file_path: str):
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return
        
        if os.path.exists(self.index_file) and os.path.exists(self.meta_file):
            print(f"Database already exists at {self.db}. Skipping import.")
            return

        print(f"Building memory database from {file_path}...")
        embeddings = []
        metadata = []
        total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))  # Count lines
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    memory_obj = json.loads(line.strip())
                    if "timestamp" not in memory_obj:
                        memory_obj["timestamp"] = time.time()
                    content = memory_obj.get("content", "")
                    embedding = self.get_embedding(content)
                    embeddings.append(embedding)
                    metadata.append(memory_obj)
                    if (i + 1) % 1000 == 0:  # Update every 1000 entries
                        print(f"Processed {i + 1}/{total_lines} entries ({(i + 1) / total_lines * 100:.1f}%)")
                except Exception as e:
                    print(f"Error parsing line {i + 1}: {line}\n{e}")

        if embeddings:
            vecs = np.array(embeddings).astype('float32')
            self.index.add(vecs)
            self.metadata.extend(metadata)
            self.persist()
            print(f"Imported {len(embeddings)} memories from {file_path}")
    
def chat_with_memories(message: str) -> str:
    """
    Chat function that retrieves relevant memories, interacts with the AI,
    and stores new memories efficiently.
    """
    memory = Memory(db="faiss_db")

    # Retrieve relevant memories based on the current message
    relevant_memories = memory.search(query=message, limit=20)

    memories_str = ""
    for entry in relevant_memories["results"]:
        memories_str += f"- {entry.get('content', '')}\n"

    print("Retrieved Memories:")
    print(memories_str)

    # Build the system prompt by including the retrieved memories
    system_prompt = (
        f"You are a helpful AI. Answer the question based on the query and memories below.\n"
        f"User Memories:\n{memories_str}"
    )

    # Instantiate the Interactor
    interactor = Interactor(model="openai:gpt-4o-mini")
    interactor.set_system(system_prompt)

    #message = f"{message}\n\nHere are some memories related to the query.\n```memories\n{memories_str}```"

    # Get the assistant response
    assistant_response = interactor.interact(user_input=message, tools=False, stream=True)

    # Save the conversation to memory for future context
    conversation_messages = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": assistant_response}
    ]
    memory.add(conversation_messages)

    return assistant_response

if __name__ == "__main__":
    # Handle command-line arguments for importing JSONL file
    if len(sys.argv) > 2 and sys.argv[1] == "import_jsonl":
        jsonl_file = sys.argv[2]
        memory = Memory(db="faiss_db")
        memory.import_jsonl(jsonl_file)
        sys.exit(0)

    print("Chat with AI using FAISS memory (type 'exit' to quit):")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        response = chat_with_memories(user_input)
        print(f"AI: {response}\n")
