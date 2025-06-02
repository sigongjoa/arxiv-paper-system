from .script_generator_impl import ScriptGeneratorImpl

class LocalLLMClient:
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.impl = ScriptGeneratorImpl(base_url)
        
    def generate_script(self, summary_data, paper_data):
        return self.impl.generate_script(summary_data, paper_data)
