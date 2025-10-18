
import pandas as pd
import json

from solanum.model import SolanumModel

test_clim_data = pd.read_csv('example/test_clim_data.csv')
with open('example/params.json', 'r') as f:
    params = json.load(f)

model = SolanumModel(test_clim_data, params, debug=False)
model.run_simulation() 
model.save_results_csv('example/test_results.csv')
