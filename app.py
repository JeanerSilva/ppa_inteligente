# app/app.py
import streamlit as st
from config import setup_app
from ui import render_interface
import logging

setup_app()
render_interface()
