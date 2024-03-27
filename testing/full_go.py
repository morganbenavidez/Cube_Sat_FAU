import time
import RPi.GPIO as GPIO
import datetime
import csv
#from PiPocketGeiger import RadiationWatch
import ms5837
from startUpBMP180 import *
import os
from scd30_i2c import SCD30
import sys
import subprocess


class Bar02:
    def __init__(self,i2cbus=1):
        self.sensor = ms5837.MS5837_30BA(i2cbus)
        self.sensor.init()
    def read(self):
        self.sensor.read()
        _data = [self.sensor.pressure(ms5837.UNITS_psi), self.sensor.temperature(ms5837.UNITS_Centigrade), self.sensor.altitude()]
        return _data    

# class HeatingElement:
#     def __init__(self, pin):
#         self.pin = pin
#         GPIO.setup(pin,GPIO.OUT)
#         self.on = False
#     def setHigh(self):
#         self.on = True
#         GPIO.output(self.pin,1)
#     def setLow(self):
#         self.on = False
#         GPIO.output(self.pin,0)

class Sensor:
    def __init__(self, pins):
        self.pins = pins
        for pin in self.pins:
            GPIO.setup(pin,GPIO.OUT)
        def read(self):
            return [GPIO.input(x) for x in self.pins]

def truncate(x):
    try:
        return round(x, 2)
    except:
        return x



def double_write(date_var, time_var, ran_already, flag, container_name, python_script):

    # Set file_paths
    current_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_path)
    csv_path = os.path.join(current_path, 'main.csv')
    backup_csv_path = os.path.join(current_path, 'backup.csv')

    # Open backup csv and transmit csv
    with open(csv_path, 'a+', newline='') as SENSORS, open(backup_csv_path, 'a+', newline='') as backup_SENSORS:
        transmit_writer = csv.writer(SENSORS, delimiter=',') #all readings here bar02 was first
        backup_writer = csv.writer(backup_SENSORS, delimiter=',')

        # Backup File - Write once
        if not(ran_already_backup):

            backup_writer.writerow(['Date', 'Time', 'psi', 'temperature', 'altitude', 'CO2level', 'relativeHumidity', 'scdTemperature', 'bmp_temperature','bmp_pressure','bmp_altitude'])
            ran_already_backup = True

        # Transmit file - Will write more than once
        if not(ran_already):
            transmit_writer.writerow(['Date', 'Time', 'psi', 'temperature', 'altitude', 'CO2level', 'relativeHumidity', 'scdTemperature', 'bmp_temperature','bmp_pressure','bmp_altitude'])
            ran_already = True

        # Sensor 1
        try:
            scd30_data = scd30.read_measurement()
            C02level = scd30_data[0]
            scdTemperature = scd30_data[1]
            relativeHumidity = scd30_data[2]


        except:
            C02level, scdTemperature, relativeHumidity = 'null', 'null', 'null' #read -1 instead of null


        # Sensor 2
        try:
            bar_data = bar02.read()
            psi = bar_data[0]
            temperature = bar_data[1]
            altitude = bar_data[2]
        except:
            psi, temperature, altitude = 'null', 'null', 'null'


        # Sensor 3
        try:
            bmp_temperature = bmp.get_temp()
            bmp_pressure = bmp.get_pressure()
            bmp_altitude = bmp.get_altitude()
        except:
            bmp_temperature, bmp_pressure, bmp_altitude = 'null', 'null', 'null'

        total_values = [date_var, time_var, psi, temperature, 
                        altitude, C02level, relativeHumidity, 
                        scdTemperature, bmp_temperature, bmp_pressure, bmp_altitude]


        # Truncate data
        total_values = [truncate(x) for x in total_values]
        #print('total_values: ',total_values)

        # Backup and transmit data
        transmit_writer.writerow(total_values)
        backup_writer.writerow(total_values)

        # Continue reading sensors and writing to files
        if flag == 'continue':

            time.sleep(10)
            ran_already = True

        # Execute a transmission and delete main.csv
        elif flag == 'transmit':
            
            print('INSIDE transmit')
            time.sleep(10)
            # Start the container
            docker_start = ["docker", "start", container_name]
            subprocess.run(docker_start, check=True)

            # After starting, wait 10 seconds
            time.sleep(10)

            # Execute python script inside docker container
            docker_exec = ['docker', 'exec', container_name, 'python3', python_script]
            proc = subprocess.Popen(docker_exec)

            # After calling, wait 10 seconds
            time.sleep(10)

            # Try this first
            proc.terminate() # This might not kill the Python script in the container
            # If the above doesn't kill the py file, try the next thing:
            # Also - if the proc.terminate() works, then move the docker start to initialization section

            # Close the container
            #docker_stop = ['docker', 'stop', container_name]
            #subprocess.run(docker_stop, check=True)

            # After closing, wait 10 seconds
            time.sleep(10)

            # Delete the main.csv file
            os.remove(csv_path)

            ran_already = False


        return ran_already



def read_all_sensors(loop_counter, ran_already, container_name, python_script):

    # Get timestamp info and parse it
    timeStart = datetime.datetime.now()
    date_and_time = str(timeStart)
    dt_split = date_and_time.split(' ')
    date_var = dt_split[0]
    time_var = dt_split[1]

    # Initiate
    if (loop_counter % 6) == 0:
        flag = 'transmit'
    else:
        flag = 'continue'
    
    ran_already = double_write(date_var, time_var, ran_already, flag, container_name, python_script)




########################End function definitions######################
    

ran_already_backup = False # This one is the newly added one
bar02 = Bar02()
scd30 = SCD30()
bmp = bmp180(0x77)
GPIO.setmode(GPIO.BCM)
# Start the docker container
container_name = 'gr385'
python_script_path = 'path/to/script.py'
#docker_start = ["docker", "start", container_name]
#subprocess.run(docker_start, check=True)

try:
    loop_counter = 0
    ran_already = False
    while True:
        loop_counter += 1
        psi, temperature, altitude = 'null', 'null', 'null'
        CO2level, scdTemperature, relativeHumidity = 'null', 'null', 'null'
        bmp_temperature, bmp_pressure, bmp_altitude = 'null', 'null', 'null'
        ran_already = read_all_sensors(loop_counter, ran_already, container_name, python_script_path)
        #time.sleep(1)

except KeyboardInterrupt:
    print("Exiting the program.")
    GPIO.cleanup()  # Clean up GPIO pins if you've been using them
    sys.exit(0)


# heating = HeatingElement(37)





# attempt at heating element, suspended for mosfet and buck converter research
    
#     temp_threshold_low = 30 # 17
#     temp_threshold_high = 31 # 25
#     if float(data[3]) < temp_threshold_low:
#         heating.setHigh()
#         print("ksjdfskf")
#     if float(data[3]) > temp_threshold_high:
#         heating.setLow()
#         print("djfslkdfj")
#     print(data[3])
#     print(heating.on)
#     time.sleep(1)
