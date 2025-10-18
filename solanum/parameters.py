
import pandas as pd
import numpy as np

class SolanumParameterProcessor:
    
    def __init__(self, params):
        self.raw_params = params
        self.processed_params = {}
        self._extract_parameters()
        self._calculate_derived_parameters()
        # self._validate_parameters()
    
    def _extract_parameters(self):
        
        self.processed_params['phenology'] = {
            'sowing': self.raw_params['sowing'],
            'harvest': self.raw_params['harvest'], 
            'EDay': self.raw_params['EDay'],
            'time_duration': None
        }
        
        self.processed_params['growth'] = {
            'plantDensity': self.raw_params['plantDensity'],
            'wmax': self.raw_params['wmax'],
            'tm': self.raw_params['tm'],
            'te': self.raw_params['te'],
            'A': self.raw_params['A'],
            'tu': self.raw_params['tu'],
            'b': self.raw_params['b'],
            'RUE': self.raw_params['RUE'],
            'DMCont': self.raw_params['DMCont']
        }
        
        self.processed_params['temperature'] = {
            'Tb': self.raw_params['Tb'],
            'To': self.raw_params['To'],
            'Tu': self.raw_params['Tu'],
            'Tcr': self.raw_params['Tcr'],
            'Tld': self.raw_params['Tld'],
            'Trg': self.raw_params['Trg']
        }
        
        self.processed_params['photoperiod'] = {
            'Pc': self.raw_params['Pc'],
            'w': self.raw_params['w']
        }
        
        self.processed_params['soil_water'] = {
            'Soil_depth': self.raw_params['Soil_depth'],
            'fc': self.raw_params['FC'] ,
            'wp': self.raw_params['WP'] ,
            'ism': self.raw_params['ISM'] 
        }
        
        self.processed_params['environment'] = {
            'CO2AirConcent': self.raw_params['CO2AirConcent'],
            'useRefIrri': self.raw_params['useRefIrri']
        }
        
        self.processed_params['simulation'] = {
            'numrep': self.raw_params['numrep']
        }
    
    def _calculate_derived_parameters(self):
        
        sowing_date = pd.to_datetime(self.processed_params['phenology']['sowing'])
        harvest_date = pd.to_datetime(self.processed_params['phenology']['harvest'])
        time_duration = (harvest_date - sowing_date).days + 1
        self.processed_params['phenology']['time_duration'] = time_duration
        
        soil_params = self.processed_params['soil_water']
        soil_params['cl'] = soil_params['fc'] - 0.5 * (soil_params['fc'] - soil_params['wp'])
        
        soil_vol = 10000 * soil_params['Soil_depth']
        soil_params['Soil_Vol'] = soil_vol
        soil_params['FC'] = (soil_vol * soil_params['fc']) / 1000
        soil_params['CL'] = (soil_vol * soil_params['cl']) / 1000
        soil_params['WP'] = (soil_vol * soil_params['wp']) / 1000
        soil_params['ISM'] = (soil_vol * soil_params['ism']) / 1000
        
        growth_params = self.processed_params['growth']
        growth_params['t50'] = self._bisection(
            growth_params['te'], 
            growth_params['te'] + 1000,
            growth_params['wmax'],
            growth_params['te'],
            growth_params['tm']
        )
        growth_params['d'] = growth_params['t50'] - growth_params['te']
        
        temp_params = self.processed_params['temperature']
        temp_params['a'] = (np.log(2)) / np.log((temp_params['Tu'] - temp_params['Tb']) / 
                                                (temp_params['To'] - temp_params['Tb']))
        
        co2_concent = self.processed_params['environment']['CO2AirConcent']
        if co2_concent < 330:
            co2_effect = 0.0031 * co2_concent + 0.0093
        elif co2_concent < 880:
            co2_effect = 0.0007 * co2_concent + 0.79
        else:
            co2_effect = 0.000008 * co2_concent + 1.4223
        
        self.processed_params['environment']['co2_effect'] = round(co2_effect, 1)
    
    def _fx50(self, x, wmax, te, tm):
        return 0.5 - wmax * (1 + (te - x) / (te - tm)) * ((x / te) ** (te / (te - tm)))
    
    def _bisection(self, a, b, wmax, te, tm):
        x = b
        d = (a + b) / 2.0
        
        while True:
            if abs(x - d) / abs(x) < 1e-12:
                break
            if self._fx50(x, wmax, te, tm) == 0.0:
                break
            
            valor1 = self._fx50(x, wmax, te, tm)
            valor2 = self._fx50(a, wmax, te, tm)
            
            if valor1 * valor2 < 0:
                b = x
            else:
                a = x
                
            d = x
            x = (a + b) / 2.0
            
        return x
    
    def get_parameters(self):
        return self.processed_params
    
    def print_summary(self):
        print("=" * 60)
        print("SOLANUM MODEL PARAMETER SUMMARY")
        print("=" * 60)
        
        for category, params in self.processed_params.items():
            print(f"\n{category.upper().replace('_', ' ')} PARAMETERS:")
            print("-" * 40)
            for key, value in params.items():
                if isinstance(value, float):
                    print(f"  {key:15}: {value:8.3f}")
                else:
                    print(f"  {key:15}: {value}")