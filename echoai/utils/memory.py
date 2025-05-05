#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: memory.py
# Author: Wadih Khairallah
# Description: Vector-based memory system for storing and retrieving text content using FAISS
# Created: 2025-03-26 17:33:07
# Modified: 2025-05-05 19:07:41

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import time
import json
import re
import hashlib
import numpy as np
import faiss
from datetime import datetime, timezone
from sentence_transformers import SentenceTransformer
from rich.console import Console

console = Console()
print = console.print
log = console.log

class Memory:
    def __init__(
        self,
        db: str,
        model_name: str = "all-MiniLM-L6-v2",
        min_chars: int = 80,
        min_sentences: int = None
    ):
        """
        Initialize the Memory system with vector storage and metadata.
        
        Args:
            db (str): Path to the database directory
            model_name (str): Name of the sentence transformer model (default: all-MiniLM-L6-v2)
            min_chars (int): Minimum characters for useful memory (default: 80)
            min_sentences (int): Minimum sentences for useful memory (default: None)
        """
        self.db = os.path.expanduser(db)
        self.index_file = os.path.join(self.db, "index.faiss")
        self.meta_file = os.path.join(self.db, "metadata.json")

        model_dims = {
            "all-MiniLM-L6-v2": 384,
            "all-MiniLM-L12-v2": 384,
            "multi-qa-MiniLM-L6-cos-v1": 384,
            "all-distilroberta-v1": 768,
            "all-mpnet-base-v2": 768
        }
        self.embedding_dim = model_dims.get(model_name, 384)

        self.min_chars = min_chars
        self.min_sentences = min_sentences

        if not os.path.exists(self.db):
            os.makedirs(self.db)

        self.embedder = SentenceTransformer(model_name)

        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r") as f:
                self.metadata = json.load(f)
            self.content_hashes = {self._hash_content(m.get("content", "")) for m in self.metadata}
        else:
            self.metadata = []
            self.content_hashes = set()

    def _get_human_timestamp(self, unix_ts: float = None) -> str:
        """
        Convert Unix timestamp to ISO8601 UTC format.
        
        Args:
            unix_ts (float, optional): Unix timestamp. If None, uses current time
            
        Returns:
            str: ISO8601 formatted timestamp
        """
        if unix_ts is None:
            unix_ts = time.time()
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    def _hash_content(self, content: str) -> str:
        """
        Create SHA256 hash of content string.
        
        Args:
            content (str): Content to hash
            
        Returns:
            str: Hexadecimal hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_embedding(self, text: str):
        """
        Generate embedding vector for input text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            numpy.ndarray: Normalized embedding vector
        """
        return self.embedder.encode(text, convert_to_numpy=True, normalize_embeddings=True)

    def persist(self):
        """Save the current state of the index and metadata to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, "w") as f:
            json.dump(self.metadata, f)

    def _segment_text(self, text: str, block_size: int = 500, overlap: int = 50):
        """
        Split text into overlapping blocks.
        
        Args:
            text (str): Text to segment
            block_size (int): Size of each block in characters (default: 500)
            overlap (int): Number of overlapping characters between blocks (default: 50)
            
        Returns:
            list: List of text blocks
        """
        blocks = []
        start = 0
        while start < len(text):
            block = text[start: start + block_size]
            blocks.append(block)
            start += (block_size - overlap)
        return blocks

    def create(self, memory_obj):
        """
        Create new memory entry and add to index.
        
        Args:
            memory_obj: String content or dictionary with memory data
        """
        #print("Creating memory.")
        if isinstance(memory_obj, str):
            cleaned = re.sub(r'\s+', ' ', memory_obj).strip()
            human_timestamp = self._get_human_timestamp()
            enriched = f"[{human_timestamp}] {cleaned}"
            blocks = self._segment_text(enriched)
            for block in blocks:
                self.create({"content": block})
            return { "status": "success", "content": memory_obj }

        if "timestamp" not in memory_obj:
            memory_obj["timestamp"] = time.time()
        human_timestamp = self._get_human_timestamp(memory_obj["timestamp"])
        content = memory_obj.get("content", "")
        content = re.sub(r'\s+', ' ', content).strip()
        if not content:
            print(f"Skipping entry with empty content: {json.dumps(memory_obj)[:50]}...")
            return { "status": "failed", "result": "Entry has empty content." } 
        if not content.startswith("["):
            content = f"[{human_timestamp}] {content}"
            memory_obj["content"] = content

        content_hash = self._hash_content(content)
        if content_hash in self.content_hashes:
            print(f"Skipping duplicate entry: {content[:50]}...")
            return { "status": "failed", "result": "Duplicate memory entry." }

        embedding = self.get_embedding(content)
        vec = np.array([embedding])
        self.index.add(vec)
        self.metadata.append(memory_obj)
        self.content_hashes.add(content_hash)
        self.persist()

        return "Memory successfully updated."

    def _is_useful_memory(self, text: str) -> bool:
        """
        Determine if a memory text is useful based on configured minimum characters or sentences.
        
        Args:
            text (str): The text content to evaluate
            
        Returns:
            bool: True if the text meets the minimum criteria, False otherwise
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
            return True

    def search(self, query: str, limit: int = 5):
        """
        Search for relevant memories using vector similarity.
        
        Args:
            query (str): The search query text
            limit (int): Maximum number of results to return (default: 3)
            
        Returns:
            dict: Dictionary containing search results with memory objects
        """
        #print("Searching memory.")
        query_embedding = self.get_embedding(query)
        vec = np.array([query_embedding])
        distances, indices = self.index.search(vec, limit)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                memory_obj = self.metadata[idx]
                content = memory_obj.get("content", "")
                distance = float(distances[0][i])
                memory_obj["distance"] = distance
                memory_obj["score"] = 1 / (1 + distance)
                results.append(memory_obj)
                #if self._is_useful_memory(content):
                #    results.append(memory_obj)
        return {
                "status": "success",
                "query": query,
                "results": results
            }

    def add(self, obj):
        """
        Add new memory entries to the database.
        
        Args:
            obj: Memory content to add, can be:
                - str: Text content that will be timestamped and segmented
                - list: List of message objects with role and content
                - dict: Memory object with content field
                
        Raises:
            ValueError: If obj is not a string, list, or dict
        """
        if isinstance(obj, str):
            cleaned = re.sub(r'\s+', ' ', obj).strip()
            human_timestamp = self._get_human_timestamp()
            enriched = f"[{human_timestamp}] {cleaned}"
            blocks = self._segment_text(enriched)
            for block in blocks:
                self.create({"content": block})
        elif isinstance(obj, list):
            memory_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in obj)
            self.create({"content": memory_text})
        elif isinstance(obj, dict):
            self.create(obj)
        else:
            raise ValueError("Invalid type for add: expected string, list, or dict.")

    def import_text(self, text: str, block_size: int = 500, overlap: int = 50):
        """
        Import and process plain text into memory blocks.
        
        Args:
            text (str): The raw text string to import
            block_size (int): Size of each text block in characters (default: 500)
            overlap (int): Number of overlapping characters between blocks (default: 50)
        """
        text = re.sub(r'\s+', ' ', text).strip()
        blocks = self._segment_text(text, block_size, overlap)

        print(f"Processing {len(blocks)} blocks from text input...")

        new_blocks = []
        new_hashes = []

        for i, block in enumerate(blocks, 1):
            cleaned = re.sub(r'\s+', ' ', block).strip()
            if not cleaned:
                continue

            content_hash = self._hash_content(cleaned)
            if content_hash not in self.content_hashes:
                new_blocks.append(cleaned)
                new_hashes.append(content_hash)

            if i % 100 == 0 or i == len(blocks):
                percent = (i / len(blocks)) * 100
                print(f"Scanned {i}/{len(blocks)} blocks ({percent:.1f}%)")

        if new_blocks:
            enriched_blocks = []
            timestamps = []

            for text in new_blocks:
                unix_ts = time.time()
                human_ts = self._get_human_timestamp(unix_ts)
                enriched = f"[{human_ts}] {text}"
                enriched_blocks.append(enriched)
                timestamps.append(unix_ts)

            embeddings = self.embedder.encode(
                enriched_blocks, convert_to_numpy=True, normalize_embeddings=True
            )
            self.index.add(np.array(embeddings))

            for i, content in enumerate(enriched_blocks):
                self.metadata.append({
                    "timestamp": timestamps[i],
                    "content": content
                })
                self.content_hashes.add(self._hash_content(content))

            self.persist()

        print(f"\n✅ Import complete: {len(new_blocks)} new blocks added, "
              f"{len(blocks) - len(new_blocks)} duplicates skipped.\n")


    def import_file(self, file_path: str, block_size: int = 500, overlap: int = 50):
        """
        Import and process a text file into memory blocks.
        
        Args:
            file_path (str): Path to the text file to import
            block_size (int): Size of each text block in characters (default: 500)
            overlap (int): Number of overlapping characters between blocks (default: 50)
        """
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            corpus = f.read()

        corpus = re.sub(r'\s+', ' ', corpus).strip()
        blocks = self._segment_text(corpus, block_size, overlap)

        print(f"Processing {len(blocks)} blocks from {file_path}...")

        new_blocks = []
        new_hashes = []

        for i, block in enumerate(blocks, 1):
            cleaned = re.sub(r'\s+', ' ', block).strip()
            if not cleaned:
                continue

            content_hash = self._hash_content(cleaned)
            if content_hash not in self.content_hashes:
                new_blocks.append(cleaned)
                new_hashes.append(content_hash)

            if i % 100 == 0 or i == len(blocks):
                percent = (i / len(blocks)) * 100
                print(f"Scanned {i}/{len(blocks)} blocks ({percent:.1f}%)")

        if new_blocks:
            enriched_blocks = []
            timestamps = []

            for text in new_blocks:
                unix_ts = time.time()
                human_ts = self._get_human_timestamp(unix_ts)
                enriched = f"[{human_ts}] {text}"
                enriched_blocks.append(enriched)
                timestamps.append(unix_ts)

            embeddings = self.embedder.encode(
                enriched_blocks, convert_to_numpy=True, normalize_embeddings=True
            )
            self.index.add(np.array(embeddings))

            for i, content in enumerate(enriched_blocks):
                self.metadata.append({
                    "timestamp": timestamps[i],
                    "content": content
                })
                self.content_hashes.add(self._hash_content(content))

            self.persist()

        print(f"\n✅ Import complete: {len(new_blocks)} new blocks added, "
              f"{len(blocks) - len(new_blocks)} duplicates skipped.\n")


if __name__ == "__main__":
    """Example usage for using RAG memories."""
    from interactor import Interactor
    db_path = os.path.expanduser("~/.echoai/echoai_db")
    memory = Memory(db=db_path)
    ai = Interactor(model="openai:gpt-4o-mini")

    if len(sys.argv) > 2 and sys.argv[1] == "import":
        text_file = sys.argv[2]
        memory = Memory(db=db_path, model_name="all-MiniLM-L6-v2")
        memory.import_file(text_file)
        sys.exit(0)

    print("Chat with AI using FAISS memory (type 'exit' to quit):")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Retrieve memories
        relevant_memories = memory.search(query=user_input, limit=10)
        memories_str = ""
        for entry in relevant_memories["results"]:
            memories_str += f"- {entry.get('content', '')}\n"

        log(f"Retrieved Memories:\n{memories_str}")

        # Add user query to memories
        #memory.add(f"user: {user_input}")

        # Add memories to your system prompt.
        system_prompt = (
            f"You are a helpful AI. Answer the question based on the query and memories below.\n"
            f"User Memories:\n{memories_str}"
        )
        ai.messages_system(system_prompt)

        # Send user query to AI assistant 
        ai_response = ai.interact(user_input=user_input, tools=False, stream=True)
        print()

        # Add response to your memories
        #memory.add(f"assistant: {ai_response}")
