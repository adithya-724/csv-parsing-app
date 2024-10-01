import pathlib
import textwrap
import os
import google.generativeai as genai
from pdf2image import convert_from_bytes
from PIL import Image
import io
import os
import pandas as pd
import ast
from IPython.display import display
from IPython.display import Markdown
import streamlit as st
import json





def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

def pdf_to_images(bytes_data):
    images = convert_from_bytes(bytes_data)
    return images

def sanitize_dict_string(data):
    if isinstance(data, str):
        # Escape single quotes
        sanitized_str =  data.replace("'", "\\'")
        sanitized_str1 = sanitized_str.replace('>', '').strip()
        return sanitized_str1
    else:
        return data

def parse_dict_string(dict_str):
    """
    Parse a sanitized dictionary string using JSON.
    """
    result_str_new = dict_str.replace("'", '"')
    sanitized_str = sanitize_dict_string(result_str_new)
    try:
        return json.loads(sanitized_str)
    except json.JSONDecodeError as e:
        st.error("Error decoding JSON:", e)
        return None
    
@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')