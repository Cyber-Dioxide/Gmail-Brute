import os
import platform
from core import colors
from core.colors import r, g, y, c
from rgbprint import gradient_print

logo = f"""
                 ██████╗ ███╗   ███╗ █████╗ ██╗██╗        
                ██╔════╝ ████╗ ████║██╔══██╗██║██║        
                ██║  ███╗██╔████╔██║███████║██║██║        
                ██║   ██║██║╚██╔╝██║██╔══██║██║██║        
                ╚██████╔╝██║ ╚═╝ ██║██║  ██║██║███████╗   
                 ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝   
                                                          
                ██████╗ ██████╗ ██╗   ██╗████████╗███████╗
                ██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝
                ██████╔╝██████╔╝██║   ██║   ██║   █████╗  
                ██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  
                ██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗
                ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝
                     Author: Saad Khan | Cyber-Dioxide  (V4.0)
        =========================================================
                        [+] Telegram @coding_memz             
                        [+] Instagram @coding_memz
        =========================================================
"""
c = colors
try:
    from colorama import Fore, Style
except ModuleNotFoundError:
    os.system("pip install colorama")


def banner():
    gradient_print(logo, start_color='yellow' , end_color='magenta')


def clear():
    s = platform.platform()
    if "Windows" in s:
        os.system("cls")
    else:
        os.system("clear")
