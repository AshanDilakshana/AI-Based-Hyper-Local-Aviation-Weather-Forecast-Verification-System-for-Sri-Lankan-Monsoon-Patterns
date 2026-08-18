import os
import sys

# Add project root to path to ensure preprocessing_and_feature_engineering can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from preprocessing_and_feature_engineering.pipeline import WeatherDataPipeline

class UnifiedWeatherPipeline(WeatherDataPipeline):
    """
    Wrapper subclass for the models directory structure.
    """
    def __init__(self):
        super().__init__()
