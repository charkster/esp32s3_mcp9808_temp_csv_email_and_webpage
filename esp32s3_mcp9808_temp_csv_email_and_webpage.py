import machine
import socket
import network
import time
import ntptime
import utime
import _thread
import MCP9808 # this needs to be a file saved on esp32s3
import umail   # this needs to be a file saved on esp32s3
import os

def file_exists(filename):
    try:
        os.stat(filename)
        return True
    except:
        return False

def print_csv_header(meas_interval): # meas_interval is in minutes
    row_text = "0:00,"
    curr_min = 0
    while (curr_min + meas_interval) < (60 * 24):
        curr_min += meas_interval
        hour = curr_min//60
        min  = curr_min%60
        row_text += str(hour) + ":" + str("{:02d}".format(min)) + ","
    return row_text

def align_to_midnight():
    while (not connect_to_wifi()): # ensure we get latest NTP correction to RTC
        time.sleep(10)
    t = time.localtime()
    curr_min = t[3]*60+t[4]
    curr_sec = t[5]
    time.sleep(60 - curr_sec) # align with minute boundary
    time.sleep( ((60*24) - curr_min - 1)*60 )

def log_temp_data_to_file(FILE_NAME='temp_data.csv',meas_interval=30, fahrenheit=True): # meas_interval is in minutes
    i2c = machine.I2C(sda=machine.Pin(5), scl=machine.Pin(6), freq=400000) # esp32s3 xiao
    tsensor = MCP9808.MCP9808(i2c_instance=i2c, i2c_dev_addr=0x18, fahrenheit=fahrenheit)
    t = time.localtime()
    curr_month = t[1]
    curr_min = t[3]*60+t[4]
    missed_meas = curr_min//meas_interval + 1
    if (not file_exists(FILE_NAME)):
        f = open(FILE_NAME, 'a+') # if already exists open and append, else create and append
        f.write("\n" + print_csv_header(meas_interval) + "\n")
        f.write(missed_meas*',')
        f.close()
    curr_sec = t[5]
    time.sleep(60 - curr_sec) # align with minute boundary
    wait_min = meas_interval - (curr_min % meas_interval) - 1
    time.sleep(60*wait_min) # align with expected interval boundary
    total_meas = (60 * 24)//meas_interval
    remaining_meas = total_meas - missed_meas
    for n in range(0,remaining_meas): # this loop is for the first day
        try:
            temp = tsensor.get_temp()
        except:
            temp = tsensor.get_temp()
        f = open(FILE_NAME, 'a+')
        if (fahrenheit):
            f.write("{:.0f},".format(temp))
        else:
            f.write("{:.2f},".format(temp))
        f.close()
        # if wifi is down do one attempt to connect
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            connect_to_wifi()
        if (n < (remaining_meas - 1)): # last iteration skip wait time as we will align to midnight
            time.sleep(meas_interval*60)

    t = time.localtime()
    date = str("{:d}/{:d}/{:d}".format(t[1],t[2],t[0]))
    f = open(FILE_NAME, 'a+')
    f.write(date + "\n")
    f.close()
    if (t[1] != curr_month):
        sendEmail(FILE_NAME)
    align_to_midnight()

    while True: # this loop is for all subsequent days
        for n in range(0,total_meas): 
            try:
                temp = tsensor.get_temp()
            except:
                temp = tsensor.get_temp()
            f = open(FILE_NAME, 'a+')
            if (fahrenheit):
                f.write("{:.0f},".format(temp))
            else:
                f.write("{:.2f},".format(temp))
            f.close()
            # if wifi is down do one attempt to connect
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                connect_to_wifi()
            if (n < (total_meas - 1)): # last iteration skip wait time as we will align to midnight
                time.sleep(meas_interval*60)

        t = time.localtime()
        date = str("{:d}/{:d}/{:d}".format(t[1],t[2],t[0]))
        f = open(FILE_NAME, 'a+')
        f.write(date + "\n")
        f.close()
        if (t[1] != curr_month):
            sendEmail(FILE_NAME)
        align_to_midnight()

