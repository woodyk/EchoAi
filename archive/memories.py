#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: memories.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-25 15:45:59
# Modified: 2025-03-25 17:21:23

import os
import sys
import time
import json
import numpy as np
import faiss
from interactor import Interactor  # Your provided interactor module

class Memory:
    def __init__(self, db: str):
        """
        Initialize the FAISS memory module.
        Loads an existing FAISS index and metadata from the given directory if available,
        otherwise creates new ones.
        """
        self.db = db
        self.index_file = os.path.join(db, "index.faiss")
        self.meta_file = os.path.join(db, "metadata.json")
        self.embedding_dim = 1536  # Set according to your embedding model's dimensions

        # Ensure the database directory exists
        if not os.path.exists(db):
            os.makedirs(db)

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
        Generate a dummy embedding for the given text.
        Replace this function with an actual embedding model as needed.
        """
        # For testing, we use a deterministic dummy embedding based on the text hash.
        np.random.seed(abs(hash(text)) % (2**32))
        return np.random.rand(self.embedding_dim).astype("float32")

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
        # Append the memory object to the metadata list
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
        Combines messages into a single text block.
        """
        memory_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)
        memory_obj = {
            "role": "conversation",
            "content": memory_text,
            "timestamp": time.time()
        }
        self.create(memory_obj)
    
    def import_jsonl(self, file_path: str):
        """
        Import memories from a JSONL file.
        Each line in the file should be a JSON object with "role" and "content" keys.
        """
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    memory_obj = json.loads(line.strip())
                    # Ensure the memory has a timestamp
                    if "timestamp" not in memory_obj:
                        memory_obj["timestamp"] = time.time()
                    self.create(memory_obj)
                except Exception as e:
                    print(f"Error parsing line: {line}\n{e}")

def chat_with_memories(message: str) -> str:
    """
    Chat function that retrieves relevant memories, interacts with the AI,
    and stores new memories. This uses FAISS as the local memory store.
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

    # Instantiate the Interactor (your interact() function from interactor.py)
    interactor = Interactor(model="openai:gpt-4o-mini")
    interactor.set_system(system_prompt)

    message = f"{message}\n\nHere are some memories related to the query.\n```memories\n{memories_str}```"

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
    # If command-line arguments are provided for importing JSONL file, do that and exit.
    if len(sys.argv) > 2 and sys.argv[1] == "import_jsonl":
        jsonl_file = sys.argv[2]
        memory = Memory(db="faiss_db")
        memory.import_jsonl(jsonl_file)
        print(f"Imported memories from {jsonl_file}")
        sys.exit(0)

    print("Chat with AI using FAISS memory (type 'exit' to quit):")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        response = chat_with_memories(user_input)
        print("\n")

