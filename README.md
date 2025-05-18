Micropython script for esp32s3 and mcp9808 to log temperature to a csv file and email it as an attachment. Web server also included to get a live copy of the temperature log file. NTP time is synchronized daily.

Seeed Xiao esp32s3         |  Adafruit MCP9808
:-------------------------:|:-------------------------:
![picture](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/img/105.jpg)  |  ![picture](https://cdn-shop.adafruit.com/970x728/5027-09.jpg)

MCP9808.py and [umail.py](https://github.com/shawwwn/uMail) need to be downloaded to the esp32s3 running the latest micropython. esp32s3_mcp9808_temp_csv_email_and_webpage.py needs to be modified to have your wifi and gmail details, and then it is downloaded to the esp32s3 with the name "main.py" (so that it runs automatically). Your PC's web browser should be able to connect to the web server (remember that the micropython web server is only http, not https). Feel free to change the logging interval (it is presently set for every 30min). If you just want to access the logfile with the web server, feel free to remove the "sendEmail" code.

![picture](https://github.com/charkster/esp32s3_mcp9808_temp_csv_email_and_webpage/blob/main/images/web_server_page.png)

The CSV log file has columns which indicate when the temperature was sampled. The date is stored in the final column. If you adjust the measure interval, the CSV header will adapt to the change.
![picture](https://github.com/charkster/esp32s3_mcp9808_temp_csv_email_and_webpage/blob/main/images/temp_data_csv.png)
