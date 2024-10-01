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
from helpers import *
from pathlib import Path

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''

st.set_page_config(page_title="csv parser")
st.markdown('''
<style>
[data-testid="stMarkdownContainer"] ul{
    list-style-position: inside;
}
</style>
''', unsafe_allow_html=True)





def create_csv(supp_name,cols,img_list):
    df_ls = []
    for img in img_list:
        model = genai.GenerativeModel('gemini-1.5-flash')        
        response = model.generate_content([f'''
        You will be given an image which conatains tabular data.
        Extract this information and format it in a python dictionary format.
        The result should strictly only have the fully formatted dictionary.
        Each column should be a unique key and the column values should be the values of the key.
        Also only look for these columns : {cols} 
        Make sure that the dictionary you return is purely in a python dictionary format without any formatting issues.
        ''',img])

        result_json = to_markdown(response.text)
        result_str = result_json.data
        print('fetched result')

        start_idx = result_str.find('{')
        end_idx = result_str.find('}')

        result_str_new = result_str[start_idx:end_idx+1]
        try:
          result_dict = parse_dict_string(result_str_new)
        except:
          print('parsing errors')
          result_dict = parse_dict_string(result_str_new)


        max_length = max(len(value) for value in result_dict.values())

        for key, value in result_dict.items():
            if len(value) < max_length:
                result_dict[key] = value + ['dummy_value'] * (max_length - len(value))

        final_df = pd.DataFrame(result_dict)

        final_df['supplier_name'] = supp_name
        df_ls.append(final_df)

    combined_df = pd.concat(df_ls, ignore_index=True)
    return combined_df

# App
with st.expander('readme'):
        st.markdown(" -This app is intended to quickly convert tabular data from pdfs or images to csv format")
        st.markdown(" -In case of a pdf, each page will be treated as a separate image. Make sure to create the pdf accordingly.")
        st.markdown("-If you get parsing errors, retry by clicking the button again. If it does not work, upload a clearer image.")
        st.markdown("-Extracted data might not be entirely accurate. Always check your data after extraction.")
        
st.session_state['api_key'] = st.text_input('Enter your gemini api key')
genai.configure(api_key=st.session_state['api_key'])

st.info(f'You can create an api key here')
st.page_link('https://aistudio.google.com/app/apikey',label='API key',icon='🔑')

if st.session_state['api_key'] != '':
    
    uploaded_file = st.file_uploader('Choose your .pdf file or image file', type=["pdf","png","jpg"])
    if uploaded_file is not None:
        ext = Path(uploaded_file.name).suffix

        bytes_data = uploaded_file.getvalue()
        image_io = io.BytesIO(bytes_data)
        final_img_list = []
        newsize = (1000, 1000)


        if ext == '.pdf':
            img_list = pdf_to_images(bytes_data)
            for img in img_list:
                im1 = img.resize(newsize)
                st.write(im1)
                final_img_list.append(im1)
        if ext in ('.png','.jpg'):
            img = Image.open(image_io)
            im1 = img.resize(newsize)
            st.write(im1)
            final_img_list.append(im1)
        
        st.subheader('Verify Images')
        
        cols = st.text_input('Enter column headers in csv format',placeholder='S.no,item name,gst rate,etc..')
        supplier_name = st.text_input('Enter supplier/file name')
        try:
            btn = st.button('process')
            if btn:
                if supplier_name != '' and cols != '':             
                    with st.spinner('Processing'):  
                        try:
                            df = create_csv(supplier_name,cols,final_img_list)  
                            csv = convert_df(df)
                            st.download_button(
                            "Download",
                            csv,
                            f"{supplier_name}.csv",
                            "text/csv",
                            key='download-csv'
                            )

                        except Exception as e:
                            st.error(f'Parsing failed.Please retry')
                            st.error(e)
                                    
                else:
                    st.error('Enter column headers and supp name to proceed')

        except Exception as e:
            st.error(e)
      
else:
    st.error('Please enter api key')
