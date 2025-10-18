import pandas as pd
import numpy as np

class SolanumWaterBalance:

    def __init__(self, params):
        self.params = params
        sp = params['soil_water']
        self.FC = sp['FC']
        self.WP = sp['WP']
        self.CL = sp['CL']
        self.ISM = sp['ISM']
        self.wmax = params['growth']['wmax']

    def calculate_potential_transpiration(self, eto, canopy_cover):
        if canopy_cover <= 0:
            return 0.0001
        d001 = np.exp(-0.7 * 4 * canopy_cover)
        if d001 == 1:
            return 0.0001
        t0 = (self.wmax * eto * (1 - np.exp(-0.7 * 4 * canopy_cover))
              ) / (1 - np.exp(-0.7 * 4 * self.wmax))
        return max(0.0001, t0)

    def calculate_potential_soil_evaporation(self, eto, pot_transp):
        return max(0.0, eto - pot_transp)

    def calculate_actual_transpiration(self, pot_transp, avail_water):
        if avail_water < self.WP:
            return 0.0
        if avail_water <= self.CL:
            rf = (self.WP - avail_water)/(self.WP - self.CL)
            return max(0.0, pot_transp * rf)
        return max(0.0, pot_transp)

    def calculate_water_stress_factor(self, actual_transp, pot_transp):
        if pot_transp <= 0:
            return 0.0
        if actual_transp > 0.5 * pot_transp:
            return 0.0
        return (0.5 * pot_transp - actual_transp) / pot_transp

    def calculate_canopy_cover_water_limited(self, cum_water_stress, canopy_pot):
        if cum_water_stress > 75:
            return 0.0
        return ((75 - cum_water_stress) / 75) * canopy_pot

    def update_soil_water_balance(self, curr_water, precip, irri, soil_evap, transp):
        water_in = precip + irri
        water_out = soil_evap + transp
        new_water = curr_water + water_in - water_out
        
        # print(f"new_water: {new_water:.3f}")
        
        if new_water <= self.WP:
            final = self.WP
            run = 0.0
        elif new_water >= self.FC:
            final = self.FC
            run = new_water - self.FC
        else:
            final = new_water
            run = 0.0
        irrigation_need = max(0.0, self.FC - final) if final <= self.CL else 0.0
        return final, irrigation_need