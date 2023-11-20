import influxdb
from influxdb import InfluxDBClient
from datetime import datetime, timezone, timedelta
import subprocess
import os


class WindCheck():
    
    def __init__(self, ip = None, port = None, db = None):
        self.client = InfluxDBClient(ip,port)
        self.client._database = db 
        


    def aris_query(self):
        try:
            query = self.client.query(f"SELECT * FROM active_pow ORDER BY DESC LIMIT 1")            
            return query
        except (influxdb.exceptions.InfluxDBClientError, influxdb.exceptions.InfluxDBServerError) as e:
            print(e)
            return None             

    def neykovo_query(self):
        try:
            query = self.client.query(f"SELECT * FROM neykovo_pow ORDER BY DESC LIMIT 1")            
            return query
        except (influxdb.exceptions.InfluxDBClientError, influxdb.exceptions.InfluxDBServerError) as e:
            print(e)
            return None       
    
    def from_day_beginning(self, measurement):
        # Get the current date
        current_date = datetime.now().date()

        # Set the beginning of the day
        beginning_of_day = datetime.combine(current_date, datetime.min.time())

        # Convert the beginning_of_day to UNIX timestamp in seconds
        beginning_of_day_timestamp = int(beginning_of_day.timestamp())

        # Create the InfluxDB query with the WHERE clause for the time range
        query = f"SELECT * FROM {measurement} WHERE time >= {beginning_of_day_timestamp}s"
        result = self.client.query(query)
        
        self.missing_for_today(result)
        
        

    def check_missing_live(self, query):
        
        timestamp = None
               
        for r in query:            
            timestamp = r[0].get("time", None)
        if timestamp:
            datetime_object = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            datetime_object = datetime_object.replace(tzinfo=timezone.utc)

            current_time = datetime.now(timezone.utc)
            time_difference = current_time - datetime_object
            
            difference_in_minutes = time_difference.total_seconds() / 60
            print(f"live: {difference_in_minutes}")
            if difference_in_minutes <= 2:
                return True
            else:
                return False
            
    def missing_for_today(self, today_query):

        data = list(today_query)[0]
        
        print(len(data))
        
        
        # Get the current date
        current_date = datetime.now().date()

        # Set the beginning of the day
        beginning_of_day = datetime.combine(current_date, datetime.min.time())

        # Generate a list of expected timestamps for each minute from the beginning of the day till now
        expected_timestamps = [beginning_of_day + timedelta(minutes=i) for i in range((datetime.now() - beginning_of_day).seconds // 60)]
        print(len(expected_timestamps))        
    
    def ping_farms(self, host):
        try:
            # Use subprocess to run the ping command
            subprocess.run(["ping", "-c", "4", host], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        
    def forecast_check_mail(self, path):
        
        asset_path = path.split("/")[1]        
        
        # Get the current date in the format you specified (e.g., "20.05.2023")
        current_date = datetime.now()
        # Get the absolute path to the home directory
        home_directory = os.path.expanduser("~")

        # Specify the relative path to the "forecasts" folder
        relative_folder_path = path #"forecast_final/newForecasts"

        # Create the absolute path by joining the home directory and the relative path
        absolute_folder_path = os.path.join(home_directory, relative_folder_path)       

        # For example, listing all files in the "forecasts" folder
        files_in_folder = os.listdir(absolute_folder_path)
        
        # Check if there is a file with the current date in its name     
        matching_files = None   
        if asset_path == 'newForecasts':
            current_date = current_date.strftime("%d.%m.%Y")
            matching_files = [file for file in files_in_folder if f"3000_{current_date}" in file]
        elif asset_path == 'newForecastsUtopus':
            current_date = current_date.strftime("%Y%m%d")
            matching_files = [file for file in files_in_folder if f"{current_date}" in file]
        elif asset_path == 'newForecastsUtopusNeykovo':
            current_date = current_date.strftime("%Y%m%d")
            matching_files = [file for file in files_in_folder if f"{current_date}" in file]            
            
        if matching_files:            
            return True
        else:            
            return False
    
    def forecast_check_db_day_begin(self, measurement):
         # Get the current date
        current_date = datetime.now().date()
        next_day = datetime.now().date() + timedelta(days=1)

        # Set the beginning of the day
        beginning_of_day = datetime.combine(current_date, datetime.min.time())
        
        beginning_of_next_day = datetime.combine(next_day, datetime.min.time())
        

        # Convert the beginning_of_day to UNIX timestamp in seconds
        beginning_of_day_timestamp = int(beginning_of_day.timestamp())
        
        beginning_of_next_day_timestamp = int(beginning_of_next_day.timestamp())

        # Create the InfluxDB query with the WHERE clause for the time range
        query = f"SELECT * FROM {measurement} WHERE time >= {beginning_of_day_timestamp}s and time <= {beginning_of_next_day_timestamp}s"        
        result = self.client.query(query)
        if result:
            data = list(result)[0]
            print(len(data))      
            if len(data) == 97:
                return True
            else:
                return False       
        else:
            return False
        
def check_services(is_called_from_menu=False):
    print("Here!!!")
    status_list = []
    periodic_messages = []
    
    check = WindCheck('127.0.0.1','8086', 'wind')
    
    #Live Aris:
    live_aris_query = check.aris_query()
    
    live_aris_check = check.check_missing_live(live_aris_query)
    
    #Live Power:
    live_power_query = check.neykovo_query()
    live_power_check = check.check_missing_live(live_power_query)
    
    #Check e-mail exist En-Pro and Utopus:
    #EnPro Aris&Power
    email_enPro = check.forecast_check_mail('forecast_final/newForecasts')
    #Utopus Aris
    
    email_utopus_aris = check.forecast_check_mail('forecast_final/newForecastsUtopus')
    
    #Utopus Power
    email_utopus_power = check.forecast_check_mail('forecast_final/newForecastsUtopusNeykovo')   
    
    
    #Check if the forecast database is complete
    #Aris EnPro
    aris_db_count_enPro = check.forecast_check_db_day_begin("aris_forecast")
    #Power EnPro
    power_db_count_enPro = check.forecast_check_db_day_begin("power_forecast")
    #Aris Utopus
    aris_db_count_utopus = check.forecast_check_db_day_begin("aris_forecast_utopus")
    #Power Utopus
    power_db_count_utopus = check.forecast_check_db_day_begin("neykovo_forecast_utopus")
    
    #Ping Farms:
    #Aris:10.126.252.1
    ping_aris = check.ping_farms('10.126.252.1')
    #Power:10.126.253.1
    ping_power = check.ping_farms('10.126.253.1')
    
    if live_aris_check:
        if is_called_from_menu:
            status_list.append("Aris DB: OK")
        else: 
            periodic_messages.append({
                "aris_db":"Aris | database fixed"
            })      
        
    else:
        if is_called_from_menu:
            status_list.append("Aris DB: Fail!")
        else:
            periodic_messages.append({
                "aris_db":"Aris | database error"
            }) 
            
    if live_power_check:
        if is_called_from_menu:
            status_list.append("Power DB: OK")
        else:
            periodic_messages.append({
                "power_db":"Power | database fixed"
            })            
    else:
        if is_called_from_menu:
            status_list.append("Power DB: Fail!")
        else:
            periodic_messages.append({
                "power_db":"Power | database error"
            })
    if email_enPro:
        status_list.append("mail enPro: OK")
        print(f"mail enPro: OK")
    else:
        status_list.append("mail enPro: Missing!")
        print(f"mail enPro: Missing!")
    if email_utopus_aris:
        status_list.append("mail Aris Utopus: OK")
        print(f"mail Aris Utopus: OK")
    else:
        status_list.append("mail Aris Utopus: Missing!")
        print(f"mail Aris Utopus: Missing!")
    if email_utopus_power:
        status_list.append("mail Power Utopus: OK")
        print(f"mail Power Utopus: OK")
    else:
        status_list.append("mail Power Utopus: Missing!")
        print(f"mail Power Utopus: Missing!")
    if aris_db_count_enPro:
        status_list.append("Aris Forecast Complete: OK")
        print(f"Aris Forecast Complete: OK")
    else:
        status_list.append("Aris Forecast Complete: Missing vals")
        print(f"Aris Forecast Complete: Missing vals")
    if power_db_count_enPro:
        status_list.append("Power Forecast Complete: OK")
        print(f"Power Forecast Complete: OK")
    else:
        status_list.append("Power Forecast Complete: Missing vals")
        print(f"Power Forecast Complete: Missing vals")
    if aris_db_count_utopus:
        status_list.append("Aris ForecastUtopus Complete: OK")
        print(f"Aris ForecastUtopus Complete: OK")
    else:
        status_list.append("Aris ForecastUtopus Complete: Missing vals")
        print(f"Aris ForecastUtopus Complete: Missing vals")
    if power_db_count_utopus:
        status_list.append("Power ForecastUtopus Complete: OK")
        print(f"Power ForecastUtopus Complete: OK")
    else:
        status_list.append("Power ForecastUtopus Complete: Missing vals")
        print(f"Power ForecastUtopus Complete: Missing vals")
    #Ping
    if ping_aris:
        status_list.append("Aris Ping: OK")
        print(f"Aris Ping: OK")
    else:
        status_list.append("Aris Ping: Fail")
        print(f"Aris Ping: Fail")
    if ping_power:
        status_list.append("Power Ping: OK")
        print(f"Power Ping: OK")
    else:
        status_list.append("Power Ping: Fail")
        print(f"Power Ping: Fail")
    
    print(f"status: {print(len(status_list))}, periodic: {print(len(periodic_messages))}")
    if len(status_list) > 0:
        return status_list
    elif len(periodic_messages) > 0:
        return periodic_messages
    
