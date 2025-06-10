import faiss
import numpy as np
import logging
import os
from typing import List, Tuple
from datetime import datetime

from .paper_database import PaperDatabase
from .embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)

class FAISSManager:
    def __init__(self, db_path: str = "arxiv_papers.db", index_path: str = "arxiv_papers.faiss"):
        self.db_path = db_path
        self.index_path = index_path
        self.paper_db = PaperDatabase()
        self.embedding_manager = EmbeddingManager()
        self.index = None
        self.paper_ids = [] # To map FAISS index to paper IDs
        self._load_or_build_index()

    def _load_or_build_index(self):
        if os.path.exists(self.index_path):
            logger.info(f"Loading FAISS index from {self.index_path}")
            self.index = faiss.read_index(self.index_path)
            # Load paper_ids alongside index (assuming it's saved separately)
            # For simplicity, let's just rebuild for now if no separate paper_ids file.
            # In a real scenario, paper_ids should be persisted with the index.
            logger.warning("FAISS index loaded, but paper_ids are NOT loaded. Rebuilding index to ensure consistency.")
            self._build_index()
        else:
            logger.info(f"FAISS index not found. Building new index at {self.index_path}")
            self._build_index()

    def _build_index(self):
        papers = self.paper_db.get_papers_by_date_range(datetime.min, datetime.max, limit=None) # Get all papers
        embeddings = []
        self.paper_ids = []

        for paper in papers:
            if paper.embedding is not None:
                embeddings.append(paper.embedding)
                self.paper_ids.append(paper.paper_id)
        
        if not embeddings:
            logger.warning("No embeddings found in the database to build FAISS index.")
            self.index = None
            return

        embeddings = np.array(embeddings).astype('float32')
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dimension) # Using IndexFlatL2 for simplicity (exact search)
        # For IVF-PQ (approximate search), more setup is needed:
        # nlist = 100 # Number of clusters
        # m = 8 # Number of bytes per vector
        # self.index = faiss.IndexIVFPQ(index_factory_method(dimension, nlist, m), dimension, nlist, m)
        # self.index.train(embeddings)

        self.index.add(embeddings)
        faiss.write_index(self.index, self.index_path)
        logger.info(f"FAISS index built and saved to {self.index_path} with {len(self.paper_ids)} papers.")

    def search_papers(self, query_text: str, k: int = 10) -> List[Tuple[str, float]]:
        if self.index is None:
            logger.warning("FAISS index not available. Cannot perform search.")
            return []

        query_embedding = self.embedding_manager.get_embedding(query_text)
        if query_embedding is None or query_embedding.size == 0:
            logger.warning("Failed to generate embedding for query text.")
            return []

        query_embedding = np.array([query_embedding]).astype('float32')

        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.paper_ids):
                results.append((self.paper_ids[idx], distances[0][i]))
            else:
                logger.warning(f"Invalid index {idx} found in FAISS search results. Skipping.")
        return results

    def rebuild_index(self):
        logger.info("Rebuilding FAISS index...")
        self._build_index()

from datetime import datetime 