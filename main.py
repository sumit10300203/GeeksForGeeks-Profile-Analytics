import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.app_logo import add_logo
from streamlit_card import card
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_extras.grid import grid
from streamlit_option_menu import option_menu
import streamlit_antd_components as sac
from streamlit_lottie import st_lottie
import pandas as pd
import numpy as np
from plotly_calplot import calplot
import plotly.graph_objects as go
import plotly.express as px
import requests as re
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
import time
import calendar
from pytz import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re as regex
import os
import json as js
import toml as tm
import math
from prophet import Prophet
import logging
import pyrebase
import pickle
import urllib.request
import traceback
import sketch

tz = timezone("Asia/Kolkata")
cache_time_sync = datetime.now(tz).strftime("%Y-%m-%d-%H")
max_entries = 500

logger = logging.getLogger('cmdstanpy')
logger.addHandler(logging.NullHandler())
logger.propagate = False
logger.setLevel(logging.CRITICAL)

firebase = pyrebase.initialize_app(st.secrets.FIREBASE_API_KEY)
storage = firebase.storage()

os.environ['SKETCH_MAX_COLUMNS'] = '300'

st.set_page_config(
    page_title="GFG Profile Analytics",
    page_icon="📈",
    layout="wide"
)


# sketch library problem info msg
sketch_problem = "Sketch Library which is used for generate report using AI might not be working..."


if 'raw_data' not in st.session_state:
    st.session_state['raw_data'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'profile_details' not in st.session_state:
    st.session_state['profile_details'] = None
if 'df_all_problems' not in st.session_state:
    st.session_state['df_all_problems'] = None
if 'df_problems_solved_by_user' not in st.session_state:
    st.session_state['df_problems_solved_by_user'] = None
if 'df_all_problems_with_solved_status' not in st.session_state:
    st.session_state['df_all_problems_with_solved_status'] = None
if 'company' not in st.session_state:
    st.session_state["company"] = None
if 'topic' not in st.session_state:
    st.session_state["topic"] = None

def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return js.load(f)

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-features=NetworkService")
options.add_argument("--window-size=1920x1080")
options.add_argument("--disable-features=VizDisplayCompositor")

def home():
    @st.cache_data(show_spinner = 0, max_entries = max_entries)
    def get_profile_short_info(profile_name: str, hash_str: str):
        username = ''
        with webdriver.Chrome(options=options) as driver:
            tz_params = {'timezoneId': 'Asia/Kolkata'}
            driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)
            try:
                url = f'https://auth.geeksforgeeks.org/user/{profile_name}'
                driver.get(url)
                driver.add_cookie(st.secrets.GFG_COOKIE.to_dict())
                driver.refresh()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '''#comp > div.AuthLayout_outer_div__20rxz > div > div.AuthLayout_head_content__ql3r2 > div > div > div.heatMapAndLineChart_head__kvZtS > div.heatMapCard_head__QlR7_ > div.heatMapHeader_head__HLQSQ > div.heatMapHeader_head_right__ncipg > select''')))
                soup = bs(driver.page_source, 'html.parser')
                username = soup.find('div', class_='profilePicSection_head_userHandleAndFollowBtnContainer_userHandle__p7sDO').text
                if username != profile_name:
                    username = ''
                st.session_state['raw_data'] = js.loads(bs(driver.page_source, 'html.parser').find('script', id = "__NEXT_DATA__").text)

            except:
                print(traceback.format_exc())
        
            finally:
                return username

    with st.container():
        st.title(':green[GeeksForGeeks] Profile Analytics :chart_with_upwards_trend:', anchor = False)
        st.caption('**_A tool made for Coders with :heart:_**')
        st.divider()

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            profile_name = st.text_input('Enter GFG Profile Handle (eg: sumit10300203)', placeholder = 'Enter GFG Profile Handle (eg: sumit10300203)', label_visibility = 'collapsed')
        with col2:
            button = st.button('Continue')

    if button:
        if profile_name:
            with st.spinner('**Please have some :coffee: while I :mag: your profile**'):
                search_result_username = get_profile_short_info(profile_name, f'{profile_name}#{cache_time_sync}')
                if search_result_username != '':
                    st.session_state['username'] = search_result_username
                    st.success(f"**Profile Found - {st.session_state['username']}**", icon="✅")
                    return 1
                else:
                    st.session_state['username'] = ''
                    st.error(f"**Either Profile doesn't exists or GFG profile page not displaying due to maintenance. Try again later**", icon="🚨")
        else:
            st.session_state['username'] = ''
            st.error(f"**Please Enter Valid username and press Continue**", icon="🚨")
    return 0

@st.cache_data(show_spinner = 0, max_entries = max_entries)
def get_all_problems(hash_str):
    tmp_df_all_problems = pd.DataFrame.from_records(pickle.load(urllib.request.urlopen(storage.child('all_problems_sets.pickle').get_url(None))))
    tmp_df_all_problems['accuracy'] = tmp_df_all_problems['accuracy'].map(lambda x: x.replace('%', '')).astype(np.float64)
    tmp_df_all_problems.rename({'accuracy': 'accuracy(%)'}, axis = 1, inplace = True)
    tmp_df_all_problems['company_tags'] = tmp_df_all_problems['company_tags'].apply(lambda x: {v: 1 for v in x})
    tmp_df_all_problems['topic_tags'] = tmp_df_all_problems['topic_tags'].apply(lambda x: {v: 1 for v in x})
    tmp_company = pd.DataFrame(tmp_df_all_problems['company_tags'].tolist()).fillna(0)
    tmp_topic = pd.DataFrame(tmp_df_all_problems['topic_tags'].tolist()).fillna(0)
    tmp_df_all_problems = tmp_df_all_problems.join(tmp_company).join(tmp_topic)
    tmp_df_all_problems.drop(columns=['company_tags', 'topic_tags'], inplace=True)
    # tmp_df_all_problems["problem_url"] = tmp_df_all_problems["problem_url"].map(lambda x: x.replace("www.", "practice."))
    tmp_df_all_problems.set_index('id', drop = True, inplace = True)
    tmp_df_all_problems['difficulty'] = tmp_df_all_problems['difficulty'].apply(lambda x: x.lower())
    return tmp_df_all_problems, tmp_company.columns.to_list(), tmp_topic.columns.to_list()

    # all_problems_list = pd.read_csv("problems.csv")
    # all_problems_list.set_index('id', drop = True, inplace = True)
    # all_problems_list['difficulty'] = all_problems_list['difficulty'].apply(lambda x: x.lower())

@st.cache_data(show_spinner = 0, max_entries = max_entries)
def get_profile_info(profile_name: str, hash_str, main_user: int = 1):
    def create_bar(text = "Fetching Details, Please wait.."):
        return st.progress(0, f'**{text} (0%)**')
    
    def progress_bar(bar, prog, text = "Fetching Details, Please wait.."):
        bar.progress(prog, f'**{text}  ({prog}%)**')
        time.sleep(0.2)

    def empty_progress_bar(bar):
        time.sleep(0.5)
        bar.empty()

    my_bar = create_bar()

    json_file = {'username': None, 'full_name': None, 'created_date': None, 'user_img': 'https://www.seekpng.com/png/detail/72-729756_how-to-add-a-new-user-to-your.png',
                     'submissions_on_each_day': {'Date': [], 'Day': [], 'Total_submissions': []}, 'Institution_name': None, 'Organization_name': None,
                     'Languages_used': [], 'Campus_ambassador_name': None, 'Campus_ambassador_profile_link': None, 'Current_POTD_Streak': 0, 'Global_POTD_Streak': 0, 
                     'rank_in_institution': None, 'Overall_coding_score': 0, 'Total_problem_solved': 0, 'Monthly_coding_score': 0, 'Overall_Article_Published': 0, 
                     'solved_problems_collections': [],
                     'registered_geeks': None, 'institute_top_coders': {'Name': [], 'Practice_Problems': [], 'Coding_Score': [], 'Profile_url': [], 'GfG_Articles': []}}
    try:
        soup = st.session_state['raw_data']
        if soup == '':
            raise Exception("Data Fetching Error!")
        
        progress_bar(my_bar, 10)
            
        json_file['username'] = soup["props"]["pageProps"]["userHandle"]
        json_file['full_name'] = soup["props"]["pageProps"]["userInfo"]["name"]
        json_file['created_date'] = soup["props"]["pageProps"]["userInfo"]["created_date"]

        progress_bar(my_bar, 20)
        for y in range(datetime.today().year, datetime.strptime(json_file['created_date'], '%Y-%m-%d %H:%M:%S').year - 1, -1):
            heatmap_data_yearly = {
                f'{y}-{month:02d}-{day:02d}': 0  
                for month in range(1, 13) for day in range(1, calendar.monthrange(y, month)[1] + 1)
                }
            heatmap_data_yearly.update(re.post("https://practiceapi.geeksforgeeks.org/api/v1/user/problems/submissions/", json = {"handle":profile_name,"requestType":"getYearwiseUserSubmissions","year":str(y),"month":""}).json()["result"])

            for i, j in heatmap_data_yearly.items():
                tmp = i.split("-")
                json_file['submissions_on_each_day']['Total_submissions'].append(j)
                json_file['submissions_on_each_day']['Day'].append(calendar.day_name[datetime.strptime(i, '%Y-%m-%d').weekday()])
                json_file['submissions_on_each_day']['Date'].append(f'{tmp[0]} {tmp[1]} {tmp[2]}')
            # element = driver.find_element(by=By.CSS_SELECTOR, value="#comp > div.AuthLayout_outer_div__20rxz > div > div.AuthLayout_head_content__ql3r2 > div > div > div.heatMapAndLineChart_head__kvZtS > div.heatMapCard_head__QlR7_ > div.heatMapHeader_head__HLQSQ > div.heatMapHeader_head_right__ncipg > select")
            # action.click(on_element = element).perform()
            # action.send_keys(Keys.ARROW_DOWN).perform()
            # action.send_keys(Keys.ENTER).perform()
            # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '''#comp > div.AuthLayout_outer_div__20rxz > div > div.AuthLayout_head_content__ql3r2 > div > div > div.heatMapAndLineChart_head__kvZtS > div.heatMapCard_head__QlR7_ > div.heatMapHeader_head__HLQSQ > div.heatMapHeader_head_right__ncipg > select''')))

        progress_bar(my_bar, 45)

        link = soup["props"]["pageProps"]["userInfo"]["profile_image_url"]
        if '.svg' not in link:
            json_file['user_img'] = link

        progress_bar(my_bar, 50)

        json_file['Current_POTD_Streak'] = soup["props"]["pageProps"]["userInfo"]["pod_solved_longest_streak"]
        json_file['Global_POTD_Streak'] = soup["props"]["pageProps"]["userInfo"]["pod_solved_global_longest_streak"]

        progress_bar(my_bar, 55)
            
        json_file['Institution_name'] = soup["props"]["pageProps"]["userInfo"]["institute_name"] 
        json_file["Organization_name"] = soup["props"]["pageProps"]["userInfo"]["organization_name"]
        json_file['Campus_ambassador_name'] = soup["props"]["pageProps"]["userInfo"]["campus_ambassador"]
        json_file['Languages_used'] = soup["props"]["pageProps"]["languages"]
            
        progress_bar(my_bar, 60)
        
        json_file['rank_in_institution'] = soup["props"]["pageProps"]["userInfo"]["institute_rank"]

        progress_bar(my_bar, 65)

        json_file['Overall_coding_score'] = soup["props"]["pageProps"]["userInfo"]["score"]
        json_file['Total_problem_solved'] = soup["props"]["pageProps"]["userInfo"]["total_problems_solved"]
        json_file['Monthly_coding_score'] = soup["props"]["pageProps"]["userInfo"]["monthly_score"]
        json_file['Overall_Article_Published'] = soup["props"]["pageProps"]["badgesInfo"]["publish_post_count"] + soup["props"]["pageProps"]["badgesInfo"]["improvement_count"]
            
        progress_bar(my_bar, 70)
        
        json_file['solved_problems_collections'] = [int(j) for i in soup["props"]["pageProps"]["userSubmissionsInfo"] for j in soup["props"]["pageProps"]["userSubmissionsInfo"][i]]

        progress_bar(my_bar, 95)
        
        if json_file['Institution_url']:
            with webdriver.Chrome(options=options) as driver:
                tz_params = {'timezoneId': 'Asia/Kolkata'}
                driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)
                url = json_file['Institution_url']
                driver.get(url)
                soup = js.loads(bs(driver.page_source, 'html.parser').find('script', id = "__NEXT_DATA__").text)
            json_file["registered_geeks"] = soup["props"]["pageProps"]["leftCardData"]["data"]["geeks_count"]

    except:
        pass

    finally:
        progress_bar(my_bar, 100, 'Fetching Done..')
        empty_progress_bar(my_bar)
        return json_file

