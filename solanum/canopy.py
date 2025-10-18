import pandas as pd
import numpy as np

class SolanumCanopyGrowth:

    def __init__(self, params):
        self.params = params

    def calculate_canopy_cover(self, tt, plant_density, variability=0.0):
        gp = self.params['growth']
        wmax, tm, te = gp['wmax'], gp['tm'], gp['te']
        if tt <= 0:
            return 0.0
        try:
            exp1 = np.exp(-tm/(tt*plant_density))
            fac1 = 1 + (te-tt)/(te-tm)
            exp2 = (tt/te)**(te/(te-tm))
            canopy = wmax * exp1 * fac1 * exp2
            canopy = variability*canopy + canopy
            return max(0.0, min(canopy, wmax))
        except:
            return 0.0

    def calculate_harvest_index(self, tt, cum_heat_stress):
        gp = self.params['growth']
        A, tu, b = gp['A'], gp['tu'], gp['b']
        # tu2 = (tt + b)/tu
        # part1 = A*np.exp(-np.exp(- (tt-tu)/b))
        # part2 = A*np.exp(-np.exp(- (tt-tu*tu2)/b))
        # hi = part1 if tu2<=1 else part2
        hi = A * np.exp(-np.exp(-(tt - tu) / b))
        # return max(0.0, min(hi*(300-cum_heat_stress)/300, 1.0))
        return hi

    def calculate_effective_rue(self, base_rue, tt, tav, co2_effect=1.0, water_stress=0.0):
        te = self.params['growth']['te']
        if tav>=25:
            rue_t = base_rue*(0.992-0.0193*tav)
        else:
            rue_t = base_rue
        rue_w = rue_t if tt<te else rue_t
        if water_stress>0:
            rue_w = max(0.0, (rue_w*(0.8-water_stress))/0.8)
        return max(0.0, rue_w*co2_effect)

    def calculate_effective_hi(self, HI, water_stress, threshold=0.8):
       return max(0.0, HI * (threshold - water_stress) / threshold)

    def calculate_biomass_increment(self, par, canopy_cover, rue_eff):
        return (par*canopy_cover*rue_eff)/100.0 if canopy_cover>0 and rue_eff>0 else 0.0