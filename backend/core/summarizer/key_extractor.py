from .key_extractor_impl import KeyExtractorImpl

class KeyExtractor:
    def __init__(self):
        self.impl = KeyExtractorImpl()
        
    def extract(self, paper_data):
        return self.impl.extract(paper_data)
