#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: memory.py
# Author: Wadih Khairallah
# Description: Enhanced memory module with real embeddings, appending, deduplication, 
#              and optional filtering of recalled memories based on length.
# Created: 2025-03-25 18:58:03
# Modified: 2025-03-25 20:25:50

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Disable parallelism to avoid tokenizers warnings

import sys
import time
import json
import hashlib
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from interactor import Interactor  # Your provided interactor module

class Memory:
    def __init__(
        self,
        db: str,
        model_name: str = "all-MiniLM-L6-v2",
        min_chars: int = 80,
        min_sentences: int = None
    ):
        """
        Initialize the FAISS memory module with a real embedding model.
        Loads existing FAISS index and metadata if available, otherwise creates new ones.
        
        Optional filtering:
          - If min_chars is set, only memories with at least that many characters
            will be returned during search.
          - If min_sentences is set, only memories with at least that many sentences
            will be returned.
          - If both are set, a memory is considered useful if either condition is met.
        
        The 'db' path is expanded using os.path.expanduser so that '~/path' works.
        """
        self.db = os.path.expanduser(db)
        self.index_file = os.path.join(self.db, "index.faiss")
        self.meta_file = os.path.join(self.db, "metadata.json")

        # Set embedding dimension based on model
        model_dims = {
            "all-MiniLM-L6-v2": 384,
            "all-MiniLM-L12-v2": 384,
            "multi-qa-MiniLM-L6-cos-v1": 384,
            "all-distilroberta-v1": 768,
            "all-mpnet-base-v2": 768
        }
        self.embedding_dim = model_dims.get(model_name, 384)  # Default to 384 if unknown

        # Optional filtering parameters
        self.min_chars = min_chars
        self.min_sentences = min_sentences

        # Ensure the database directory exists
        if not os.path.exists(self.db):
            os.makedirs(self.db)

        # Load the embedding model
        self.embedder = SentenceTransformer(model_name)

        # Load or create the FAISS index
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

        # Load metadata and build content hash set for deduplication
        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r") as f:
                self.metadata = json.load(f)
            self.content_hashes = {self._hash_content(m.get("content", "")) for m in self.metadata}
        else:
            self.metadata = []
            self.content_hashes = set()

    def _hash_content(self, content: str) -> str:
        """Generate a SHA-256 hash of the content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_embedding(self, text: str):
        """
        Generate a real embedding for the given text using SentenceTransformer.
        """
        return self.embedder.encode(text, convert_to_numpy=True, normalize_embeddings=True)

    def persist(self):
        """Persist the FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, "w") as f:
            json.dump(self.metadata, f)

    def create(self, memory_obj: dict):
        """
        Create a new memory entry if it’s not a duplicate and content is non-empty.
        """
        if "timestamp" not in memory_obj:
            memory_obj["timestamp"] = time.time()
        content = memory_obj.get("content", "")

        # Skip if content is None or empty string
        if content is None or content == "":
            print(f"Skipping entry with null or empty content: {json.dumps(memory_obj)[:50]}...")
            return

        content_hash = self._hash_content(content)

        if content_hash in self.content_hashes:
            print(f"Skipping duplicate entry: {content[:50]}...")
            return

        embedding = self.get_embedding(content)
        vec = np.array([embedding])
        self.index.add(vec)
        self.metadata.append(memory_obj)
        self.content_hashes.add(content_hash)
        self.persist()

    def _is_useful_memory(self, text: str) -> bool:
        """
        Determine if a memory's content is useful based on configured filtering.

        - If only min_chars is set, content must be at least that many characters.
        - If only min_sentences is set, content must have at least that many sentences.
        - If both are set, content is useful if either condition is met.
        """
        text = text.strip()

        if self.min_chars is not None and self.min_sentences is None:
            return len(text) >= self.min_chars
        elif self.min_chars is None and self.min_sentences is not None:
            sentence_count = text.count('.') + text.count('?') + text.count('!')
            return sentence_count >= self.min_sentences
        elif self.min_chars is not None and self.min_sentences is not None:
            sentence_count = text.count('.') + text.count('?') + text.count('!')
            return len(text) >= self.min_chars or sentence_count >= self.min_sentences
        else:
            # No filtering configured
            return True


    def search(self, query: str, limit: int = 3):
        """
        Perform a semantic search on memories based on the query.
        Only returns memories that pass the usefulness filter.
        """
        query_embedding = self.get_embedding(query)
        vec = np.array([query_embedding])
        distances, indices = self.index.search(vec, limit)
        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self.metadata):
                memory_obj = self.metadata[idx]
                content = memory_obj.get("content", "")
                if self._is_useful_memory(content):
                    results.append(memory_obj)
        return {"results": results}

    def add(self, obj):
        """
        Flexible add() method:
         - If given a list, treat it as conversation messages and join them.
         - If given a dict, directly store it as a memory entry (alias of create()).
        """
        if isinstance(obj, list):
            memory_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in obj)
            memory_obj = {
                "role": "conversation",
                "content": memory_text,
                "timestamp": time.time()
            }
            self.create(memory_obj)
        elif isinstance(obj, dict):
            self.create(obj)
        else:
            raise ValueError("Invalid type for add: expected list or dict.")

    def import_jsonl(self, file_path: str, append: bool = True):
        """
        Import memories from a JSONL file with deduplication, skipping null or empty content.
        If append=True, adds non-duplicate entries to existing DB.
        If append=False, overwrites with new non-duplicate entries.
        """
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return

        db_exists = os.path.exists(self.index_file) and os.path.exists(self.meta_file)

        if db_exists and not append:
            print(f"Database exists at {self.db} and append=False. Overwriting with new import.")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
            self.content_hashes = set()
        elif db_exists and append:
            print(f"Appending new non-duplicate entries to existing database at {self.db}...")
        else:
            print(f"No existing database found. Building new database at {self.db}...")

        embeddings = []
        metadata = []
        duplicates_skipped = 0
        invalid_skipped = 0
        total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    memory_obj = json.loads(line.strip())
                    if "timestamp" not in memory_obj:
                        memory_obj["timestamp"] = time.time()
                    content = memory_obj.get("content", "")

                    # Skip if content is None or empty string
                    if content is None or content == "":
                        invalid_skipped += 1
                        print(f"Skipping line {i + 1} with null or empty content: {line.strip()}")
                        continue

                    content_hash = self._hash_content(content)

                    if content_hash in self.content_hashes:
                        duplicates_skipped += 1
                        continue

                    embedding = self.get_embedding(content)
                    embeddings.append(embedding)
                    metadata.append(memory_obj)
                    self.content_hashes.add(content_hash)

                    if (i + 1) % 1000 == 0:
                        print(f"Processed {i + 1}/{total_lines} entries ({(i + 1) / total_lines * 100:.1f}%), "
                              f"skipped {duplicates_skipped} duplicates, {invalid_skipped} invalid")
                except Exception as e:
                    print(f"Error parsing line {i + 1}: {line}\n{e}")
                    invalid_skipped += 1

        if embeddings:
            vecs = np.array(embeddings).astype('float32')
            self.index.add(vecs)
            self.metadata.extend(metadata)
            self.persist()
            print(f"Added {len(embeddings)} new unique memories from {file_path} "
                  f"(skipped {duplicates_skipped} duplicates, {invalid_skipped} invalid).")
            print(f"Total unique entries now: {len(self.metadata)}")
        else:
            print(f"No new unique entries added from {file_path} "
                  f"(all skipped: {duplicates_skipped} duplicates, {invalid_skipped} invalid).")

