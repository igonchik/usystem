import sys
import os
import ctypes
import tempfile
import shutil
from pathlib import Path
from win32com.client import Dispatch
import winshell
import subprocess


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_setup():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # env = os.environ["ProgramFiles"]
    env = str(Path.home())
    setup_folder = os.path.join(env, 'USystem')
    if not os.path.exists(setup_folder):
        os.mkdir(setup_folder)
    temp_name = next(tempfile._get_candidate_names()).upper()
    setup_folder = os.path.join(setup_folder, temp_name)
    while os.path.exists(setup_folder):
        temp_name = next(tempfile._get_candidate_names()).upper()
        setup_folder = os.path.join(setup_folder, temp_name)
    os.mkdir(setup_folder)
    shutil.copytree(os.path.join(BASE_DIR, 'pkg', 'dist'), os.path.join(setup_folder, 'agent'))
    shutil.copytree(os.path.join(BASE_DIR, 'pkg', 'stunnel'), os.path.join(setup_folder, 'stunnel'))
    shutil.copytree(os.path.join(BASE_DIR, 'pkg', 'UConnect'), os.path.join(setup_folder, 'UConnect'))
    appdata = os.getenv('APPDATA')
    app_dir = os.path.join(appdata, 'usystem')
    if not os.path.exists(app_dir):
        os.mkdir(app_dir)
    app_dir = os.path.join(app_dir, temp_name)
    if not os.path.exists(app_dir):
        os.mkdir(app_dir)
    shutil.copy(os.path.join(BASE_DIR, 'pkg', 'cacert.pem'), os.path.join(app_dir))
    shutil.copy(os.path.join(BASE_DIR, 'pkg', 'stun_rsa.key'), os.path.join(setup_folder))
    if not os.path.exists(os.path.join(app_dir, 'stunnel')):
        os.mkdir(os.path.join(app_dir, 'stunnel'))

    ini = "[usystem]\n\
    remote_ip = cp.u-system.tech\n\
    local_port = 5900\n\
    vnc_port = 5899\n\
    remote_sshport = 22\n\
    cert_path = {0}.pem\n\
    cacert_path = {1}\n\
    transport_port = 8080\n\
    share_path = {2}\n\
    policy = 0".format(os.path.join(appdata, "usystem", temp_name, temp_name),
                       os.path.join(appdata, "usystem", temp_name, "cacert.pem"),
                       os.path.join(appdata, "usystem", temp_name, 'share'))
    dest = os.open(os.path.join(setup_folder, 'usystem.ini'), os.O_RDWR | os.O_CREAT)
    os.write(dest, ini.encode('utf8'))

    desktop = winshell.desktop()
    path = os.path.join(desktop, "USystem{0}.lnk".format(temp_name))
    target = os.path.join(setup_folder, 'agent', 'main_client.exe')
    wDir = os.path.join(setup_folder, 'agent')
    icon = os.path.join(setup_folder, 'agent', 'main.ico')
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()
    startup = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs',
                           'Startup', "USystem{0}.lnk".format(temp_name))
    shortcut = shell.CreateShortCut(startup)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()
    subprocess.Popen([os.path.join(setup_folder, 'agent', 'main_client.exe')], cwd=os.path.join(setup_folder, 'agent'),
                     close_fds=True)


if __name__ == '__main__':
    #if not is_admin():
    run_setup()
    #else:
    #    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
