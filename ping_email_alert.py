import os
import smtplib
import threading
import time
import json
from email.mime.text import MIMEText
import tkinter as tk
from tkinter import messagebox
import sys
import subprocess
from collections import defaultdict
import asyncio
from kasa import SmartPlug

# Load configuration from JSON file
with open("config.json", "r") as config_file:
    CONFIG = json.load(config_file)

MAIL_SETTINGS = CONFIG["mail_settings"]
REBOOT_SETTINGS = CONFIG["reboot_settings"]

# Define email sending function
def send_email(subject, body, ip_address):
    try:
        with open(CONFIG["email_alert_file"], "r") as f:
            to_emails = [email.strip() for line in f for email in line.split(",") if email.strip()]

        server = smtplib.SMTP_SSL(MAIL_SETTINGS["host"], MAIL_SETTINGS["port"])
        server.login(MAIL_SETTINGS["username"], MAIL_SETTINGS["password"])
        
        email_body = f"""
        <html>
        <body>
            <h2 style="color: #b22222;">&#9888; Alert: Network Issue Detected &#9888;</h2>
            <p><strong>Issue Detected:</strong></p>
            <p>The following IP address is not responding:</p>
            <ul>
                <li><strong>IP Address:</strong> {ip_address}</li>
                <li><strong>Timestamp:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <p style="margin-top: 20px;">Regards,</p>
            <p><strong>MIS Team</strong></p>
        </body>
        </html>
        """
        
        msg = MIMEText(email_body, "html")
        msg["Subject"] = subject
        msg["From"] = MAIL_SETTINGS["from_address"]
        msg["To"] = ", ".join(to_emails)
        
        server.sendmail(MAIL_SETTINGS["from_address"], to_emails, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

# Loading animation class
class LoadingAnimation:
    def __init__(self, ip_address):
        self.running = True
        self.ip_address = ip_address
        self.animator = threading.Thread(target=self.animate)
    
    def start(self):
        self.running = True
        self.animator.start()
    
    def stop(self):
        self.running = False
        self.animator.join()
    
    def animate(self):
        while self.running:
            for ch in '|/-\\':
                print(f'\rPinging {self.ip_address}... {ch}', end='', flush=True)
                time.sleep(0.1)

failure_counts = defaultdict(int)

def ping_and_check(ip_address):
    loading = LoadingAnimation(ip_address)
    loading.start()
    try:
        result = subprocess.run(f"ping -n 1 {ip_address}", capture_output=True, text=True, shell=True)
        output = result.stdout
    finally:
        loading.stop()
    
    if "unreachable" in output or "Request timed out" in output:
        failure_counts[ip_address] += 1
        log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Failed (Attempt {failure_counts[ip_address]})")
        
        if failure_counts[ip_address] == REBOOT_SETTINGS["threshold"]:
            reboot_success, plug_online = attempt_reboot(ip_address)
            
            if reboot_success:
                failure_counts[ip_address] = 0
                log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Device Rebooted Successfully - Failure Count Reset")
            elif plug_online:
                send_email("Alert Bell: Device Reboot Incomplete", 
                           f"The IP address {ip_address} plug is online but device is not responding to ping after reboot.", 
                           ip_address)
            else:
                send_email("Alert Bell: Device Reboot Failed", 
                           f"The IP address {ip_address} failed to reboot and is not responding. Both plug and ping are down.", 
                           ip_address)
        
        if failure_counts[ip_address] >= REBOOT_SETTINGS["max_failures"]:
            send_email("IP Address is Down", 
                       f"The IP address {ip_address} is not responding after {REBOOT_SETTINGS['max_failures']} attempts and reboot.", 
                       ip_address)
    else:
        if failure_counts[ip_address] > 0:
            log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Recovered after {failure_counts[ip_address]} failures")
        failure_counts[ip_address] = 0
        log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Success")

def log_result(result):
    with open(CONFIG["log_file"], "a") as log_file:
        log_file.write(result + "\n")

def control_plug(ip_address, action):
    try:
        with open(CONFIG["plug_ip_file"], "r") as f:
            plug_ip = f.read().strip()
        
        async def async_control_plug():
            plug = SmartPlug(plug_ip)
            await plug.update()
            if action == "on":
                await plug.turn_on()
            elif action == "off":
                await plug.turn_off()
        
        asyncio.run(async_control_plug())
    except Exception as e:
        raise Exception(f"Failed to control plug: {str(e)}")

def attempt_reboot(ip_address):
    """
    Attempt to reboot the device using a smart plug and verify its status.
    Returns a tuple (reboot_success, plug_online).
    """
    for attempt in range(REBOOT_SETTINGS["retry_count"]):
        try:
            # Log the reboot attempt
            log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Attempting reboot (Attempt {attempt + 1}/{REBOOT_SETTINGS['retry_count']})")
            
            # Turn off the smart plug
            control_plug(ip_address, "off")
            time.sleep(5)  # Wait 5 seconds
            
            # Turn on the smart plug
            control_plug(ip_address, "on")
            time.sleep(30)  # Wait for the device to reboot
            
            # Check if the device responds to ping
            result = subprocess.run(f"ping -n 1 {ip_address}", capture_output=True, text=True, shell=True)
            ping_success = "bytes=" in result.stdout
            
            if ping_success:
                # Log success and reset the failure count
                log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, reboot_ping_success")
                return True, True  # Reboot successful, ping successful
            
            # If ping fails but retry attempts remain, log failure
            log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Reboot failed (Ping still failing)")
            if attempt < REBOOT_SETTINGS["retry_count"] - 1:
                time.sleep(REBOOT_SETTINGS["retry_interval"])
        
        except Exception as e:
            # Log the exception during the reboot attempt
            log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Reboot attempt {attempt + 1} failed: {str(e)}")
            if attempt < REBOOT_SETTINGS["retry_count"] - 1:
                time.sleep(REBOOT_SETTINGS["retry_interval"])
    
    # After all retry attempts, if the ping still fails, send an email alert
    send_email(
        "Alert Bell: Reboot Failed - Device Unresponsive",
        f"The IP address {ip_address} did not respond to ping after reboot attempts. Manual intervention may be required.",
        ip_address
    )
    
    # Log the final failure
    log_result(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {ip_address}, Final reboot attempt failed. Ping still not responding.")
    return False, False  # Reboot failed, ping failed


def run_ping_checks():
    with open(CONFIG["ip_address_file"], "r") as f:
        ip_addresses = [ip.strip() for line in f for ip in line.split(",") if ip.strip()]
    
    threads = []
    for ip in ip_addresses:
        t = threading.Thread(target=ping_and_check, args=(ip,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

def create_ui():
    root = tk.Tk()
    root.title("Ping Alert System")
    root.geometry("300x200")
    
    ping_button = tk.Button(root, text="Check IP Status", command=run_ping_checks, font=("Helvetica", 14), bg="#4CAF50", fg="white")
    ping_button.pack(pady=50)
    
    root.mainloop()

def is_task_scheduler():
    return len(sys.argv) > 1 and sys.argv[1] == "--task"

if __name__ == "__main__":
    if is_task_scheduler():
        run_ping_checks()
    else:
        create_ui()