def chat_with_memories(message: str) -> str:
    """
    Chat function that retrieves relevant memories, interacts with the AI,
    and stores new memories with deduplication and content check.
    """
    db_path = "~/.echoai/echoai_db"
    memory = Memory(db=db_path)

    # Retrieve relevant memories based on the current message
    relevant_memories = memory.search(query=message, limit=10)

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


    """
    # Instantiate the Interactor
    interactor = Interactor(model="openai:gpt-4o-mini")
    #interactor = Interactor(model="ollama:llama3.2")
    interactor.set_system(system_prompt)

    # Get the assistant response
    assistant_response = interactor.interact(user_input=message, tools=False, stream=True)

    # Save the conversation to memory for future context
    conversation_messages = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": assistant_response}
    ]
    memory.add(conversation_messages)

    return assistant_response
    """
    return

if __name__ == "__main__":
    db_path = "~/.echoai/echoai_db"

    # Handle command-line arguments for importing JSONL file
    if len(sys.argv) > 2 and sys.argv[1] == "import_jsonl":
        jsonl_file = sys.argv[2]
        append = True
        if len(sys.argv) > 3 and sys.argv[3].lower() == "append_false":
            append = False
        memory = Memory(db=db_path, model_name="all-MiniLM-L6-v2")
        memory.import_jsonl(jsonl_file, append=append)
        sys.exit(0)

    print("Chat with AI using FAISS memory (type 'exit' to quit):")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        response = chat_with_memories(user_input)
        print("\n********************************************\n")

