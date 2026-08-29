# MLOps Plugins Directory
# Team members can drop their model retraining plugins here.
# Each plugin should define a function: `def retrain() -> tuple[bool, str, str]:`
# The function must return a tuple: (success_boolean, message, model_key)

from .mlops_retrainer_temperature import retrain_temperature_pressure
