"""Ingestion module for data loading, chunking, and embedding"""
from .loader import ProductLoader
from .chunker import TextChunker
from .embedder import Embedder

__all__ = ['ProductLoader', 'TextChunker', 'Embedder']