def connect_to_wifi():
    # Your network credentials
    ssid = 'YOUR_SSID'
    password = 'YOUR_PASSWORD'
    #Connect to Wi-Fi
    wlan = network.WLAN(network.STA_IF)
    wlan.ifconfig(('192.168.0.201', '255.255.255.0', '192.168.0.1', '205.171.3.25')) # put your static IP here
    time.sleep_ms(1000)
    wlan.active(True)
    time.sleep_ms(1000)
    wlan.connect(ssid, password)

    # Wait for connection to establish
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)
    
    # Manage connection error
    if wlan.isconnected():
        print('connected')
        ntptime.timeout = 5
        try:
            ntptime.settime() # this is GMT
        except:
            ntptime.settime() # try again
        rtc = machine.RTC()
        utc_shift = -7 # Phoenix Arizona
        tm = utime.localtime(utime.mktime(utime.localtime()) + utc_shift*3600)
        tm = tm[0:3] + (0,) + tm[3:6] + (0,)
        rtc.datetime(tm)
        return True
    else:
        print(wlan.status())
        return False

def web_server(FILE_NAME = 'temp_data.csv'):
    while True:
        # Set up the web server
        address = socket.getaddrinfo('192.168.0.201', 80)[0][-1]
        server_socket = socket.socket()
        server_socket.bind(address)
        server_socket.listen(5) # at most 5 clients
        print('Listening on', address)

        while OSError:
            conn, addr = server_socket.accept()
            print('Client connected from', addr)
            request = conn.recv(1024)
            request = request.decode()

            if "GET /download" in request:
                try:
                    with open(FILE_NAME, "rb") as file:
                        conn.send("HTTP/1.1 200 OK\r\n")
                        conn.send("Content-Type: application/octet-stream\r\n")
                        conn.send("Content-Disposition: attachment; filename={}\r\n".format(FILE_NAME))
                        conn.send("\r\n")
                        conn.send(file.read())  # Send the file content
                except OSError:
                    try:
                        conn.send("HTTP/1.1 404 Not Found\r\n\r\nFile not found.")
                    except:
                        pass
            else:
                try:
                    conn.send("HTTP/1.1 200 OK\r\n")
                    conn.send("Content-Type: text/html\r\n\r\n")
                    conn.send("<html><body><h1>MicroPython Web Server</h1>")
                    conn.send("<p><a href='/download'>" + FILE_NAME + "</a></p>")
                    conn.send("</body></html>")
                except OSError:
                    pass
            conn.close()
        server_socket.close()
        wlan = network.WLAN(network.STA_IF)
        while not wlan.isconnected():
            connect_to_wifi()

def sendEmail(CSV_FILE):
    #initialize SMTP server and login
    smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
    # Email details
    sender_email = 'your_sender_email@gmail.com'
    sender_name = 'pico email'
    sender_app_password = 'gmail_app_password'
    recipient_email ='your_destination_email@gmail.com'
    email_subject ='Monthly automated ESP32C3 Temperature CSV file'
    smtp.login(sender_email, sender_app_password)
    smtp.to(recipient_email)
    smtp.write("From:" + sender_name + "<"+ sender_email+">\n")
    smtp.write("Subject:" + email_subject + "\n")
    uuidgen = "ddb8f663-bfcd-49d6-ae3f-ade84587f9d0"
    smtp.write("MIME-Version: 1.0\n")
    smtp.write("Content-Type: multipart/mixed; boundary=" + uuidgen + '\n\n')
    smtp.write("--" + uuidgen + '\n') # boundary
    smtp.write("Content-Type: text/plain; charset=UTF-8\n")
    smtp.write("Content-Disposition: inline\n\n")
    t = time.localtime()
    date = str("{:2d}/{:2d}/{:4d} {:2d}:{:02d}:{:02d}".format(t[1],t[2],t[0],t[3],t[4],t[5]))
    smtp.write("ESP32C3 Temperature logfile is attached\n")
    smtp.write("Present time is " + date + '\n\n')
    smtp.write("--" + uuidgen + '\n') # boundary
    smtp.write('Content-Type: text/csv; name=' + CSV_FILE + '\n')
    smtp.write('Content-Disposition: attachment; filename=' + CSV_FILE + '\n\n')
    content = ''
    try:
        with open(CSV_FILE, 'r') as infile:
            content = infile.read()
            smtp.write(content)
            smtp.write('\n')
            smtp.send()
            smtp.quit()
    except OSError:
        pass
    

while (not connect_to_wifi()):
    time.sleep(10)
# ESP32S3 has 2 cores, let's have temperature logging run on one thread
first_thread = _thread.start_new_thread(log_temp_data_to_file, ())
time.sleep(3) # make sure log file is created before webserver is started
# have web_server running on other thread
second_thread = _thread.start_new_thread(web_server, ())


