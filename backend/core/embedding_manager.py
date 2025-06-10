from transformers import AutoTokenizer, AutoModel
from adapters import AutoAdapterModel
import logging
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, model_name: str = "allenai/specter2", base_model_name: str = "allenai/specter2_base"):
        self.model_name = model_name
        self.base_model_name = base_model_name
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading tokenizer: {self.base_model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)

            logger.info(f"Loading AutoAdapterModel: {self.base_model_name} with adapter {self.model_name}")
            self.model = AutoAdapterModel.from_pretrained(self.base_model_name)
            self.model.load_adapter(self.model_name, source="hf", set_active=True)
            
            logger.info("Model and adapter loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {e}")
            raise

    def _get_model_output(self, texts: list[str]) -> np.ndarray:
        if not self.tokenizer or not self.model:
            raise RuntimeError("Model or tokenizer not loaded. Call _load_model first.")
        
        # Concatenate title and abstract for SPECTER2
        # Assuming texts are already processed as title + [SEP] + abstract
        inputs = self.tokenizer(texts, padding=True, truncation=True, 
                                return_tensors="pt", return_token_type_ids=False, max_length=512)
        
        # Ensure inputs are on the correct device if using GPU
        # For simplicity, keeping it on CPU for now as FAISS is CPU-based
        
        output = self.model(**inputs)
        # Take the first token (CLS token) in the batch as the embedding
        embeddings = output.last_hidden_state[:, 0, :].detach().numpy()
        return embeddings

    def get_embedding(self, text: str) -> np.ndarray:
        if not text:
            return np.array([]) # Return empty numpy array for empty text
        return self._get_model_output([text])[0] # Get the first embedding from the batch

    def get_embeddings(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([]) # Return empty numpy array for empty text
        return self._get_model_output(texts) 