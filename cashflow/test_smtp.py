
import smtplib

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail's SMTP server
    server.starttls()  # Start TLS encryption
    server.login('cashflow00102@gmail.com', 'rwpdbydoqxdpvdph')  # Replace with your app password
    print("SMTP connection successful")
    server.quit()
except Exception as e:
    print("SMTP connection failed:", e)
