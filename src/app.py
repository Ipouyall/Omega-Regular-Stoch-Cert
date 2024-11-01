import streamlit as st

from system.webUI.ui import WebUI

__author__ = "Pouya Sadeghi"
__contact__ = "https://github.com/ipouyall"
__copyright__ = "Copyright 2025,"
__deprecated__ = False
__app_name__ = "Neural Almost-sure LTL Control"

st.set_page_config(page_title=__app_name__, layout="wide")
st.sidebar.title(__app_name__)
# st.sidebar.divider()

if "app" not in st.session_state:
    st.session_state.app = WebUI()
st.session_state.app.run()
