import pandas as pd
import numpy as np

class SolanumStressCalculator:

    def __init__(self, params):
        self.params = params

    def calculate_temperature_index(self, tav):
        Tb, To, Tu = (self.params['temperature'][k] for k in ('Tb','To','Tu'))
        a = self.params['temperature']['a']
        if tav < Tb or tav > Tu:
            return 0.0
        num = 2 * ((tav - Tb)**a) * ((To - Tb)**a) - ((tav - Tb)**(2*a))
        den = (To - Tb)**(2*a)
        return num/den

    def calculate_photoperiod_index(self, photoperiod):
        Pc = self.params['photoperiod']['Pc']
        w  = self.params['photoperiod']['w']
        return np.exp(-w*(photoperiod-Pc)) if photoperiod>Pc else 1.0

    def calculate_heat_stress(self, tav):
        return 1.0 if tav<=20 else 0.0 if tav>=35 else -0.0667*tav+2.3333

    def calculate_thermal_correction_factor(self, tav):
        return 0.992 - 0.0193*tav

    def calculate_frost_stress_factors(self, tmin):
        Tcr = self.params['temperature']['Tcr']
        Tld = self.params['temperature']['Tld']
        Trg = self.params['temperature']['Trg']
        if tmin<Tld:
            ccl=1.0
        elif tmin<Tcr:
            ccl=1.0-(Tld-tmin)/(Tld-Tcr)
        else:
            ccl=0.0
        if tmin<=Trg:
            rf=0.0
        elif tmin< Tcr:
            rf=(Trg-tmin)/(Trg-Tcr)
        else:
            rf=1.0
        return ccl, rf