#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: memory.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-26 17:33:07
# Modified: 2025-03-26 20:54:27

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
        """Return a proper ISO8601 UTC timestamp string using timezone-aware datetime."""
        if unix_ts is None:
            unix_ts = time.time()
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_embedding(self, text: str):
        return self.embedder.encode(text, convert_to_numpy=True, normalize_embeddings=True)

    def persist(self):
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, "w") as f:
            json.dump(self.metadata, f)

    def _segment_text(self, text: str, block_size: int = 500, overlap: int = 50):
        blocks = []
        start = 0
        while start < len(text):
            block = text[start: start + block_size]
            blocks.append(block)
            start += (block_size - overlap)
        return blocks

    def create(self, memory_obj):
        if isinstance(memory_obj, str):
            cleaned = re.sub(r'\s+', ' ', memory_obj).strip()
            human_timestamp = self._get_human_timestamp()
            enriched = f"[{human_timestamp}] {cleaned}"
            blocks = self._segment_text(enriched)
            for block in blocks:
                self.create({"content": block})
            return

        if "timestamp" not in memory_obj:
            memory_obj["timestamp"] = time.time()
        human_timestamp = self._get_human_timestamp(memory_obj["timestamp"])
        content = memory_obj.get("content", "")
        content = re.sub(r'\s+', ' ', content).strip()
        if not content:
            print(f"Skipping entry with empty content: {json.dumps(memory_obj)[:50]}...")
            return
        if not content.startswith("["):
            content = f"[{human_timestamp}] {content}"
            memory_obj["content"] = content

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

    def search(self, query: str, limit: int = 3):
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


    def import_text(self, file_path: str, block_size: int = 500, overlap: int = 50):
        """
        Import an unstructured text file (e.g., a book), clean up whitespace,
        split into blocks, prepend timestamps to each block, and batch index them.
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
        memory.import_text(text_file)
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
        ai.set_system(system_prompt)

        # Send user query to AI assistant 
        ai_response = ai.interact(user_input=user_input, tools=False, stream=True)
        print()

        # Add response to your memories
        #memory.add(f"assistant: {ai_response}")
