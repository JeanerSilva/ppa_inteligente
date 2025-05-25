# app/app.py
import streamlit as st
from config import setup_app
import logging

from ui.chat import render_interface
import sys
import os
sys.path.append(os.path.dirname(__file__))

os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

setup_app()
render_interface()
