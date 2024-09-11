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

#helpers
def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

def pdf_to_images(bytes_data):
    images = convert_from_bytes(bytes_data)
    return images


if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''



st.session_state['api_key'] = st.text_input('Enter your gemini api key')
genai.configure(api_key=st.session_state['api_key'])




@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')



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
        ''',im1])
        result_json = to_markdown(response.text)
        result_str = result_json.data
        print('fetched result')

        start_idx = result_str.find('{')
        end_idx = result_str.find('}')

        result_str_new = result_str[start_idx:end_idx+1]
        result_dict = ast.literal_eval(result_str_new)
        print(result_dict)

        max_length = max(len(value) for value in result_dict.values())

        for key, value in result_dict.items():
            if len(value) < max_length:
                result_dict[key] = value + ['dummy_value'] * (max_length - len(value))

        final_df = pd.DataFrame(result_dict)

        final_df['supplier_name'] = supp_name
        df_ls.append(final_df)

    combined_df = pd.concat(df_ls, ignore_index=True)
    return combined_df


if st.session_state['api_key'] != '':
    uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        img_list = pdf_to_images(bytes_data)
        st.subheader('Verify Images')
        final_img_list = []
        newsize = (1000, 1000)
        for img in img_list:
            im1 = img.resize(newsize)
            st.write(im1)
            final_img_list.append(im1)
        cols = st.text_input('Enter column header in csv',placeholder='S.no,item name,gst rate,etc..')
        final_cols = '[ ' + cols + ' ]'
        supplier_name = st.text_input('Enter supplier name')
        try:
            if supplier_name != '' and cols != '':
                with st.spinner:
                    df = create_csv(supplier_name,final_cols,final_img_list)
                            
                    csv = convert_df(df)

                    st.download_button(
                    "Press to Download",
                    csv,
                    f"{supplier_name}.csv",
                    "text/csv",
                    key='download-csv'
                    )
            else:
                st.error('Enter column headers and supp name to proceed')

        except Exception as e:
            st.error(e)
      
    # df.to_csv('/content/bharath_auto1.csv',index=False)
else:
    st.error('Please enter api key')
