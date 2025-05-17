Micropython script for esp32s3 and mcp9808 to log temperature to a csv file and email it as an attachment. Web server also included to get a live version of the temperature log file.

Seeed Xiao esp32s3         |  Adafruit MCP9808
:-------------------------:|:-------------------------:
![picture](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/img/105.jpg)  |  ![picture](https://cdn-shop.adafruit.com/970x728/5027-09.jpg)

MCP9808.py and umail.py need to be downloaded to the esp32s3 running the latest micropython. esp32s3_mcp9808_temp_csv_email_and_webpage needs to be modified to have your wifi and gmail details, and then it is downloaded to the esp32s3 with the name "main.py" (so that it runs automatically). Connect to the unit by using your PC's web browser (remember that the micropython web server is only http, not https). Feel free to change the logging interval (it is presently set for every 30min).


