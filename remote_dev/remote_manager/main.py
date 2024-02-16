import os
import time

import streamlit as st
import shared as s

s.init()


st.title("4090资源管理平台")

dashboard, settings = st.tabs(['dashboard', 'settings'])

with settings:
    st.subheader("全局设置")
    s.args['ip'] = st.text_input("ip address", value=s.args['ip'])
    s.args['sys_info_port'] = st.text_input("sys_info_port", value=s.args['sys_info_port'])
    s.args['name'] = st.text_input("name", key="user name", value=s.args['name'])
    st.divider()
    st.subheader("项目设置")
    s.args['project_path'] = st.text_input("local path", value=s.args['project_path'])
    s.args['svn_path'] = st.text_input("remote path", value=s.args['svn_path'])

    st.subheader("jupyter notebook 管理器")
    for i, jupyter_info in enumerate(s.args['jupyter_info']):
        name = jupyter_info['name']
        port = jupyter_info['port']
        launcher_path = jupyter_info['launcher_path']

        col1, col2, col3, col4 = st.columns(4)
        jupyter_info['name'] = col1.text_input(label="name", key=f"jupyter_name_{i}", value=name)
        jupyter_info['port'] = col2.text_input(label="port", key=f'jupyter_port_{i}', value=port)
        jupyter_info['launcher_path'] = col3.text_input(label="path", key=f'jupyter_launcher_path_{i}', value=launcher_path)
        col4.text("")
        col4.text("")
        if col4.button("X", key=f'juypyter_delete_{i}'):
            s.args['jupyter_info'].pop(i)
            st.experimental_rerun()
    if st.button("add", key="add_jupyter_info"):
        s.args['jupyter_info'].append({'name':'', 'port':'', 'launcher_path':''})
        st.experimental_rerun()
    if st.button("save", key='save_settings'):
        print(s.args)
        s.write_config()
        st.cache_resource.clear()
        st.experimental_rerun()

with dashboard:
    st.subheader("Jupyter 状态管理")
    for i, jupyter_info in enumerate(s.args['jupyter_info']):
        name = jupyter_info['name']
        port = jupyter_info['port']
        launcher_path = jupyter_info['launcher_path']
        pids = s.get_port(port)

        col1, col2, col3, col4 = st.columns(4)
        col1.text(name)
        col2.text(port)
        if len(pids) > 0:
            status = col3.text("online")
            if col4.button("terminate", key=f"terminate_{i}"):
                for pid in pids:
                    res = s.kill_jupyter(pid)
                st.experimental_rerun()
        else:
            status = col3.text("offline")
            if col4.button("run", key=f"run_{i}"):
                res = s.run_jupyter(launcher_path)
                st.experimental_rerun()

    st.subheader("Subversion")
    col1, col2 = st.columns([8, 2])
    col1.write(f"svn path: {s.args['svn_path']}")
    if col2.button("update"):
        with st.spinner("更新中"):
            res = s.http_get("svn_update", {"svn_path": s.args['svn_path']})
            st.info(res.text)

    st.subheader("远程文件查看器")
    if 'remote_path' not in st.session_state:
        st.session_state.remote_path = s.args['svn_path']
    st.write(f"当前目录: {st.session_state.remote_path}")
    res = s.http_get("get_file_list", {'path': st.session_state.remote_path}).json()
    if st.button("../", use_container_width=True):
        st.session_state.remote_path = os.path.dirname(st.session_state.remote_path)
        st.experimental_rerun()
    for i, folder in enumerate(res['folders']):
        if folder.startswith("."):
            continue
        if st.button(folder, key=f"folder_{i}", use_container_width=True):
            st.session_state.remote_path = os.path.join(st.session_state.remote_path, folder)
            st.experimental_rerun()

    for i, file in enumerate(res['files']):
        st.text(file)
    for i in range(10):
        st.empty()





with st.sidebar:
    st.title("实时系统信息")
    res = s.http_get("get_sys_info")
    sys_info = res.json()

    cpu_progress= st.progress(0,'')
    memory_progress = st.progress(0,'')
    gpu_progresses = []
    for gpu_info in sys_info['gpu_info']:
        gpu_progresses.append(st.progress(0,''))

    while True:
        res = s.http_get("get_sys_info")
        sys_info = res.json()
        print(sys_info)
        cpu_progress.progress(value=sys_info['cpu_percent'] / 100.0,text=f"CPU: {sys_info['cpu_percent']}")
        memory_progress.progress(value=(sys_info['memory_used'] / sys_info['memory_total']),text=f"Memory {(sys_info['memory_used'] / 1024 / 1024 / 1024):.2f}/{(sys_info['memory_total'] / 1024 / 1024 / 1024):.2f}GB")
        for gpu_index, gpu_info in enumerate(sys_info['gpu_info']) :
            gpu_progresses[gpu_index].progress(value=(gpu_info['memoryUsed'] / gpu_info['memoryTotal']), text=f"{gpu_info['name']} {(gpu_info['memoryUsed'] / 1024):.2f}/{(gpu_info['memoryTotal']/1024):.2f}GB")

        #st.write(sys_info)
        time.sleep(5)