@st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)         
def user_img(username, hash_str):
    with st.container():
        card(
            title = "",
            text = "",
            image= st.session_state['profile_details']['user_img'],
            url = f"https://auth.geeksforgeeks.org/user/{username}", on_click = lambda: None)
        st.header(f":green[Welcome] {username.split('#')[0]}", anchor = False)
        st.divider()

with st.sidebar:
    @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
    def side_bar_lottie():
        st_lottie(load_lottiefile("lottie_files/Animation - 1695676237611.json"))
    side_bar_lottie()
    page = sac.menu([
    sac.MenuItem('Home', icon='house'),
    sac.MenuItem('Dashboard', icon='speedometer2', children=[
        sac.MenuItem('User basic details', icon='person-circle'),
        sac.MenuItem('Submission analysis', icon='bar-chart-line'),
        sac.MenuItem('Problem submission analysis', icon='plus-slash-minus')]),
    sac.MenuItem('View Problem Set & Report', icon='view-stacked'),
    sac.MenuItem('Can I Solve ?', icon='check2-square'),
    sac.MenuItem('Help Scrapper', icon='info-circle-fill'),
    sac.MenuItem('About Me', icon='person-vcard'),
    sac.MenuItem('My Projects', icon ='card-text')
    ], index=0, format_func='title', size='sm', indent=15, open_index=None, open_all=True, return_index=True)

if page == 0:
    st.session_state['df_all_problems'], st.session_state["company"], st.session_state["topic"] = get_all_problems(cache_time_sync)
    if home():
        st.session_state['profile_details'] = get_profile_info(st.session_state['username'], f"{st.session_state['username']}#{cache_time_sync}")
        st.success(f"**:leftwards_arrow_with_hook: Redirect to Dashboard from the side panel**")

        st.session_state['df_problems_solved_by_user'] = pd.DataFrame(st.session_state['profile_details']['solved_problems_collections'], columns = ["id"])
        st.session_state['df_problems_solved_by_user'].set_index('id', drop = True, inplace = True)
        st.session_state['df_problems_solved_by_user']['solved_status'] = 1

        st.session_state['df_all_problems_with_solved_status'] = st.session_state['df_all_problems'].join(st.session_state['df_problems_solved_by_user']['solved_status'], how = "left")
        st.session_state['df_all_problems_with_solved_status'].fillna(0, inplace = True)
        st.session_state['df_all_problems_with_solved_status']['accuracy(%) group'] = pd.cut(st.session_state['df_all_problems_with_solved_status']['accuracy(%)'], bins = 10).apply(lambda x: f'{int(x.left)}-{int(x.right)}')
        st.session_state['df_all_problems_with_solved_status']['all_submissions group'] = pd.cut(st.session_state['df_all_problems_with_solved_status']['all_submissions'], bins = 20).apply(lambda x: f'{int(x.left) if int(x.left) > 0 else 0}-{int(x.right)}')

        st.session_state['df_problems_solved_by_user'] = st.session_state['df_all_problems_with_solved_status'].query("`solved_status` == 1")
        
        st.session_state['df_problems_solved_on_each_day'] = pd.DataFrame(st.session_state['profile_details']['submissions_on_each_day'])
        st.session_state['df_problems_solved_on_each_day']['Date'] = pd.to_datetime(st.session_state['df_problems_solved_on_each_day']['Date'])
        st.session_state['df_problems_solved_on_each_day']['Total_submissions'] = st.session_state['df_problems_solved_on_each_day']['Total_submissions'].astype(int)
        st.session_state['df_problems_solved_on_each_day'].drop(st.session_state['df_problems_solved_on_each_day'][st.session_state['df_problems_solved_on_each_day']['Total_submissions'] == 0].index)
        st.session_state['df_problems_solved_on_each_day'].rename({'Total_submissions': 'Total Submissions'}, axis = 1, inplace = True)
        st.session_state['df_problems_solved_on_each_day'].sort_values(['Date'], inplace = True)

    st.markdown('''**Using this tool you can see your :green[GeeksForGeeks] Profile Performance Report in a more interactive way. This will help
                one to plan their coding journey in a more organized way and recruiters will be benefited in analysing candidates's coding progress. Please refer to :red[About Me] section for more info. :red[Best view in Desktop Mode]**''')
    lottie_col = st.columns(2)
    with lottie_col[0].container():
        st_lottie(load_lottiefile("lottie_files/Animation - 1695676263122.json"), height = 512)
    with lottie_col[1].container():
        st_lottie(load_lottiefile("lottie_files/Animation - 1695676435687.json"), height = 512) 

elif page == 2:
    if st.session_state['username'] and st.session_state['profile_details'] and st.session_state['profile_details']['username']:
        user_img(st.session_state['profile_details']['username'], f"{st.session_state['profile_details']['username']}#{cache_time_sync}")
        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)  
        def user_basic_details(hash_str):
            col1, col2 = st.columns(2)
            with col1.container():
                full_name = st.session_state['profile_details']['full_name']
                creation_date = st.session_state['profile_details']['created_date']
                clg_name = st.session_state['profile_details']['Institution_name']
                org_name = st.session_state['profile_details']['Organization_name']
                col1_nested0 = col1.columns([11, 8])
                col1_nested0[0].markdown(f"**:green[Full Name:] {full_name if full_name else 'NA'}**")
                col1_nested0[1].markdown(f"**:green[Created on:] {datetime.strptime(st.session_state['profile_details']['created_date'], '%Y-%m-%d %H:%M:%S').date() if creation_date else 'NA'}**")
                col1.markdown(f"**:green[Institution Name:] {clg_name if clg_name else 'NA'}**")
                col1.markdown(f"**:green[Organization Name:] {org_name if org_name else 'NA'}**")
                col1_nested1 = col1.columns([11, 8])
                with col1_nested1[0].container():
                    clg_rank = st.session_state['profile_details']['rank_in_institution']
                    Campus_ambassador_name = st.session_state['profile_details']['Campus_ambassador_name']
                    monthly_score = st.session_state['profile_details']['Monthly_coding_score']
                    col1_nested1[0].markdown(f"**:green[Campus Ambassador:] {Campus_ambassador_name if Campus_ambassador_name else 'NA'}**")
                    col1_nested1[0].markdown(f"**:green[Institution Rank:] {clg_rank if clg_rank else 'NA'}**")
                    col1_nested1[0].markdown(f"**:green[Monthly Coding Score:] {monthly_score}**")

                with col1_nested1[1].container():
                    registered_geeks = st.session_state['profile_details']['registered_geeks']
                    overall_score = st.session_state['profile_details']['Overall_coding_score']
                    article_published = st.session_state['profile_details']['Overall_Article_Published']
                    col1_nested1[1].markdown(f"**:green[Overall Coding Score:] {overall_score}**")
                    col1_nested1[1].markdown(f"**:green[Overall Article Published:] {article_published}**")

                col1_nested2 = col1.columns([3, 1])
                with col1_nested2[0].container():
                    Languages_used = st.session_state['profile_details']['Languages_used']
                    current_potd, global_potd = st.session_state['profile_details']['Current_POTD_Streak'], st.session_state['profile_details']['Global_POTD_Streak']
                    prog = current_potd / global_potd
                    col1_nested2[0].markdown(f"**:green[Languages Used:] {Languages_used if Languages_used else 'NA'}**")
                    col1_nested2[0].progress(prog, text = f"**:green[POTD (_Current / Global_):] {current_potd} / {global_potd} ({round(prog * 100, 2)}%)**")

            with col2.container():
                n, m = st.session_state['profile_details']['Total_problem_solved'], st.session_state['df_all_problems'].shape[0]
                prog = n / m
                col2.progress(prog if prog < 1 else 1.0, text = f"**Total Problems Solved: {n} / {m} ({round(prog * 100, 2)}%)**")

                all_problems_difficulty_count = st.session_state['df_all_problems']['difficulty'].value_counts().to_dict()
                solved_problems_difficulty_count = st.session_state['df_problems_solved_by_user']['difficulty'].value_counts().to_dict()
                col2_1, col2_2 = col2.columns(2)
                with col2_1.container():
                    for i, j in [['school', 'blue'], ['basic', 'violet'], ['easy', 'green']]:
                        n, m = solved_problems_difficulty_count[i] if i in solved_problems_difficulty_count else 0, all_problems_difficulty_count[i]
                        prog = n / m
                        col2_1.progress(prog if prog < 1 else 1.0, text = f"**:{j}[{i.capitalize()} Level:] {n} / {m} ({round(prog * 100, 2)}%)**")

                with col2_2.container():
                    for i, j in [['medium', 'orange'], ['hard', 'red']]:
                        n, m = solved_problems_difficulty_count[i] if i in solved_problems_difficulty_count else 0, all_problems_difficulty_count[i]
                        prog = n / m 
                        col2_2.progress(prog if prog < 1 else 1.0, text = f"**:{j}[{i.capitalize()} Level:] {n} / {m} ({round(prog * 100, 2)}%)**")

                col2.caption("**:red[*Note:]** Due to removal of some questions by GFG, the user's solved question will not be used in analytics and user's solved question count can be greater than actual question count.")
        
        user_basic_details(f"{st.session_state['profile_details']['username']}#{cache_time_sync}")
    else:
        st.warning(f"**Please Enter Valid username**", icon="⚠️")
