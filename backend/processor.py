from .processor_impl import ProcessorImpl

class PaperProcessor:
    def __init__(self):
        self.impl = ProcessorImpl()  # 이제 __init__ 메서드가 있음
        
    def process_arxiv_paper(self, arxiv_id):
        return self.impl.process_arxiv_paper(arxiv_id)
