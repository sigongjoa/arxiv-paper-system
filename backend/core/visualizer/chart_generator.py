from .chart_generator_impl import ChartGeneratorImpl

class ChartGenerator:
    def __init__(self):
        self.impl = ChartGeneratorImpl()
    
    def generate_performance_chart(self, data, output_path):
        return self.impl.generate_performance_chart(data, output_path)
