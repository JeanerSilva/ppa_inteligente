# app/app.py
import streamlit as st
from config import setup_app
from ui import render_interface

setup_app()
render_interface()
