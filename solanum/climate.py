import pandas as pd
import numpy as np

class SolanumClimateProcessor:
    
    def __init__(self, climate_data, params):
        self.raw_climate = climate_data.copy()
        self.params = params
        self.processed_climate = None
        self._process_climate_data()
    
    def _process_climate_data(self):
        
        # if 'Date' not in self.raw_climate.columns:
        #     self.raw_climate['Date'] = pd.to_datetime(
        #         self.raw_climate[['Year', 'Month', 'Day']]
        #     )
        
        if 'Date' in self.raw_climate.columns:
            self.raw_climate['Date'] = pd.to_datetime(self.raw_climate['Date'], dayfirst=True)
        else:
            raise ValueError("Input data must contain a 'Date' column.")

        ##########
        self.raw_climate['Day'] = self.raw_climate['Date'].dt.day
        self.raw_climate['Month'] = self.raw_climate['Date'].dt.month
        self.raw_climate['Year'] = self.raw_climate['Date'].dt.year
        ###########
        
        cols = ['Date'] + [col for col in self.raw_climate.columns if col != 'Date']
        self.processed_climate = self.raw_climate[cols].copy()
        
        sowing_date = pd.to_datetime(self.params['phenology']['sowing'])
        harvest_date = pd.to_datetime(self.params['phenology']['harvest'])
        
        mask = ((self.processed_climate['Date'] >= sowing_date) & 
                (self.processed_climate['Date'] <= harvest_date))
        self.processed_climate = self.processed_climate[mask].reset_index(drop=True)
        
        self._calculate_thermal_time()
        # self._validate_climate_data()
    
    def _calculate_thermal_time(self):
        
        sowing = self.params['phenology']['sowing']
        harvest = self.params['phenology']['harvest']
        emergency_days = self.params['phenology']['EDay']
        
        temp_params = self.params['temperature']
        tt_params = (temp_params['Tb'], temp_params['To'], 
                    temp_params['Tu'] - 11, temp_params['Tu'])
        
        tt_data = self._thermal_time_calculation(
            self.processed_climate['Date'],
            self.processed_climate['Tmin'],
            self.processed_climate['Tmax'],
            sowing,
            harvest,
            emergency_days,
            tt_params
        )
        
        self.processed_climate['TT'] = tt_data['tt'].values
    
    def _thermal_time_calculation(self, date, tmin, tmax, sowing, end_harvest, 
                                    emergency_days=30, parameters=(0, 12, 24, 35)):
        
        data_clima = pd.DataFrame({
            'date': pd.to_datetime(date), 
            'tmin': tmin, 
            'tmax': tmax
        })
        
        b1 = 1 / (parameters[1] - parameters[0])
        a1 = -b1 * parameters[0]
        b2 = 1 / (parameters[2] - parameters[3])
        a2 = -b2 * parameters[3]
        
        sowing = pd.to_datetime(sowing)
        end_harvest = pd.to_datetime(end_harvest)
        
        D1 = sowing + pd.Timedelta(days=emergency_days)
        D2 = end_harvest
        rango = data_clima[(data_clima['date'] >= D1) & (data_clima['date'] <= D2)]
        
        ndays = len(rango)
        
        if ndays == 0:
            pre_emergence = data_clima[
                (data_clima['date'] >= sowing) & (data_clima['date'] <= end_harvest)
            ].copy()
            pre_emergence['tt'] = 0
            return pre_emergence[['date', 'tt']]
        
        minimo = rango['tmin'].median()
        base = 2 if minimo > 10 else 0
        
        TT = []
        peso = []
        
        Y0 = (rango.iloc[0]['tmin'] + rango.iloc[0]['tmax']) / 2
        if Y0 < parameters[1]:
            k = a1 + b1 * Y0
        elif Y0 > parameters[2]:
            k = a2 + b2 * Y0
        else:
            k = 1
        if Y0 < parameters[0] or Y0 > parameters[3]:
            k = 0
        
        peso.append(k)
        TT.append(peso[0] * (Y0 - base))
        
        for i in range(1, ndays):
            Y0 = (rango.iloc[i]['tmin'] + rango.iloc[i]['tmax']) / 2
            if Y0 < parameters[1]:
                k = a1 + b1 * Y0
            elif Y0 > parameters[2]:
                k = a2 + b2 * Y0
            else:
                k = 1
            if Y0 < parameters[0] or Y0 > parameters[3]:
                k = 0
            
            peso.append(k)
            TT.append(TT[i - 1] + peso[i] * (Y0 - base))
        
        tmp_dataframe = pd.DataFrame({'date': rango['date'], 'tt': TT})
        
        pre_emergence = data_clima[
            (data_clima['date'] >= sowing) & (data_clima['date'] < D1)
        ].copy()
        pre_emergence['tt'] = 0
        
        tmp_dataframe = pd.concat([pre_emergence[['date', 'tt']], tmp_dataframe], 
                                    ignore_index=True)
        
        return tmp_dataframe
    
    def get_processed_climate(self):
        return self.processed_climate
    
    def print_summary(self):
        print("=" * 60)
        print("CLIMATE DATA SUMMARY")
        print("=" * 60)
        
        print(f"Simulation period: {self.processed_climate['Date'].iloc[0]} to {self.processed_climate['Date'].iloc[-1]}")
        print(f"Number of days: {len(self.processed_climate)}")
        print(f"Total thermal time: {self.processed_climate['TT'].iloc[-1]:.2f}")
        
        print("\nClimate Variables Summary:")
        print("-" * 40)
        numeric_cols = self.processed_climate.select_dtypes(include=[np.number]).columns
        summary_stats = self.processed_climate[numeric_cols].describe()
        print(summary_stats.round(2))