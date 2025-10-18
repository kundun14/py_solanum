
import pandas as pd
import numpy as np

from solanum.parameters import SolanumParameterProcessor
from solanum.climate import SolanumClimateProcessor
from solanum.stress import SolanumStressCalculator
from solanum.canopy import SolanumCanopyGrowth
from solanum.water import SolanumWaterBalance

class SolanumModel:

    def __init__(self, climate_data, params, debug=False):
        self.debug = debug
        self.param_proc = SolanumParameterProcessor(params)
        self.params     = self.param_proc.get_parameters()
        self.climate_proc = SolanumClimateProcessor(climate_data, self.params)
        self.climate    = self.climate_proc.get_processed_climate()
        self.stress     = SolanumStressCalculator(self.params)
        self.canopy     = SolanumCanopyGrowth(self.params)
        self.water      = SolanumWaterBalance(self.params)

    def run_simulation(self):
        days = len(self.climate)
        states = self._init_states()
        records = {
            'FTYP': np.zeros(days),
            'FTYW': np.zeros(days),
            'CCw':  np.zeros(days),
            'HI_HS':np.zeros(days),
            'WS':   np.zeros(days),
            'RUEw': np.zeros(days),
            'ASWC': np.zeros(days),
            'ETC':  np.zeros(days),
            'HI_ws': np.zeros(days), #### OJO
        }
        for i in range(days):
            out = self._daily(i, states)
            for k, v in out.items():
                # Map 'T' key to 'ETC' output name
                records['ETC' if k=='T' else k][i] = v

        df = pd.DataFrame({
            'Date': self.climate['Date'],
            'Tmin': self.climate['Tmin'],
            'Tmax': self.climate['Tmax'],
            'TT':   self.climate['TT'],
            'ETo':  self.climate['ETo'],
            'Prec': self.climate['Prec'],
            'Rad':  self.climate['Rad'],
            'FTYP': records['FTYP'],
            'FTYW': records['FTYW'],
            'CCw':  records['CCw'],
            'HI_HS':records['HI_HS'],
            'RUEw': records['RUEw'],
            'ASWC': records['ASWC'],
            'WS':   records['WS'],
            'ETC':  records['ETC']
        })

        self.results = df  
        # return df
    
    def _init_states(self):
        return {
            'TDM':0.0, 'TDMw':0.0, 'TDMco2':0.0,
            'day':-1, 'DAE':0,
            'cHT':0.0, 'cWS':0.0,
            'reb':1.0, 'c1':0.0, 'c2':0.0,
            'soil': self.params['soil_water']['ISM'],
            'v': 0.0  # no random variability
        }

    def _daily(self, i, s):
        r = self.climate.iloc[i]
        tav = (r['Tmin'] + r['Tmax'])/2
        s['day'] += 1
        s['DAE'] = max(0, s['day'] - self.params['phenology']['EDay'])

        HS = self.stress.calculate_heat_stress(tav)
        s['cHT'] += HS

        canopy = self.canopy.calculate_canopy_cover(r['TT'], self.params['growth']['plantDensity'], s['v'])
        if s['DAE'] <= 0:
            canopy = 0.0
        ccl, rf = self.stress.calculate_frost_stress_factors(r['Tmin'])
        canopy = max(0.0, canopy + s['c2'] - s['c1'])

        t0 = self.water.calculate_potential_transpiration(r['ETo'], canopy)
        e0 = self.water.calculate_potential_soil_evaporation(r['ETo'], t0)

        if s['day'] > 0:
            irri = r.get('Irri', 0.0) if self.params['environment']['useRefIrri']==0 else 0.0
            s['soil'], _ = self.water.update_soil_water_balance(
                s['soil'], r['Prec'], irri,
                e0*0.5, t0*0.8
                # self.params['soil_water']['FC'],
                # self.params['soil_water']['WP']
            )

        actualT = self.water.calculate_actual_transpiration(t0, s['soil'])
        WS = self.water.calculate_water_stress_factor(actualT, t0)
        s['cWS'] += WS

        cw = self.water.calculate_canopy_cover_water_limited(s['cWS'], canopy)
        HI = self.canopy.calculate_harvest_index(r['TT'], s['cHT'])
        rue_w = self.canopy.calculate_effective_rue(
            self.params['growth']['RUE'], r['TT'], tav, 1.0, WS
        )
        
        par = r['Rad'] * 0.5

        inc_p = self.canopy.calculate_biomass_increment(
            par, canopy,
            self.canopy.calculate_effective_rue(self.params['growth']['RUE'], r['TT'], tav)
        )
        inc_w = self.canopy.calculate_biomass_increment(par, cw, rue_w)

        s['TDM'] += inc_p
        s['TDMw'] += inc_w

        fty_p = s['TDM'] * HI / self.params['growth']['DMCont']
        
        HI_ws = self.canopy.calculate_effective_hi(HI, WS)
        fty_w = s['TDMw'] * HI / self.params['growth']['DMCont']

        ######
        ###### DEBUGGING
        ######

        # HI0 = self.canopy.calculate_harvest_index(r['TT'], 0.0)
        # HI_HS = self.canopy.calculate_harvest_index(r['TT'], s['cHT'])
        # HI_WS = HI_HS * (1.0 - WS)
        
        if self.debug:
            date = self.climate['Date'].iloc[i].date()
            print(
            f"{date} – "
            f"HI: {HI:.3f}, - "
            
            # f"t0: {t0:.3f} - ",
            f"HS: {HS:.3f} - "
            # f"avail_water: {s['soil']:.3f} - "
            # f"actualT: {actualT:.3f} - ",
            # f"WS: {WS:.3f} - ",
            # f"RUEW: {rue_w:.3f} - "
            
            
        )
        
        ######
        ###### OUTPUT
        ###### 
        
        return {
            'FTYP': fty_p,
            'FTYW': fty_w,
            'CCw':  cw,
            'HI_HS': HI,
            'RUEw': rue_w,
            'ASWC': s['soil'],
            'WS':   WS,
            'T':    actualT
        }
    
    def save_results_csv(self, filepath):
        if self.results is None:
            raise ValueError("No results found. Run run_simulation() first.")
        self.results.to_csv(filepath, index=False)
        if self.debug:
            print(f"Results saved to {filepath}")