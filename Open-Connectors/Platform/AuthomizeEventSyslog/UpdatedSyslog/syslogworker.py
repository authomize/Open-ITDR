# syslogworker.py
import socket
import logging

def send_to_syslog(body, syslog_host, syslog_port):
    try:
        # Open a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Send the data as bytes
        syslog_msg = f"<14>{body}".encode('utf-8')
        sock.sendto(syslog_msg, (syslog_host, syslog_port))

        # Close the socket
        sock.close()
    except Exception as e:
        # Log the exception message
        logging.error(f"An error occurred while sending to syslog: {e}")