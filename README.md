# Send Email on Failed IP Ping with Reboot Attempt

This project monitors a list of IP addresses by pinging them, and if any IP fails to respond:

1. It attempts to reboot the associated device using a **Kasa Smart Plug**.
2. If the reboot fails or the IP still does not respond, an **email alert** is sent to the specified recipients.
3. Logs all events, including successful pings, failures, and reboot attempts.

It includes:
- A **GUI** for manual execution.
- A **task scheduler mode** for automated checks.

---

## Features
- **IP Monitoring**: Continuously pings IP addresses from a list.
- **Smart Plug Reboot**: Uses the Kasa library to reboot devices via a smart plug.
- **Email Alerts**: Sends email notifications for critical events (e.g., ping failures, failed reboots).
- **Logging**: Records all events into a log file for monitoring.
- **GUI Interface**: Allows manual execution with a simple button press.
- **Task Scheduler Support**: Runs in the background with the `--task` flag.

---

## Prerequisites

1. **Python** (3.8 or above)
2. Required Libraries:
   - `python-kasa`
   - `asyncio`
   - `smtplib`
   - `tkinter`
3. A **Kasa Smart Plug** configured and connected to the network.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Abdallah-Tah/send-email-failed-ip.git
   cd send-email-failed-ip
   ```
2. Install required dependencies:
   ```bash
   pip install python-kasa
   ```

---

## Configuration

Update the `config.json` file with the following details:

```json
{
    "mail_settings": {
        "host": "mail.privateemail.com",
        "port": 465,
        "username": "your-email@example.com",
        "password": "your-email-password",
        "from_address": "your-email@example.com"
    },
    "reboot_settings": {
        "threshold": 2,
        "retry_count": 3,
        "retry_interval": 180
    },
    "email_alert_file": "email_send_alert.txt",
    "log_file": "ping_log.txt",
    "ip_address_file": "ip_address_list.txt",
    "plug_ip_file": "plug_ip.txt"
}
```

- **mail_settings**: Configure your SMTP server for sending emails.
- **reboot_settings**:
   - `threshold`: Number of consecutive ping failures before attempting a reboot.
   - `retry_count`: Number of reboot attempts before sending a failure alert.
   - `retry_interval`: Delay (in seconds) between reboot retries.
- **email_alert_file**: File containing recipient email addresses (comma-separated).
- **ip_address_file**: File containing the list of IP addresses to monitor.
- **plug_ip_file**: File containing the smart plug's IP address.

---

## Usage

### 1. **Run Manually with GUI**
Execute the script without flags to launch the GUI:
```bash
python script.py
```

### 2. **Automated Task Scheduler Mode**
Run the script with the `--task` flag for background operation (e.g., through a task scheduler):
```bash
python script.py --task
```

---

## File Structure
```
.
├── config.json              # Configuration file
├── script.py                # Main script file
├── email_send_alert.txt     # List of recipient email addresses
├── ip_address_list.txt      # List of IP addresses to monitor
├── plug_ip.txt              # IP of the smart plug
├── ping_log.txt             # Log file for events
└── README.md                # Project documentation
```

---

## Example Log Entry
```
2024-06-10 10:15:32, 192.168.1.10, Failed (Attempt 1)
2024-06-10 10:16:45, 192.168.1.10, Attempting reboot (Attempt 1/3)
2024-06-10 10:18:00, 192.168.1.10, reboot_ping_success
```

---

## Troubleshooting
1. **Email Not Sending**:
   - Check SMTP credentials in `config.json`.
   - Ensure the SMTP server allows external connections.

2. **Smart Plug Control Fails**:
   - Verify the plug IP in `plug_ip.txt`.
   - Ensure the device is reachable on the network.

3. **Ping Failures**:
   - Ensure the monitored IP addresses are correct and online.

---

## License
This project is licensed under the MIT License.

---

## Contact
For issues or support, please contact:
**[Your Name]**  
**[Your Email]**  
**[GitHub Profile](https://github.com/Abdallah-Tah)**
