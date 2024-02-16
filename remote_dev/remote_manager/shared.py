import requests
import os
import yaml
import streamlit as st

args = {
    'ip': '127.0.0.1',
    'sys_info_port': '5000',
    'jupyter_info': [{'name': '', 'port': '', 'launcher_path': ''}],
    'name': 'unknown',
    'project_path': '.',
    'svn_path': ''
}



@st.cache_resource
def init():
    if not load_config():
        write_config()
    print(f"init complete with args {args}")


def http_get(url: str, arguments=None):
    if arguments is None:
        arguments = {}
    url = f"http://{args['ip']}:{args['sys_info_port']}/{url}"
    if len(arguments.keys()) > 0:
        url += "?"
        key_value_pair = [f"{key}={value}" for key, value in arguments.items()]
        url += "$".join(key_value_pair)
    print(url)
    res = requests.get(url)

    return res

def run_cmd(cmd:str):
    res = http_get("run_cmd", arguments={"cmd": cmd})
    return res.text
def get_port(port):
    res = http_get("get_port", arguments={"port": str(port)})
    res = res.text.split("\n")
    result = set()
    for line in res:
        temp = [i for i in line.split(' ') if i != ""]
        if len(temp) > 4:
            result.add(temp[4])
    return result

def run_jupyter(bat_path:str):
    res = http_get("run_jupyter", arguments={'path':bat_path})
    return res

def kill_jupyter(pid):
    cmd = 'taskkill /pid ' + str(pid) + ' /f'
    res = run_cmd(cmd)
    return res

def load_config():
    global args
    try:
        with open('./config.yml', 'r', encoding='utf-8') as f:
            args = yaml.load_all(f.read(), Loader=yaml.FullLoader)
            if not args:
                return False
    except FileNotFoundError as e:
        return False
    args = list(args)[0]

    return True


def write_config():
    global args
    with open('./config.yml', 'w', encoding='utf-8') as f:
        yaml.dump(data=args, stream=f, allow_unicode=True)
        print(f"config save to ./config.yml")