elif page == 3:
    if st.session_state['username'] and st.session_state['profile_details'] and st.session_state['profile_details']['username']:
        user_img(st.session_state['profile_details']['username'], f"{st.session_state['profile_details']['username']}#{cache_time_sync}")
        years = sorted(st.session_state['df_problems_solved_on_each_day']['Date'].dt.year.unique())
        month_map_1 = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
        month_map_2 = {j: i for i, j in month_map_1.items()}
        submissions = sorted(st.session_state['df_problems_solved_on_each_day']['Total Submissions'].unique())
        last_3_months = [month_map_2[month] for month in range(month_map_1[pd.to_datetime(datetime.now(tz)).strftime('%B')] - 2 if month_map_1[pd.to_datetime(datetime.now(tz)).strftime('%B')] - 2 > 0 else 1, month_map_1[pd.to_datetime(datetime.now(tz)).strftime('%B')] + 1)]
        st.write("")

        with st.expander("##### Filters"):
            selected_year = st.multiselect("**Select Year**", years, default = int(pd.to_datetime(datetime.now(tz)).strftime('%Y')))
            selected_month = list(map(lambda x: month_map_1[x], st.multiselect("**Select Month**", month_map_1.keys(), default = last_3_months)))
            selected_submissions = st.multiselect("**Select Submission Count**", submissions, default = submissions)
        
        const_hash_str_1 = "#".join(map(str, selected_year + selected_month + selected_submissions + [st.session_state['profile_details']['username']]))

        modified_df_problems_solved_on_each_day = (st.session_state['df_problems_solved_on_each_day'][((st.session_state['df_problems_solved_on_each_day']['Date'].dt.year).isin(selected_year)) & ((st.session_state['df_problems_solved_on_each_day']['Date'].dt.month).isin(selected_month)) & ((st.session_state['df_problems_solved_on_each_day']['Total Submissions']).isin(selected_submissions))]).copy().query(f'''Date <= "{pd.to_datetime(datetime.now(tz).date())}"''')

        try:
            if selected_month and selected_year and selected_submissions:    
                weekly_problem_solved = pd.DataFrame(modified_df_problems_solved_on_each_day.groupby('Day').apply(lambda x: x['Total Submissions'].sum())) # include_groups=False
                weekly_problem_solved.sort_index(key = lambda x: x.map({'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}), inplace = True)
                weekly_problem_solved.rename(columns = {0: 'Total Submissions'}, inplace = True)
                weekly_problem_solved.reset_index(inplace = True)

                monthly_problem_solved = pd.DataFrame(modified_df_problems_solved_on_each_day.groupby(modified_df_problems_solved_on_each_day['Date'].dt.month).apply(lambda x: x['Total Submissions'].sum()))
                monthly_problem_solved.reset_index(inplace = True)
                monthly_problem_solved.rename(columns = {'Date': 'Month', 0: 'Total Submissions'}, inplace = True)
                monthly_problem_solved['Month'] = pd.to_datetime(monthly_problem_solved['Month'], format='%m').dt.month_name()

                no_of_submission_count = pd.DataFrame(modified_df_problems_solved_on_each_day['Total Submissions'].value_counts())
                no_of_submission_count = no_of_submission_count.reset_index()
                no_of_submission_count.rename({'index': 'No. of Submissions', 'Total Submissions': 'Count'}, axis = 1, inplace = True)

                modified_df_problems_solved_on_each_day['consecutive_count_submission'] = modified_df_problems_solved_on_each_day.groupby((modified_df_problems_solved_on_each_day['Total Submissions'] != modified_df_problems_solved_on_each_day['Total Submissions'].shift()).cumsum()).cumcount() + 1
                consecutive_v_total = modified_df_problems_solved_on_each_day.groupby('Total Submissions')['consecutive_count_submission'].max().reset_index()
                consecutive_v_total.set_index('Total Submissions', drop = True, inplace = True)
                consecutive_v_total = consecutive_v_total.join(modified_df_problems_solved_on_each_day['Total Submissions'].value_counts(), how = 'inner')
                consecutive_v_total.rename({'Total Submissions': 'total_count_submission'}, axis = 1, inplace = True)
                consecutive_v_total.reset_index(inplace = True)
                consecutive_v_total.rename({'index': 'Total Submissions'}, axis = 1, inplace = True)

                weekday_count_of_problems = modified_df_problems_solved_on_each_day.groupby(['Day', 'Total Submissions']).size().reset_index().rename({'Total Submissions': 'No. of Submissions', 0: 'Count'}, axis = 1)
                weekday_count_of_problems = weekday_count_of_problems.dropna()

                monthly_count_of_problems = modified_df_problems_solved_on_each_day.groupby([modified_df_problems_solved_on_each_day['Date'].dt.month, 'Total Submissions']).size().reset_index().rename({'Total Submissions': 'No. of Submissions', 'Date': 'Month', 0: 'Count'}, axis = 1)
                monthly_count_of_problems['Month'] = pd.to_datetime(monthly_count_of_problems['Month'], format='%m').dt.month_name()
                monthly_count_of_problems = monthly_count_of_problems.dropna()

                quarterly_count_of_problems = modified_df_problems_solved_on_each_day.groupby([modified_df_problems_solved_on_each_day['Date'].dt.quarter, 'Total Submissions']).size().reset_index().rename({'Total Submissions': 'No. of Submissions', 'Date': 'Quarter', 0: 'Count'}, axis = 1)
                quarterly_count_of_problems['Quarter'] = 'Q' + quarterly_count_of_problems['Quarter'].astype(int).astype(str)
                quarterly_count_of_problems = quarterly_count_of_problems.dropna()

                modified_df_problems_solved_on_each_day['Day Category'] = modified_df_problems_solved_on_each_day['Date'].dt.day.apply(lambda x: 'Early Month' if x < 12 else ('Mid Month' if x < 20 else 'Month End'))
                month_start_end_count_of_problems = (
                        modified_df_problems_solved_on_each_day
                        .groupby(['Day Category', modified_df_problems_solved_on_each_day['Date'].dt.month])
                        ['Total Submissions'].value_counts()
                        .reset_index(name='Count')
                        .rename(columns={'Total Submissions': 'No. of Submissions', 'Date': 'Month'}))
                month_start_end_count_of_problems['Month'] = pd.to_datetime(month_start_end_count_of_problems['Month'], format='%m').dt.month_name()

                model = Prophet()
                trend_df = modified_df_problems_solved_on_each_day[(modified_df_problems_solved_on_each_day['Date'] <= pd.to_datetime(datetime.now(tz).date()))][['Date', 'Total Submissions']].rename({'Date': 'ds', 'Total Submissions': 'y'}, axis = 1)
                if trend_df.shape[0] >= 2:
                    model.fit(trend_df)
                    df_pct_ch = pd.DataFrame(model.predict(model.make_future_dataframe(periods=0))['trend'].pct_change().to_list(), columns = ['pct_change'])
                    df_pct_ch.dropna(inplace = True)
                else:
                    df_pct_ch = pd.DataFrame({'pct_change': [0, 0]})
                perc = ((df_pct_ch['pct_change'].iloc[-1] - df_pct_ch['pct_change'].iloc[0]) / (df_pct_ch['pct_change'].iloc[0] if df_pct_ch['pct_change'].iloc[0] != 0 else 1)) * 100.00

                grid1 = grid([1, 1.3], vertical_align="center")
                with grid1.expander("##### Quick Statistics", expanded = True):
                    @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                    def sub_analysis_stats(hash_str):
                        today_date_query = f"Date == '{datetime.now(tz).date()}'"
                        previous_date_query = f"Date == '{datetime.now(tz).date() - timedelta(days=1)}'"
                        sac.alert(label="Only the first highest Submission in a month, weekday and particular day is mentioned.", description=None, icon=True, closable=False, banner=True, color = "red")
                        st.metric(label="**Trend in Submissions**", value = f"{modified_df_problems_solved_on_each_day['Total Submissions'].sum()}", delta = f"{perc:2f}%", delta_color="off" if perc == 0 else "normal")
                        st.markdown(f'''

                        👉 **:green[Highest Submission in a month:] {monthly_problem_solved['Total Submissions'].max()} (In {monthly_problem_solved[monthly_problem_solved['Total Submissions'] == monthly_problem_solved['Total Submissions'].max()]['Month'].to_list()[0]})**

                        👉 **:green[Highest Submission in a weekday:] {weekly_problem_solved['Total Submissions'].max()} (In {weekly_problem_solved[weekly_problem_solved['Total Submissions'] == weekly_problem_solved['Total Submissions'].max()]['Day'].to_list()[0]})**

                        👉 **:green[Highest Submission in a particular day:] {modified_df_problems_solved_on_each_day['Total Submissions'].max()} (In {modified_df_problems_solved_on_each_day[modified_df_problems_solved_on_each_day['Total Submissions'] == modified_df_problems_solved_on_each_day['Total Submissions'].max()]['Date'].to_list()[0].date()})**

                        👉 **:green[Total Submission in weekends / weekdays:] {modified_df_problems_solved_on_each_day[modified_df_problems_solved_on_each_day['Day'].isin(['Saturday', 'Sunday'])]['Total Submissions'].sum()} / {modified_df_problems_solved_on_each_day[~modified_df_problems_solved_on_each_day['Day'].isin(['Saturday', 'Sunday'])]['Total Submissions'].sum()}**

                        👉 **:green[Today's Total Submission ({datetime.now(tz).date()}):] {st.session_state['df_problems_solved_on_each_day'].query(today_date_query)["Total Submissions"].item()}**

                        👉 **:green[Yesterday's Total Submission ({datetime.now(tz).date() - timedelta(days=1)}):] {st.session_state['df_problems_solved_on_each_day'].query(previous_date_query)["Total Submissions"].item()}**
                        ''')
                    sub_analysis_stats(f'{const_hash_str_1}#{cache_time_sync}')

                
                with grid1.expander("##### Submission Count with respect to Date", expanded = True):
                    @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                    def sub_count_wrt_date_plots(hash_str):
                        sac.alert(label=f"{modified_df_problems_solved_on_each_day['Total Submissions'].sum()} Submission with max Submission of {modified_df_problems_solved_on_each_day['Total Submissions'].max()} for Day count of {modified_df_problems_solved_on_each_day[modified_df_problems_solved_on_each_day['Total Submissions'] == modified_df_problems_solved_on_each_day['Total Submissions'].max()].shape[0]}", description=None, icon=True, closable=False, banner=True, color = "red")
                        fig = px.area(modified_df_problems_solved_on_each_day, x="Date", y="Total Submissions", markers=True, height = 335)
                        fig.update_traces(line_color="red")
                        fig.update_layout(yaxis = dict(tickmode="linear", dtick=2))
                        st.plotly_chart(fig, use_container_width = True)
                    sub_count_wrt_date_plots(f'{const_hash_str_1}#{cache_time_sync}')
                
                with grid1.expander("##### Percent on each submissions", expanded = True):
                    @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                    def perc_of_each_sub_plots(hash_str):
                        sac.alert(label=f"Max Submission is {no_of_submission_count['Count'].max()} for Submission Count of {str(no_of_submission_count[no_of_submission_count['Count'] == no_of_submission_count['Count'].max()]['No. of Submissions'].to_list()).replace('[', '').replace(']', '')}", description=None, icon=True, closable=False, banner=True, color = "red")
                        fig = px.pie(no_of_submission_count, values = 'Count', names = 'No. of Submissions', height = 663, color_discrete_sequence=px.colors.sequential.Inferno, hole = 0.6)
                        st.plotly_chart(fig, use_container_width = True)
                    perc_of_each_sub_plots(f'{const_hash_str_1}#{cache_time_sync}')

                with grid1.expander("##### Monthly, Weekly & Total vs Consecutive Count on submissions", expanded = True):
                    viewmap1 = sac.tabs([
                        sac.TabsItem(label='Monthly Count'),
                        sac.TabsItem(label='Weekly Count'),
                        sac.TabsItem(label='Total Vs Consecutive Count')],
                    index=0, format_func='title', height=None, align='center', position='top', variant = 'outline', use_container_width = True, return_index=True)
                    if viewmap1 == 0:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def month_count_subs_plots(hash_str):
                            sac.alert(label=f"Max Submission is {monthly_problem_solved['Total Submissions'].max()} in the month of {str(monthly_problem_solved[monthly_problem_solved['Total Submissions'] == monthly_problem_solved['Total Submissions'].max()]['Month'].to_list()).replace('[', '').replace(']', '')}", description=None, icon=True, closable=False, banner=True, color = "red")
                            st.plotly_chart(px.bar(monthly_problem_solved, x='Month', y='Total Submissions', height = 594, text_auto = True, color='Total Submissions', color_continuous_scale = px.colors.sequential.Inferno), use_container_width = True)
                        month_count_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')
                    elif viewmap1 == 1:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def week_count_subs_plots(hash_str):
                            sac.alert(label=f"Max Submission is {weekly_problem_solved['Total Submissions'].max()} in the Weekday of {str(weekly_problem_solved[weekly_problem_solved['Total Submissions'] == weekly_problem_solved['Total Submissions'].max()]['Day'].to_list()).replace('[', '').replace(']', '')}", description=None, icon=True, closable=False, banner=True, color = "red")
                            st.plotly_chart(px.bar(weekly_problem_solved, x='Day', y='Total Submissions', height = 594, text_auto = True, color='Total Submissions', color_continuous_scale = px.colors.sequential.Inferno), use_container_width = True)
                        week_count_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')
                    elif viewmap1 == 2:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def total_vs_consecutive_count_subs_plots(hash_str):
                            sac.alert(label=f"Total Max Submission is {consecutive_v_total['total_count_submission'].max()} where No. of Problems solved for each day is {str(consecutive_v_total[consecutive_v_total['total_count_submission'] == consecutive_v_total['total_count_submission'].max()]['Total Submissions'].to_list()).replace('[', '').replace(']', '')}", description=None, icon=True, closable=False, banner=True, color = "red")
                            sac.alert(label=f"Consecutive Max Submission is {consecutive_v_total['consecutive_count_submission'].max()} where No. of Problems solved for each day is {str(consecutive_v_total[consecutive_v_total['consecutive_count_submission'] == consecutive_v_total['consecutive_count_submission'].max()]['Total Submissions'].to_list()).replace('[', '').replace(']', '')}", description=None, icon=True, closable=True, banner=True, color = "red")
                            fig = go.Figure(data=[go.Bar(name='Total count', x = consecutive_v_total['Total Submissions'], y = consecutive_v_total['total_count_submission'], text = consecutive_v_total['total_count_submission'], showlegend = False, marker=dict(color=px.colors.sequential.Inferno)), go.Bar(name = 'Consecutive count', x = consecutive_v_total['Total Submissions'], y = consecutive_v_total['consecutive_count_submission'], text = consecutive_v_total['consecutive_count_submission'], showlegend = False, marker=dict(color=px.colors.sequential.Viridis))])
                            fig.update_layout(hovermode='x unified', height = 528)
                            fig.update_xaxes(title_text='No. of Problems solved for each day')
                            fig.update_yaxes(title_text='No. of times')
                            st.plotly_chart(fig, use_container_width = True)
                        total_vs_consecutive_count_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')

                with st.expander("##### More Visualizations on Submissions", expanded = True):
                    viewmap2 = sac.tabs([
                        sac.TabsItem(label='Monthly Count'),
                        sac.TabsItem(label='Weekly Count'),
                        sac.TabsItem(label='Quarterly Count'),
                        sac.TabsItem(label='Month Start Vs End Count')],
                        index=3, format_func='title', height=None, align='center', position='top', variant = 'outline', use_container_width = True, return_index=True)
                    if viewmap2 == 0:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def month_count_sunburst_subs_plots(hash_str):
                            st.plotly_chart(px.sunburst(monthly_count_of_problems, path=['Month', 'No. of Submissions'], values='Count', height = 550, color_discrete_sequence = px.colors.sequential.Inferno), use_container_width = True)
                        month_count_sunburst_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')
                    elif viewmap2 == 1:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def week_count_sunburst_subs_plots(hash_str):
                            st.plotly_chart(px.sunburst(weekday_count_of_problems, path=['Day', 'No. of Submissions'], values='Count', height = 550, color_discrete_sequence = px.colors.sequential.Inferno), use_container_width = True)
                        week_count_sunburst_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')
                    elif viewmap2 == 2:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def quarter_count_sunburst_subs_plots(hash_str):
                            st.plotly_chart(px.sunburst(quarterly_count_of_problems, path=['Quarter', 'No. of Submissions'], values='Count', height = 550, color_discrete_sequence = px.colors.sequential.Inferno), use_container_width = True)
                        quarter_count_sunburst_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')
                    elif viewmap2 == 3:
                        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                        def month_start_vs_end_count_sunburst_subs_plots(hash_str):
                            st.plotly_chart(px.sunburst(month_start_end_count_of_problems, path=['Day Category', 'Month', 'No. of Submissions'], values='Count', height = 550, color_discrete_sequence = px.colors.sequential.Inferno), use_container_width = True)
                            st.caption("**:red[*Note:] Above sunburst chart took 1 < = Start of Month < 12 < Mid of Month < 20 < End of Month in terms of Date**")
                        month_start_vs_end_count_sunburst_subs_plots(f'{const_hash_str_1}#{cache_time_sync}')
                
                with st.expander("##### Submission Heatmap", expanded = True):
                    heatmap_year = sac.tabs([sac.TabsItem(label = str(y)) for y in years], index=len(years) - 1, format_func='title', height=None, align='center', position='top', variant = 'outline', use_container_width = True, return_index=True)
                    @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                    def sub_heatmap_plots(hash_str, y):
                        heatmap_df = st.session_state['df_problems_solved_on_each_day'][st.session_state['df_problems_solved_on_each_day']['Date'].dt.year == y]
                        per_day_sub_max = st.session_state['df_problems_solved_on_each_day']['Total Submissions'].max()
                        st.plotly_chart(calplot(heatmap_df, x = "Date", y = "Total Submissions", cmap_min = 0, cmap_max = per_day_sub_max if per_day_sub_max else 100, dark_theme=0, text = 'Total Submissions', colorscale = 'algae', total_height = 240, month_lines_width=4, month_lines_color="#fff"), use_container_width = True)        
                    sub_heatmap_plots(f'{const_hash_str_1}#{cache_time_sync}', years[heatmap_year])

            else:
                st.error("**Select atleast one year, month and submission count for visualization analysis**", icon="🚨")
        except:
            print(traceback.format_exc())
            st.error("**No data to show!**", icon = '🚨')
    else:
        st.warning(f"**Please Enter Valid username**", icon="⚠️")
elif page == 4:
    if st.session_state['username'] and st.session_state['profile_details'] and st.session_state['profile_details']['username']:
        user_img(st.session_state['profile_details']['username'], f"{st.session_state['profile_details']['username']}#{cache_time_sync}")
        st.write("")
        with st.expander("##### Filters"):
            col_solved_status = st.columns([1.8, 3, 1, 1, 1, 1], gap = "small")
            with col_solved_status[0].container():
                st.markdown('**Select Solved Status:**')
            with col_solved_status[1].container():
                selected_solved_status = sac.checkbox(items = ['Unsolved', 'Solved'], label=None, index = 1, size = "sm", format_func = None, align='start', check_all=True, return_index=True)
            
            selected_difficulty = st.multiselect("**Select Difficulty**", ['school', 'basic', 'easy', 'medium', 'hard'], default = ['school', 'basic', 'easy', 'medium', 'hard'])
            selected_accuracy_group = st.multiselect("**Select Accuracy**", st.session_state['df_all_problems_with_solved_status']['accuracy(%) group'].cat.categories.to_list(), default = st.session_state['df_all_problems_with_solved_status']['accuracy(%) group'].cat.categories.to_list())
            selected_all_submissions_group = st.multiselect("**Select Submission Count**", st.session_state['df_all_problems_with_solved_status']['all_submissions group'].cat.categories.to_list(), default = st.session_state['df_all_problems_with_solved_status']['all_submissions group'].cat.categories.to_list())
            
            filtered_df = st.session_state['df_all_problems_with_solved_status'].query(f"{selected_solved_status} in solved_status and {selected_difficulty} in difficulty and {selected_accuracy_group} in `accuracy(%) group` and {selected_all_submissions_group} in `all_submissions group`")
            selected_company = st.multiselect("**Select Company**", st.session_state["company"], placeholder = 'Choose an option (None signifies all options)', default = None)
            selected_company_operator = None
            if selected_company != []:
                selected_company_operator = sac.switch("Select Operator ?", value = False, key = 'selected_company_operator', on_label='and', off_label='or', align='start', position='left', size='sm')
                selected_company_query = f" {'and' if selected_company_operator else 'or'} ".join(map(lambda x: f"`{x}` == 1", selected_company))
                filtered_df = filtered_df.query(selected_company_query).copy()
            
            selected_topics = st.multiselect("**Select Topics**", st.session_state["topic"], placeholder = 'Choose an option (None signifies all options)', default = None)
            selected_topics_operator = None
            if selected_topics != []:
                selected_topics_operator = sac.switch("Select Operator ?", value = False, key = 'selected_topics_operator', on_label='and', off_label='or', align='start', position='left', size='sm')
                selected_topics_query = f" {'and' if selected_topics_operator else 'or'} ".join(map(lambda x: f"`{x}` == 1", selected_topics))
                filtered_df = filtered_df.query(selected_topics_query).copy()
        
        const_hash_str_2 = '#'.join(map(str, selected_solved_status + selected_difficulty + selected_accuracy_group + selected_all_submissions_group + selected_company + selected_topics + [selected_company_operator, selected_topics_operator, st.session_state['profile_details']['username']]))
    
        with st.expander("##### Accuracy(%) Vs Submission Count", expanded = True):
            interchange_axis = sac.switch(label="Interchange Axes ?", value = False, align='start', position='top', size='lg', disabled=False)
            @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
            def acc_vs_sub_plot(hash_str, interchange_axis):
                if interchange_axis:
                    fig = px.scatter(data_frame = filtered_df, x = 'accuracy(%)', y = "all_submissions", color = "difficulty", trendline = "ols", marginal_x = 'histogram', marginal_y = "box", height = 750, render_mode='auto', color_continuous_scale = px.colors.sequential.Rainbow)
                else:
                    fig = px.scatter(data_frame = filtered_df, y = 'accuracy(%)', x = "all_submissions", color = "difficulty", trendline = "ols", marginal_x = 'histogram', marginal_y = "box", height = 750, render_mode='auto', color_continuous_scale = px.colors.sequential.Rainbow)
                fig.update_layout(coloraxis = fig.layout.coloraxis)
                st.plotly_chart(fig, use_container_width = True)
            acc_vs_sub_plot(f"{const_hash_str_2}#{cache_time_sync}", interchange_axis)
            if st.toggle(label="**Generate Report ?**", key = "acc_vs_sub", value = False):
                with st.spinner("Generating Report, Please Wait..."):
                    st.toast(f"**{sketch_problem}**", icon = "⚠️")
                    a = st.session_state['df_all_problems_with_solved_status'][['accuracy(%)', 'all_submissions',	'difficulty', 'solved_status']].sketch.ask('''This dataset shows user coding problems which they have solved, solved_status signifies that if the user have solved the problem or not. A scatter plot will be plotted on y = 'accuracy(%)', x = "all_submissions", color = "difficulty", trendline = "ols", marginal_x = 'histogram', marginal_y = "box". Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                    b = st.session_state['df_all_problems_with_solved_status'][['accuracy(%)', 'all_submissions',	'difficulty', 'solved_status']].sketch.ask('''Also tell the user which group of accuracy and submission and difficulty he is currently focusing on and for which group of accuracy and submission and difficulty he should focus now in solving problems which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                    st.markdown(f'''##### Insights: 
                                {a}\n##### Suggestions:
                                {b}''')

        grid2 = grid([1, 1], vertical_align="center")
        
        with grid2.expander("##### Accuracy Vs Problem Count", expanded = True):
            accuracy_vs_difficulty_problem_count_solved_df = pd.DataFrame({"accuracy(%) group": filtered_df['accuracy(%) group'].cat.categories.to_list(), "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
            def func(df):
                for c in df['accuracy(%) group'].cat.categories.to_list():
                    tmp = df[df['accuracy(%) group'] == c].shape[0]
                    accuracy_vs_difficulty_problem_count_solved_df.loc[accuracy_vs_difficulty_problem_count_solved_df[accuracy_vs_difficulty_problem_count_solved_df['accuracy(%) group'] == c].index.item(), "Total_Solved"] += tmp
                    accuracy_vs_difficulty_problem_count_solved_df.loc[accuracy_vs_difficulty_problem_count_solved_df[accuracy_vs_difficulty_problem_count_solved_df['accuracy(%) group'] == c].index.item(), df.name] = tmp

            filtered_df.groupby(['difficulty'], group_keys=False).apply(func) # include_groups=False
            accuracy_vs_difficulty_problem_count_solved_df.reset_index(drop = True, inplace = True)
            Total_Solved_accuracy_vs_difficulty = st.number_input('**Select Problem Count [>=]**', key = 'accuracy_vs_difficulty_problem_count', min_value = 0, max_value = int(accuracy_vs_difficulty_problem_count_solved_df['Total_Solved'].max()), value = int(accuracy_vs_difficulty_problem_count_solved_df['Total_Solved'].mean()))
            accuracy_vs_difficulty_problem_count_solved_df.query(f"`Total_Solved` >= {Total_Solved_accuracy_vs_difficulty}", inplace = True)

            @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
            def accuracy_vs_difficulty_plot(hash_str):
                fig = px.line(
                    pd.melt(accuracy_vs_difficulty_problem_count_solved_df, id_vars = ['accuracy(%) group', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                    y='Problem Count',
                    x='accuracy(%) group',
                    color='Category',
                    markers = True,
                    height = 500
                    )
                st.plotly_chart(fig, use_container_width = True)
            accuracy_vs_difficulty_plot(f"{const_hash_str_2}#{Total_Solved_accuracy_vs_difficulty}#{cache_time_sync}")  

            if st.toggle(label="**Generate Report ?**", key = "accuracy_vs_difficulty", value = False):
                with st.spinner("Generating Report, Please Wait..."):
                    st.toast(f"**{sketch_problem}**", icon = "⚠️")
                    a = accuracy_vs_difficulty_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each accuracy group which each difficulties. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                    b = accuracy_vs_difficulty_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which accuracy group he is currently focusing on and for which accuracy group he should focus now in solving problems along with difficulty level which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                    st.markdown(f'''##### Insights: 
                                {a}\n##### Suggestions:
                                {b}''')

        with grid2.expander("##### Total Submission Vs Problem Count", expanded = True):
            submission_vs_difficulty_problem_count_solved_df = pd.DataFrame({"all_submissions group": filtered_df['all_submissions group'].cat.categories.to_list(), "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
            def func(df):
                for c in df['all_submissions group'].cat.categories.to_list():
                    tmp = df[df['all_submissions group'] == c].shape[0]
                    submission_vs_difficulty_problem_count_solved_df.loc[submission_vs_difficulty_problem_count_solved_df[submission_vs_difficulty_problem_count_solved_df['all_submissions group'] == c].index.item(), "Total_Solved"] += tmp
                    submission_vs_difficulty_problem_count_solved_df.loc[submission_vs_difficulty_problem_count_solved_df[submission_vs_difficulty_problem_count_solved_df['all_submissions group'] == c].index.item(), df.name] = tmp

            filtered_df.groupby(['difficulty'], group_keys=False).apply(func) # include_groups=False
            submission_vs_difficulty_problem_count_solved_df.reset_index(drop = True, inplace = True)
            Total_Solved_submission_vs_difficulty = st.number_input('**Select Problem Count [>=]**', key = 'submission_vs_difficulty_problem_count', min_value = 0, max_value = int(submission_vs_difficulty_problem_count_solved_df['Total_Solved'].max()), value = int(submission_vs_difficulty_problem_count_solved_df['Total_Solved'].mean()))
            submission_vs_difficulty_problem_count_solved_df.query(f"`Total_Solved` >= {Total_Solved_submission_vs_difficulty}", inplace = True)
            @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
            def submission_vs_difficulty_plot(hash_str):
                fig = px.line(
                    pd.melt(submission_vs_difficulty_problem_count_solved_df, id_vars = ['all_submissions group', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                    y='Problem Count',
                    x='all_submissions group',
                    color='Category',
                    markers = True,
                    height = 500
                    )
                st.plotly_chart(fig, use_container_width = True)
            submission_vs_difficulty_plot(f"{const_hash_str_2}#{Total_Solved_submission_vs_difficulty}#{cache_time_sync}")

            if st.toggle(label="**Generate Report ?**", key = "submission_vs_difficulty", value = False):
                with st.spinner("Generating Report, Please Wait..."):
                    st.toast(f"**{sketch_problem}**", icon = "⚠️")
                    a = submission_vs_difficulty_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each submission group which each difficulties. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                    b = submission_vs_difficulty_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which submission group he is currently focusing on and for which submission group he should focus now in solving problems along with difficulty level which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                    st.markdown(f'''##### Insights: 
                                {a}\n##### Suggestions:
                                {b}''')


        with grid2.expander("##### Company Wise Analysis", expanded = True):
            viewmap3 = sac.tabs([
                        sac.TabsItem(label='Problem Count and Difficulty'),
                        sac.TabsItem(label='Problem Count and Submission'),
                        sac.TabsItem(label='Problem Count and Accuracy')],
                        key = "viewmap3",
                        index=0, format_func='title', height=None, align='center', position='top', variant = 'outline', use_container_width = True, return_index=True, color = "red")
            if viewmap3 == 0:
                company_problem_count_solved_df = pd.DataFrame({"Company": st.session_state["company"], "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
                def func(df):
                    for c in st.session_state["company"]:
                        tmp = df[c].sum()
                        company_problem_count_solved_df.loc[company_problem_count_solved_df[company_problem_count_solved_df['Company'] == c].index.item(), "Total_Solved"] += tmp
                        company_problem_count_solved_df.loc[company_problem_count_solved_df[company_problem_count_solved_df['Company'] == c].index.item(), df.name] = tmp

                filtered_df.groupby(['difficulty'], group_keys=False).apply(func) # include_groups=False
                company_problem_count_solved_df.sort_values('Total_Solved', ascending = True, inplace = True)
                company_problem_count_solved_df.reset_index(drop = True, inplace = True)
                Total_company_problem_count = st.number_input('**Select Problem Count [>=]**', key = 'company_problem_count_1', min_value = 0, max_value = int(company_problem_count_solved_df['Total_Solved'].max()), value = int(company_problem_count_solved_df['Total_Solved'].mean()))
                company_problem_count_solved_df.query(f"`Total_Solved` >= {Total_company_problem_count} and `Total_Solved` > 0", inplace = True)

                @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                def company_problem_count_plot(hash_str):
                    fig = px.bar(
                        pd.melt(company_problem_count_solved_df, id_vars = ['Company', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                        x='Problem Count',
                        y='Company',
                        color='Category',
                        color_continuous_scale = px.colors.sequential.Rainbow,
                        height = 25 * company_problem_count_solved_df.shape[0] if 25 * company_problem_count_solved_df.shape[0] > 625 else 625
                        )
                    st.plotly_chart(fig, use_container_width = True)
                company_problem_count_plot(f"{const_hash_str_2}#{Total_company_problem_count}#{cache_time_sync}")

                if st.toggle(label="**Generate Report ?**", key = "company_problem_count_report_1", value = False):
                    with st.spinner("Generating Report, Please Wait..."):
                        st.toast(f"**{sketch_problem}**", icon = "⚠️")
                        a = company_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each Companies which each difficulties. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                        b = company_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which company he is currently focusing on and for which company he should focus now in solving problems along with difficulty level which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                        st.markdown(f'''##### Insights: 
                                    {a}\n##### Suggestions:
                                    {b}''')
    
            elif viewmap3 == 1:
                company_vs_submission_problem_count_solved_df = pd.DataFrame({"Company": st.session_state["company"], "Total_Solved": 0})
                def func(df):
                    for c in st.session_state["company"]:
                        if df.name not in company_vs_submission_problem_count_solved_df:
                            company_vs_submission_problem_count_solved_df[df.name] = 0
                        tmp = df[c].sum()
                        company_vs_submission_problem_count_solved_df.loc[company_vs_submission_problem_count_solved_df[company_vs_submission_problem_count_solved_df['Company'] == c].index.item(), "Total_Solved"] += tmp
                        company_vs_submission_problem_count_solved_df.loc[company_vs_submission_problem_count_solved_df[company_vs_submission_problem_count_solved_df['Company'] == c].index.item(), df.name] = tmp

                filtered_df.groupby(['all_submissions group']).apply(func)

                company_vs_submission_problem_count_solved_df.sort_values('Total_Solved', ascending = True, inplace = True)
                company_vs_submission_problem_count_solved_df.reset_index(drop = True, inplace = True)
                Total_company_vs_submission_problem_count = st.number_input('**Select Problem Count [>=]**', key = 'company_problem_count_2', min_value = 0, max_value = int(company_vs_submission_problem_count_solved_df['Total_Solved'].max()), value = int(company_vs_submission_problem_count_solved_df['Total_Solved'].mean()))
                company_vs_submission_problem_count_solved_df.query(f"`Total_Solved` >= {Total_company_vs_submission_problem_count} and `Total_Solved` > 0", inplace = True)
                
                @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                def company_vs_submission_problem_count_plot(hash_str):
                    fig = px.bar(
                        pd.melt(company_vs_submission_problem_count_solved_df, id_vars = ['Company', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                        x='Problem Count',
                        y='Company',
                        color='Category',
                        color_continuous_scale = px.colors.sequential.Plasma,
                        height = 25 * company_vs_submission_problem_count_solved_df.shape[0] if 25 * company_vs_submission_problem_count_solved_df.shape[0] > 625 else 625
                        )
                    st.plotly_chart(fig, use_container_width = True)

                company_vs_submission_problem_count_plot(f"{const_hash_str_2}#{Total_company_vs_submission_problem_count}#{cache_time_sync}")

                if st.toggle(label="**Generate Report ?**", key = "company_problem_count_report_2", value = False):
                    with st.spinner("Generating Report, Please Wait..."):
                        st.toast(f"**{sketch_problem}**", icon = "⚠️")
                        a = company_vs_submission_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each company with submission group. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                        b = company_vs_submission_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which company he is currently focusing on and for which company he should focus now in solving problems along with submission group which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                        st.markdown(f'''##### Insights: 
                                    {a}\n##### Suggestions:
                                    {b}''')
            
            elif viewmap3 == 2:
                company_vs_accuracy_problem_count_solved_df = pd.DataFrame({"Company": st.session_state["company"], "Total_Solved": 0})
                def func(df):
                    for c in st.session_state["company"]:
                        if df.name not in company_vs_accuracy_problem_count_solved_df:
                            company_vs_accuracy_problem_count_solved_df[df.name] = 0
                        tmp = df[c].sum()
                        company_vs_accuracy_problem_count_solved_df.loc[company_vs_accuracy_problem_count_solved_df[company_vs_accuracy_problem_count_solved_df['Company'] == c].index.item(), "Total_Solved"] += tmp
                        company_vs_accuracy_problem_count_solved_df.loc[company_vs_accuracy_problem_count_solved_df[company_vs_accuracy_problem_count_solved_df['Company'] == c].index.item(), df.name] = tmp

                filtered_df.groupby(['accuracy(%) group']).apply(func)

                company_vs_accuracy_problem_count_solved_df.sort_values('Total_Solved', ascending = True, inplace = True)
                company_vs_accuracy_problem_count_solved_df.reset_index(drop = True, inplace = True)
                Total_company_vs_accuracy_problem_count = st.number_input('**Select Problem Count [>=]**', key = 'company_problem_count_3', min_value = 0, max_value = int(company_vs_accuracy_problem_count_solved_df['Total_Solved'].max()), value = int(company_vs_accuracy_problem_count_solved_df['Total_Solved'].mean()))
                company_vs_accuracy_problem_count_solved_df.query(f"Total_Solved >= {Total_company_vs_accuracy_problem_count} and `Total_Solved` > 0", inplace = True)
                
                @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                def company_vs_accuracy_problem_count_plot(hash_str):
                    fig = px.bar(
                        pd.melt(company_vs_accuracy_problem_count_solved_df, id_vars = ['Company', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                        x='Problem Count',
                        y='Company',
                        color='Category',
                        color_continuous_scale = px.colors.sequential.Plasma,
                        height = 25 * company_vs_accuracy_problem_count_solved_df.shape[0] if 25 * company_vs_accuracy_problem_count_solved_df.shape[0] > 625 else 625
                        )
                    st.plotly_chart(fig, use_container_width = True)
                company_vs_accuracy_problem_count_plot(f"{const_hash_str_2}#{Total_company_vs_accuracy_problem_count}#{cache_time_sync}")

                if st.toggle(label="**Generate Report ?**", key = "company_problem_count_report_3", value = False):
                    with st.spinner("Generating Report, Please Wait..."):
                        st.toast(f"**{sketch_problem}**", icon = "⚠️")
                        a = company_vs_accuracy_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each company with accuracy group. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                        b = company_vs_accuracy_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which company he is currently focusing on and for which company he should focus now in solving problems along with accuracy group which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                        st.markdown(f'''##### Insights: 
                                    {a}\n##### Suggestions:
                                    {b}''')
            
        with grid2.expander("##### Topic Wise Analysis", expanded = True):
            viewmap4 = sac.tabs([
                        sac.TabsItem(label='Problem Count and Difficulty'),
                        sac.TabsItem(label='Problem Count and Submission'),
                        sac.TabsItem(label='Problem Count and Accuracy')],
                        key = "viewmap4",
                        index=0, format_func='title', height=None, align='center', position='top', variant = 'outline', use_container_width = True, return_index=True, color = "red")
            if viewmap4 == 0:
                topic_problem_count_solved_df = pd.DataFrame({"Topic": st.session_state["topic"], "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
                def func(df):
                    for c in st.session_state["topic"]:
                        tmp = df[c].sum()
                        topic_problem_count_solved_df.loc[topic_problem_count_solved_df[topic_problem_count_solved_df['Topic'] == c].index.item(), "Total_Solved"] += tmp
                        topic_problem_count_solved_df.loc[topic_problem_count_solved_df[topic_problem_count_solved_df['Topic'] == c].index.item(), df.name] = tmp

                filtered_df.groupby(['difficulty'], group_keys=False).apply(func) # include_groups=False
                topic_problem_count_solved_df.sort_values('Total_Solved', ascending = True, inplace = True)
                topic_problem_count_solved_df.reset_index(drop = True, inplace = True)
                Total_topic_problem_count = st.number_input('**Select Problem Count [>=]**', key = 'topic_problem_count_1', min_value = 0, max_value = int(topic_problem_count_solved_df['Total_Solved'].max()), value = int(topic_problem_count_solved_df['Total_Solved'].mean()))
                topic_problem_count_solved_df.query(f"Total_Solved >= {Total_topic_problem_count} and `Total_Solved` > 0", inplace = True)

                @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                def topic_problem_count_plot(hash_str):
                    fig = px.bar(
                        pd.melt(topic_problem_count_solved_df, id_vars = ['Topic', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                        x='Problem Count',
                        y='Topic',
                        color='Category',
                        color_continuous_scale = px.colors.sequential.Rainbow,
                        height = 25 * topic_problem_count_solved_df.shape[0] if 25 * topic_problem_count_solved_df.shape[0] > 625 else 625
                        )
                    st.plotly_chart(fig, use_container_width = True)
                topic_problem_count_plot(f"{const_hash_str_2}#{Total_topic_problem_count}#{cache_time_sync}")

                if st.toggle(label="**Generate Report ?**", key = "topic_problem_count_report_1", value = False):
                    with st.spinner("Generating Report, Please Wait..."):
                        st.toast(f"**{sketch_problem}**", icon = "⚠️")
                        a = topic_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each topics which each difficulties. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                        b = topic_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which topics he is currently focusing on and for which topics he should focus now in solving problems along with difficulty level which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                        st.markdown(f'''##### Insights: 
                                    {a}\n##### Suggestions:
                                    {b}''')
            
            elif viewmap4 == 1:
                topic_vs_submission_problem_count_solved_df = pd.DataFrame({"Topic": st.session_state["topic"], "Total_Solved": 0})
                def func(df):
                    for c in st.session_state["topic"]:
                        if df.name not in topic_vs_submission_problem_count_solved_df:
                            topic_vs_submission_problem_count_solved_df[df.name] = 0
                        tmp = df[c].sum()
                        topic_vs_submission_problem_count_solved_df.loc[topic_vs_submission_problem_count_solved_df[topic_vs_submission_problem_count_solved_df['Topic'] == c].index.item(), "Total_Solved"] += tmp
                        topic_vs_submission_problem_count_solved_df.loc[topic_vs_submission_problem_count_solved_df[topic_vs_submission_problem_count_solved_df['Topic'] == c].index.item(), df.name] = tmp

                filtered_df.groupby(['all_submissions group']).apply(func)

                topic_vs_submission_problem_count_solved_df.sort_values('Total_Solved', ascending = True, inplace = True)
                topic_vs_submission_problem_count_solved_df.reset_index(drop = True, inplace = True)
                Total_topic_vs_submission_problem_count = st.number_input('**Select Problem Count [>=]**', key = 'topic_problem_count_2', min_value = 0, max_value = int(topic_vs_submission_problem_count_solved_df['Total_Solved'].max()), value = int(topic_vs_submission_problem_count_solved_df['Total_Solved'].mean()))
                topic_vs_submission_problem_count_solved_df.query(f"Total_Solved >= {Total_topic_vs_submission_problem_count} and `Total_Solved` > 0", inplace = True)
                
                @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                def topic_vs_submission_problem_count_plot(hash_str):
                    fig = px.bar(
                        pd.melt(topic_vs_submission_problem_count_solved_df, id_vars = ['Topic', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                        x='Problem Count',
                        y='Topic',
                        color='Category',
                        color_continuous_scale = px.colors.sequential.Plasma,
                        height = 25 * topic_vs_submission_problem_count_solved_df.shape[0] if 25 * topic_vs_submission_problem_count_solved_df.shape[0] > 625 else 625
                        )
                    st.plotly_chart(fig, use_container_width = True)
                topic_vs_submission_problem_count_plot(f"{const_hash_str_2}#{Total_topic_vs_submission_problem_count}#{cache_time_sync}")

                if st.toggle(label="**Generate Report ?**", key = "topics_problem_count_report_2", value = False):
                    with st.spinner("Generating Report, Please Wait..."):
                        st.toast(f"**{sketch_problem}**", icon = "⚠️")
                        a = topic_vs_submission_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each topics along with submission group. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                        b = topic_vs_submission_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which topics he is currently focusing on and for which topics he should focus now in solving problems along with submission group which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                        st.markdown(f'''##### Insights: 
                                    {a}\n##### Suggestions:
                                    {b}''')
                        
            else:
                topic_vs_accuracy_problem_count_solved_df = pd.DataFrame({"Topic": st.session_state["topic"], "Total_Solved": 0})
                def func(df):
                    for c in st.session_state["topic"]:
                        if df.name not in topic_vs_accuracy_problem_count_solved_df:
                            topic_vs_accuracy_problem_count_solved_df[df.name] = 0
                        tmp = df[c].sum()
                        topic_vs_accuracy_problem_count_solved_df.loc[topic_vs_accuracy_problem_count_solved_df[topic_vs_accuracy_problem_count_solved_df['Topic'] == c].index.item(), "Total_Solved"] += tmp
                        topic_vs_accuracy_problem_count_solved_df.loc[topic_vs_accuracy_problem_count_solved_df[topic_vs_accuracy_problem_count_solved_df['Topic'] == c].index.item(), df.name] = tmp

                filtered_df.groupby(['accuracy(%) group']).apply(func)

                topic_vs_accuracy_problem_count_solved_df.sort_values('Total_Solved', ascending = True, inplace = True)
                topic_vs_accuracy_problem_count_solved_df.reset_index(drop = True, inplace = True)
                Total_topic_vs_accuracy_problem_count = st.number_input('**Select Problem Count [>=]**', key = 'topic_problem_count_3', min_value = 0, max_value = int(topic_vs_accuracy_problem_count_solved_df['Total_Solved'].max()), value = int(topic_vs_accuracy_problem_count_solved_df['Total_Solved'].mean()))
                topic_vs_accuracy_problem_count_solved_df.query(f"Total_Solved >= {Total_topic_vs_accuracy_problem_count} and `Total_Solved` > 0", inplace = True)
                @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
                def topic_vs_accuracy_problem_count_plot(hash_str):
                    fig = px.bar(
                        pd.melt(topic_vs_accuracy_problem_count_solved_df, id_vars = ['Topic', 'Total_Solved'], var_name='Category', value_name='Problem Count'),
                        x='Problem Count',
                        y='Topic',
                        color='Category',
                        color_continuous_scale = px.colors.sequential.Plasma,
                        height = 25 * topic_vs_accuracy_problem_count_solved_df.shape[0] if 25 * topic_vs_accuracy_problem_count_solved_df.shape[0] > 625 else 625
                        )
                    st.plotly_chart(fig, use_container_width = True)
                topic_vs_accuracy_problem_count_plot(f"{const_hash_str_2}#{Total_topic_vs_accuracy_problem_count}#{cache_time_sync}")

                if st.toggle(label="**Generate Report ?**", key = "topic_problem_count_report_3", value = False):
                    with st.spinner("Generating Report, Please Wait..."):
                        st.toast(f"**{sketch_problem}**", icon = "⚠️")
                        a = topic_vs_accuracy_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each topics along with accuracy group. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                        b = topic_vs_accuracy_problem_count_solved_df.sort_values(['Total_Solved'], ascending = False).sketch.ask('''Also tell the user which topics he is currently focusing on and for which topics he should focus now in solving problems along with accuracy group which will help in cracking the interview in brief details. Don't show statistics and length of dataset.''', call_display=False)
                        st.markdown(f'''##### Insights: 
                                    {a}\n##### Suggestions:
                                    {b}''')

        with st.expander("##### Company Vs Topic Analysis", expanded = True):
            company_topic_count_solved_df = pd.melt(filtered_df, id_vars = st.session_state["topic"], value_vars = st.session_state["company"]).query("`value` == 1").rename({'variable': 'Company'}, axis = 1).drop('value', axis = 1).groupby('Company').agg('sum').reset_index()
            company_topic_count_solved_df["Topic Count"] = company_topic_count_solved_df[st.session_state["topic"]].sum(axis = 1)
            Total_company_topic_count = st.number_input('**Select Topic Count [>=]**', key = 'company_topic_count', min_value = 0, max_value = int(company_topic_count_solved_df['Topic Count'].max()) if not(company_topic_count_solved_df.empty) else 0, value = int(company_topic_count_solved_df['Topic Count'].mean()) if not(company_topic_count_solved_df.empty) else 0)
            company_topic_count_solved_df.query(f"`Topic Count` >= {Total_company_topic_count} and `Topic Count` > 0", inplace = True)
            company_topic_count_solved_df = pd.melt(company_topic_count_solved_df, id_vars=['Company', 'Topic Count'], var_name='Topic', value_name='Count').sort_values(['Count', 'Topic Count'], ascending = False)

            @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
            def company_topic_count_plot(hash_str):
                fig = px.bar(
                    company_topic_count_solved_df,
                    y='Company',
                    x='Count',
                    color='Topic',
                    color_continuous_scale = px.colors.sequential.Plasma,
                    height=25 * company_topic_count_solved_df['Company'].unique().shape[0] if 25 * company_topic_count_solved_df['Company'].unique().shape[0] > 625 else 625,
                    orientation='h',
                )
                st.plotly_chart(fig, use_container_width = True)
            company_topic_count_plot(f"{const_hash_str_2}#{Total_company_topic_count}#{cache_time_sync}")
            
            if st.toggle(label="**Generate Report ?**", key = "company_topic_count_report", value = False):
                with st.spinner("Generating Report, Please Wait..."):
                    st.toast(f"**{sketch_problem}**", icon = "⚠️")
                    a = company_topic_count_solved_df.drop(['Topic Count'], axis = 1).sort_values(['Count'], ascending = False).sketch.ask('''This dataset shows user coding practice problems they have solved for each company and each topic. Generate a Report consisting of 15 very very useful brief insights user has done on it. Don't show statistics and length of dataset, just explain useful insights about the data.''', call_display=False)
                    b = company_topic_count_solved_df.drop(['Topic Count'], axis = 1).sort_values(['Count'], ascending = False).sketch.ask('''Also tell the user which company and topic he is currently focusing on and for which company and topic he should focus now in solving problems along with accuracy group which will help in cracking the interview in very brief details. Don't show statistics and length of dataset.''', call_display=False)
                    st.markdown(f'''##### Insights: 
                                {a}\n##### Suggestions:
                                {b}''')
    else:
        st.warning(f"**Please Enter Valid username**", icon="⚠️")
elif page == 5:
    if st.session_state['username'] and st.session_state['profile_details'] and st.session_state['profile_details']['username']:
        user_img(st.session_state['profile_details']['username'], f"{st.session_state['profile_details']['username']}#{cache_time_sync}")
        st.write("")
        with st.expander("##### Filters"):
            col_solved_status = st.columns([1.8, 3, 1, 1, 1, 1], gap = "small")
            with col_solved_status[0].container():
                st.markdown('**Select Solved Status:**')
            with col_solved_status[1].container():
                selected_solved_status = sac.checkbox(items = ['Unsolved', 'Solved'], label=None, size = "sm", index = [0, 1], format_func = None, align='start', check_all=True, return_index=True)
            selected_difficulty = st.multiselect("**Select Difficulty**", ['school', 'basic', 'easy', 'medium', 'hard'], key = 'selected_difficulty', default = ['school', 'basic', 'easy', 'medium', 'hard'])
            selected_accuracy_group = st.multiselect("**Select Accuracy**", st.session_state['df_all_problems_with_solved_status']['accuracy(%) group'].cat.categories.to_list(), key = 'selected_accuracy_group', default = st.session_state['df_all_problems_with_solved_status']['accuracy(%) group'].cat.categories.to_list())
            selected_all_submissions_group = st.multiselect("**Select Submission Count**", st.session_state['df_all_problems_with_solved_status']['all_submissions group'].cat.categories.to_list(), key = 'selected_all_submissions_group', default = st.session_state['df_all_problems_with_solved_status']['all_submissions group'].cat.categories.to_list())

            filtered_df = st.session_state['df_all_problems_with_solved_status'].query(f"{selected_solved_status} in solved_status and {selected_difficulty} in difficulty and {selected_accuracy_group} in `accuracy(%) group` and {selected_all_submissions_group} in `all_submissions group`")

            selected_company = st.multiselect("**Select Company**", st.session_state["company"], placeholder = 'Choose an option (None signifies all options)', default = None)
            selected_company_operator = None
            if selected_company != []:
                selected_company_operator = sac.switch("Select Operator ?", value = False, key = 'selected_company_operator', on_label='and', off_label='or', align='start', position='left', size='sm')
                selected_company_query = f" {'and' if selected_company_operator else 'or'} ".join(map(lambda x: f"`{x}` == 1", selected_company))
                filtered_df = filtered_df.query(selected_company_query).copy()

            selected_topics = st.multiselect("**Select Topics**", st.session_state["topic"], placeholder = 'Choose an option (None signifies all options)', default = None)
            selected_topics_operator = None
            if selected_topics != []:
                selected_topics_operator = sac.switch("Select Operator ?", value = False, key = 'selected_topics_operator', on_label='and', off_label='or', align='start', position='left', size='sm')
                selected_topics_query = f" {'and' if selected_topics_operator else 'or'} ".join(map(lambda x: f"`{x}` == 1", selected_topics))
                filtered_df = filtered_df.query(selected_topics_query).copy()
        
        const_hash_str_3 = '#'.join(map(str, selected_solved_status + selected_difficulty + selected_accuracy_group + selected_all_submissions_group + selected_company + selected_topics + [selected_company_operator, selected_topics_operator, st.session_state['profile_details']['username']]))

        @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
        def view_reports(hash_str):
            topic_count_solved_df = pd.DataFrame({"Topic": st.session_state['topic'], "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
            topic_count_df = pd.DataFrame({"Topic": st.session_state['topic'], "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
            def topic_count(df):
                for c in st.session_state['topic']:
                    tmp = df[c].sum()
                    topic_count_df.loc[topic_count_df[topic_count_df['Topic'] == c].index.item(), "Total_Solved"] += tmp
                    topic_count_df.loc[topic_count_df[topic_count_df['Topic'] == c].index.item(), df.name] = tmp

            def topic_count_solved(df):
                for c in st.session_state['topic']:
                    tmp = df[c].sum()
                    topic_count_solved_df.loc[topic_count_solved_df[topic_count_solved_df['Topic'] == c].index.item(), "Total_Solved"] += tmp
                    topic_count_solved_df.loc[topic_count_solved_df[topic_count_solved_df['Topic'] == c].index.item(), df.name] = tmp

            company_count_solved_df = pd.DataFrame({"Company": st.session_state['company'], "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
            company_count_df = pd.DataFrame({"Company": st.session_state['company'], "Total_Solved": 0, 'school': 0, 'basic': 0, 'easy': 0, 'medium': 0, 'hard': 0})
            def company_count(df):
                for c in st.session_state['company']:
                    tmp = df[c].sum()
                    company_count_df.loc[company_count_df[company_count_df['Company'] == c].index.item(), "Total_Solved"] += tmp
                    company_count_df.loc[company_count_df[company_count_df['Company'] == c].index.item(), df.name] = tmp

            def company_count_solved(df):
                for c in st.session_state['company']:
                    tmp = df[c].sum()
                    company_count_solved_df.loc[company_count_solved_df[company_count_solved_df['Company'] == c].index.item(), "Total_Solved"] += tmp
                    company_count_solved_df.loc[company_count_solved_df[company_count_solved_df['Company'] == c].index.item(), df.name] = tmp

            view_df = filtered_df.reset_index().rename(columns = {"problem_name": "Problem Name", "difficulty": "Difficulty", "solved_status": "Solved ?", "accuracy(%) group": "Accuracy(%)", "all_submissions group": "Total Submissions"})[["Problem Name", "Difficulty", "Accuracy(%)", "Total Submissions", "Solved ?", "problem_url"]]
            view_df['Solved ?'] = view_df['Solved ?'].apply(lambda x: bool(x))
            view_df['Difficulty'] = view_df['Difficulty'].apply(lambda x: x.capitalize())
            with st.expander("##### Problem Sets", expanded = True):
                st.data_editor(view_df, column_config={"problem_url": st.column_config.LinkColumn("Problem Link")}, use_container_width = True, hide_index = True, disabled = ["Problem Name", "Difficulty", "accuracy(%) group", "all_submissions group", "Solved ?", "Problem Link"])
                st.caption(f"**:green[Total Rows➡] {view_df.shape[0]}**")
                st.caption(f"**:green[Total Missing Rows (Solved by you, but not found in GFG)➡] {st.session_state['df_problems_solved_by_user'][~st.session_state['df_problems_solved_by_user'].index.isin(st.session_state['df_all_problems'].index)].shape[0]}**")

            grid3 = grid(2, vertical_align="center")

            with grid3.expander("##### Progress Report of selected Company", expanded = True):
                if selected_company:
                    st.markdown(f'''
                                * ###### :red[Selected Company:] {', '.join(selected_company)}
                                * ###### :red[Total Problems:] {view_df.shape[0]}
                                * ###### :red[Total Solved:] {view_df.query('`Solved ?` == True').shape[0]}''')
                    st.dataframe(view_df[['Difficulty', 'Solved ?']].groupby("Difficulty").agg("count").rename(columns = {'Solved ?': 'Problem Count'}).join(view_df[['Difficulty', 'Solved ?']].groupby("Difficulty").agg("sum").rename(columns = {'Solved ?': 'Solved'})), use_container_width = True)

                    filtered_df.groupby(['difficulty']).apply(topic_count)
                    topic_count_df.sort_values('Total_Solved', ascending = False, inplace = True)
                    topic_count_df.reset_index(drop = True, inplace = True)
                    topic_count_df.rename(columns = {"Total_Solved": "Problem Count", "school": "Total School", "basic": "Total Basic", "easy": "Total Easy", "medium": "Total Medium", "hard": "Total Hard"}, inplace = True)

                    filtered_df.query("solved_status == 1").groupby(['difficulty']).apply(topic_count_solved)
                    topic_count_solved_df.sort_values('Total_Solved', ascending = False, inplace = True)
                    topic_count_solved_df.reset_index(drop = True, inplace = True)
                    topic_count_solved_df.rename(columns = {"Total_Solved": "Solved", "school": "School Solved", "basic": "Basic Solved", "easy": "Easy Solved", "medium": "Medium Solved", "hard": "Hard Solved"}, inplace = True)

                    topic_count_solved_df.set_index("Topic", drop = True, inplace = True)
                    topic_count_df.set_index("Topic", drop = True, inplace = True)
                    st.dataframe(topic_count_df.join(topic_count_solved_df, how = "inner")[["Problem Count", "Solved", "Total School", "School Solved", "Total Basic", "Basic Solved", "Total Easy", "Easy Solved", "Total Medium", "Medium Solved", "Total Hard", "Hard Solved"]], use_container_width = True)
                else:
                    st.warning("**No data to show, please select a company from filter section**", icon = "⚠️")
            with grid3.expander("##### Progress Report of selected Topic", expanded = True):
                if selected_topics:
                    st.markdown(f'''
                                * ###### :red[Selected Topic:] {', '.join(selected_topics)}
                                * ###### :red[Total Problems:] {view_df.shape[0]}
                                * ###### :red[Total Solved:] {view_df.query('`Solved ?` == True').shape[0]}''')
                    st.dataframe(view_df[['Difficulty', 'Solved ?']].groupby("Difficulty").agg("count").rename(columns = {'Solved ?': 'Problem Count'}).join(view_df[['Difficulty', 'Solved ?']].groupby("Difficulty").agg("sum").rename(columns = {'Solved ?': 'Solved'})), use_container_width = True)

                    filtered_df.groupby(['difficulty']).apply(company_count)
                    company_count_df.sort_values('Total_Solved', ascending = False, inplace = True)
                    company_count_df.reset_index(drop = True, inplace = True)
                    company_count_df.rename(columns = {"Total_Solved": "Problem Count", "school": "Total School", "basic": "Total Basic", "easy": "Total Easy", "medium": "Total Medium", "hard": "Total Hard"}, inplace = True)

                    filtered_df.query("solved_status == 1").groupby(['difficulty']).apply(company_count_solved)
                    company_count_solved_df.sort_values('Total_Solved', ascending = False, inplace = True)
                    company_count_solved_df.reset_index(drop = True, inplace = True)
                    company_count_solved_df.rename(columns = {"Total_Solved": "Solved", "school": "School Solved", "basic": "Basic Solved", "easy": "Easy Solved", "medium": "Medium Solved", "hard": "Hard Solved"}, inplace = True)

                    company_count_solved_df.set_index("Company", drop = True, inplace = True)
                    company_count_df.set_index("Company", drop = True, inplace = True)
                    st.dataframe(company_count_df.join(company_count_solved_df, how = "inner")[["Problem Count", "Solved", "Total School", "School Solved", "Total Basic", "Basic Solved", "Total Easy", "Easy Solved", "Total Medium", "Medium Solved", "Total Hard", "Hard Solved"]], use_container_width = True)
                else:
                    st.warning("**No data to show, please select a topic from filter section**", icon = "⚠️")
        view_reports(f'{const_hash_str_3}#{cache_time_sync}')
    else:
        st.warning("**No data to show**", icon = "⚠️")
elif page == 6:
    if st.session_state['username'] and st.session_state['profile_details'] and st.session_state['profile_details']['username']:
        user_img(st.session_state['profile_details']['username'], f"{st.session_state['profile_details']['username']}#{cache_time_sync}")
        with st.expander("##### Paste a link of the problem present in GFG", expanded = True):
            link = st.text_input("Paste a Link", placeholder = "https://www.geeksforgeeks.org/problems/grinding-geek/0", label_visibility = 'collapsed')
            link = link[:link.find("/", 44) + 2]
            link = f'{link[:-2]}/1'
            # link = link.replace("www.", "practice.")
            if regex.match("^https:\/\/www\.geeksforgeeks\.org\/problems\/[a-zA-Z0-9-]+\/[0-9-]+$", link) and st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']["problem_url"] == link].shape[0] == 1:
                st.success("**Valid Link**", icon = "✅")
                topic_name = pd.melt(st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']["problem_url"] == link], value_vars = st.session_state['topic'], var_name = "Topics", value_name = "Solved ?").query("`Solved ?` == 1").set_index("Topics", drop = True).index
                topic_name_df = pd.DataFrame(st.session_state['df_all_problems_with_solved_status'][topic_name.to_list()].agg("sum"), columns = ['Total Problems']).join(pd.DataFrame(st.session_state['df_all_problems_with_solved_status'].query("`solved_status` == 1")[topic_name.to_list()].agg("sum"), columns = ['Problems Solved']), how = "inner")
                topic_name_df['Percentage (%)'] = round((topic_name_df["Problems Solved"] / topic_name_df["Total Problems"]) * 100, 2)
                st.dataframe(topic_name_df, use_container_width = True)

                acc = st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']["problem_url"] == link]["accuracy(%) group"].item()
                sub = st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']["problem_url"] == link]["all_submissions group"].item()

                acc_df = pd.DataFrame(st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']["accuracy(%) group"] == acc]["solved_status"].value_counts()).T.rename(columns = {0.0: "Total Problems", 1.0: "Problems Solved"})
                acc_df.index = [f"Accuracy(%) -> {acc}"]
                sub_df = pd.DataFrame(st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']["all_submissions group"] == sub]["solved_status"].value_counts()).T.rename(columns = {0.0: "Total Problems", 1.0: "Problems Solved"})
                sub_df.index = [f"Submission -> {sub}"]

                acc_sub_df = pd.concat([acc_df, sub_df])
                acc_sub_df.fillna(0, inplace = True)
                acc_sub_df['Total Problems'] += acc_sub_df['Problems Solved']
                acc_sub_df['Percentage (%)'] = round((acc_sub_df["Problems Solved"] / acc_sub_df["Total Problems"]) * 100, 2)
                st.dataframe(acc_sub_df, use_container_width = True)
                
                st.markdown(f"**:red[Asked by :]{', '.join(pd.melt(st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']['problem_url'] == link], value_vars = st.session_state['company'], var_name = 'Company', value_name = 'Solved ?').query('`Solved ?` == 1')['Company'].to_list())}**")

                st.markdown(f'''**:red[Probablity of solving:] {round(((topic_name_df['Percentage (%)'].median() if len(topic_name_df['Percentage (%)']) else 0) + (acc_sub_df['Percentage (%)'].median() if len(acc_sub_df['Percentage (%)']) else 0)) / 2, 2)} % :red[(> 10 % signifies high probablity of solving)]**''')

                st.markdown(f'''**{":red[Congo,] You have already solved this problem." if st.session_state['df_all_problems_with_solved_status'][st.session_state['df_all_problems_with_solved_status']['problem_url'] == link]['solved_status'].item() == 1 else "Currently you haven't solve this problem."}**''')
            else:
                st.warning("**Enter a link which exists in GFG Problem Set. Please run our scrapper tool from the side menu to fetch new problem sets.**", icon = "⚠️")
    else:
        st.warning("**No data to show**", icon = "⚠️")
elif page == 7:
    def create_bar(text = "Scrapping Data, Please wait... Do not change the page from the sidebar"):
        return st.progress(0, f'**{text}**')

    def progress_bar(bar, prog, text = "Scrapping Data, Please wait... Do not change the page from the sidebar"):
        bar.progress(prog, f'**{text}**')

    def empty_progress_bar(bar):
        bar.empty()

    def fetch_data():
        c = 0
        next = 1
        total = js.loads(re.get(f'https://practiceapi.geeksforgeeks.org/api/vr/problems/?pageMode=explore&page={next}').text)['total']
        inc = (1 / (total // 20))
        while next:
            response_API = re.get(f'https://practiceapi.geeksforgeeks.org/api/vr/problems/?pageMode=explore&page={next}')
            data = response_API.text
            parse_json = js.loads(data)
            next = parse_json['next']
            for problems in parse_json['results']:
                store = {'id': None, 'problem_name': None, 'accuracy': None, 'all_submissions': None, 'marks': None, 'difficulty': None, 'problem_url': None}
                for col in store:
                    store[col] = problems[col]
                store['company_tags'] = []
                store['topic_tags'] = []
                if problems['tags']['company_tags']:
                    tmp = set(problems['tags']['company_tags'])
                    store['company_tags'] = list(tmp)
                if problems['tags']['topic_tags']:
                    tmp = set(problems['tags']['topic_tags'])
                    store['topic_tags'] = list(tmp)
                all_problems.append(store)
            c += inc
            if c > 1:
                c = 1.0
            yield c

    st.header("**🆘 Help Scrapper**", anchor = False)
    st.divider()
    if st.button('Run Scrapper'):
        with st.spinner("**Please have some :coffee: while the scrapper finishes it's job**"):
            try:
                all_problems = []
                my_bar = create_bar()

                firebase = pyrebase.initialize_app(st.secrets.FIREBASE_API_KEY)
                storage = firebase.storage()

                for i in fetch_data():
                    progress_bar(my_bar, i)
                
                pickle_data = pickle.dumps(all_problems, protocol=pickle.HIGHEST_PROTOCOL)
                storage.child('all_problems_sets.pickle').put(pickle_data)
                st.success("**Thank you for your patience. Scrapper has done it's job, now you can close this page**", icon="✅")
            except:
                st.error("**Some Error occured, the developer has been informed. Thank you for your patience, now you can close this page**", icon = "🚨")
                # some notification to developer (eg. using pyrogram)
            finally:
                empty_progress_bar(my_bar)
    else:
        st.warning("**As this tool works on Scrapping GFG website, we need to stay updated for changes in the site. Please spare few mins on us to run this scrapper and do not select other pages from the sidebar until the process is finished. This Web Scrapper fetches all problem sets from the GFG website and store them in a cloud database.**", icon = "⚠️")
    st_lottie(load_lottiefile("lottie_files/Animation - 1695676527508.json"), height = 512)
elif page == 8:
    st.title(':green[GeeksForGeeks] Profile Analytics :chart_with_upwards_trend:', anchor = False)
    st.caption('**_A tool made for Coders with :heart:_**')

    @st.cache_resource(show_spinner = 0, experimental_allow_widgets=True, max_entries = max_entries)
    def about_me(date):
        st.divider()
        col = st.columns([5, 1])
        with col[0].container():
            st.markdown('''##### Hi, I am Sumit 👋\n#### A Data Analyst Aspirant From India\n**I am passionate about Data Analysis, Data Visualization, Machine Learning, Frontend and Backend Developing, Data Structures and Algorithms.**''')

        with col[1].container():
            st_lottie(load_lottiefile("lottie_files/Animation - 1694988603751.json"))

        st.divider()

        col = st.columns([2, 1])
        with col[0].container():
            st.markdown('''##### :film_projector: About the Project\n**`v1.0 Beta`**\n* **Using this website GFG users can view their profile analytics in a more broader way which will eventually help them to plan their coding journey in a more organized way and recruiters will be benefited in analysing candidates's coding progress.**\n* **Included all types of data plot for quick analysis of user's profile in a easier way.**\n* **The Website scrapes out GFG profile of the user using Selenium, BeautifulSoup and Requests Library.**\n* **Libraries Used: [`Streamlit`](https://streamlit.io/), [`Streamlit_extras`](https://extras.streamlit.app/), [`Pandas`](https://pandas.pydata.org/), [`Numpy`](https://numpy.org/), [`Plotly`](https://plotly.com/), [`Requests`](https://requests.readthedocs.io/en/latest/), [`BeautifulSoup`](https://www.crummy.com/software/BeautifulSoup/), [`Selenium`](https://www.selenium.dev/), [`Prophet`](https://facebook.github.io/prophet/), [`Pyrebase`](https://github.com/thisbejim/Pyrebase), [`Sketch`](https://github.com/approximatelabs/sketch), [`Streamlit Lottie`](https://github.com/andfanilo/streamlit-lottie/tree/main), [`Streamlit-Antd-Components`](https://github.com/nicedouble/StreamlitAntdComponents).**\n* **Implemented `Sketch` Library for quick summary of user's profile with the help of AI.**\n* **Implemented `Lottie` Animations.**\n* **Stores data in browser's cache.**\n* **This website uses caching to store data, so changes will be reflect after every 1 Hr.**\n* **During the use of AI, your information will be feeded into language models for analysis.**\n* **Open Source.**\n* **As this project is in beta stage, if you find any :red[errors] please send me a screenshot in the feedback form.**

**If this sounds interesting to you, share the website with your friends.**

**[`GitHub Repo Link >`](https://github.com/sumit10300203/Pandas-DataFrame-Viewer)**
        ''')
        
    # **If this sounds interesting to you, consider starring in my GitHub Repo.**

    # **Share the website with your friends.**

    # **[`GitHub Repo Link >`](https://bit.ly/3QT0wkx)**

        with col[1].container():
            st_lottie(load_lottiefile("lottie_files/Animation - 1694988937837.json"))
            components.html('''<iframe src="https://www.youtube-nocookie.com/embed/7CDtPeW7aqw?si=-NNWDwXRHnLybYcn" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>''')

        st.divider()

        col1 = st.columns([2, 1])

        with col1[0].container():
            st.markdown('''
        ##### 🔮 Future Work

        * **Institution based analysis**               
        * **Implementing sprint link for specific problems progress analysis**                        
        * **Comparing user's profile with others**                        
        * **Implementing Machine Learning in Can I solve ?**                        
        * **Notifying the developer about an error occured automatically**                        
        * **More Error Handling**
        ''')
        with col1[1].container():
            st_lottie(load_lottiefile("lottie_files/Animation - 1694991370591.json"), height = 200)
        st.divider()
        col2 = st.columns([2, 1])
        with col2[0].container():
            st.markdown('''
            ##### 📞 Contact with me

            * **Connect with me on [`LinkedIn >`](https://bit.ly/3DyD6cP)** 
            * **My Github Profile [`Github>`](https://github.com/sumit10300203)**           
            * **Mail me on `sumit10300203@gmail.com`** 
            * **Please leave us your Feedback on [`Feedback G-Form>`](https://forms.gle/vzVN6h7FtwCn45hw6)**
            ''')
        with col2[1].container():
            st_lottie(load_lottiefile("lottie_files/Animation - 1694990540946.json"), height = 150)

    about_me(datetime.now(tz).date())
elif page == 9:
    st.title('My Projects', anchor = False)
    card_grid = grid(3, vertical_align="center")
    with card_grid.container():
        card(
        title="Pandas Dataframe Viewer",
        text="A website for quick data analysis and visualization of your dataset with AI",
        image="https://user-images.githubusercontent.com/66067910/266804437-e9572603-7982-4b19-9732-18a079d48f5b.png",
        url="https://github.com/sumit10300203/Pandas-DataFrame-Viewer", 
        on_click = lambda: None)
    with card_grid.container():
        card(
        title="GeeksForGeeks Profile Analytics",
        text="A website to view GFG user's profile analytics for making their coding journey in a more organized way",
        image="https://media.geeksforgeeks.org/wp-content/uploads/20220413171711/gfgblack.png",
        url="https://github.com/sumit10300203/GeeksForGeeks-Profile-Analytics", 
        on_click = lambda: None)
    with card_grid.container():
        card(
        title="Thermal Power Plant Consumption Analysis in India",
        text="A PowerBI app to show analysis of power consumption in India (2017-2020) using Prophet Model",
        image="https://user-images.githubusercontent.com/66067910/259968786-4d4bf15a-8eef-4da3-8975-af3da9d22b1c.JPG",
        url="https://github.com/sumit10300203/Thermal-Power-Plant-Consumption-Analysis", 
        on_click = lambda: None)
