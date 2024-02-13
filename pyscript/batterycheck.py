@time_trigger('period(now, 1h)')
def battery_check():
    """Check battery status"""
    log.info(f"Checking battery status")
    
    #get setup
    import detective.core as detective
    import detective.functions as functions
    import pandas as pd
    import numpy as np

    #get data from HA DB
    db = detective.db_from_hass_config()
    df = db.fetch_all_data_of(('sensor.battery',), limit=4400)

    # convert to pandas dataframe and get time into seconds
    df = functions.format_dataframe(df)
    df['last_updated'] = pd.to_numeric(df['last_updated_ts'])

    x = df['last_updated']
    y = df['state']

    # fit linear equation
    model = np.polyfit(x, y, 1)
    log.info(f"Coefficients: {model}")

    discharged_voltage = 12.1
    charged_voltage = 14.0
    seconds_per_day = 60 * 60 * 24;
    
    # get 5% lowest voltage percentile
    current_voltage= np.percentile(y, 5);
    log.info(f"Voltage lower 5%: {current_voltage} V")

    # first coefficient is the gradient
    if model[0] < 0:
        time_to_discharge=(current_voltage-discharged_voltage)/-model[0]
        log.info(f"Time to discharge: {time_to_discharge/seconds_per_day} days")
        input_number.days_to_charge.set_value(-time_to_discharge/seconds_per_day)
    elif model[0] > 0:
        time_to_charge=(charged_voltage-current_voltage)/model[0]
        log.info(f"Time to charge: {time_to_charge/seconds_per_day} days")
        input_number.days_to_charge.set_value(time_to_charge/seconds_per_day)
    else:
        log.info(f"Charge steady state")
