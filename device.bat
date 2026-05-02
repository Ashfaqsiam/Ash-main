@echo off
echo [SYSTEM] Resetting ADB Bridge...

:: 1. Kill any existing buggy ADB processes
adb kill-server
adb start-server

echo [SYSTEM] Enabling Wireless Mode on Port 5555...
:: Note: Your phone must be connected via USB for this step to work the first time
adb tcpip 5555

echo [SYSTEM] Waiting for device to initialize...
timeout /t 3 /nobreak > nul

:: 2. Dynamically find the IP address so you don't have to type it manually
echo [SYSTEM] Fetching Phone IP address...
FOR /F "tokens=2" %%G IN ('adb shell ip addr show wlan0 ^|find "inet "') DO set ipfull=%%G
FOR /F "tokens=1 delims=/" %%G in ("%ipfull%") DO set ip=%%G

:: --- THIS IS THE UPDATED SECTION ---
if "%ip%"=="" (
    echo [WARNING] Could not find Phone IP. Skipping mobile connection!
    exit
)

echo [SYSTEM] Connecting to Ash-Mobile at IP: %ip%...
adb connect %ip%:5555

echo [SUCCESS] Connection established.
timeout /t 2 > nul
exit