import snowflake.connector
import streamlit as st
import pandas as pd
import plost

# import matplotlib.pyplot as plt

# with open("user_account.txt", "r") as file:
#     account, user, password = file.readlines()
#     account = account.rstrip()
#     user = user.rstrip()

id_col = "ID"
title_col = "TITLE"
week_col = "WEEK"
rank_col = "RANK_CHANGE"
rating_col = "RATING"
revenue_col = "WEEKLY_GROSS_REVENUE"
gross_col = "GROSS_CHANGE_PER_WEEK"

conn = snowflake.connector.connect(
    user="khanghoang12",
    password="Khang12102003@",
    account="ALYUXMA-GB72399",
    warehouse="COMPUTE_WH",
    database="DATA_LAKE",
    schema="GOLD",
    role="ACCOUNTADMIN",
)

cur = conn.cursor()
sql = "select * from data_lake.GOLD.WEEKLY_MOVIE_REPORT"
cur.execute(sql)
data = cur.fetch_pandas_all()
data_frame = pd.DataFrame(data)


def week_list_detection():
    week_list = []

    for i in range(len(data_frame["WEEK"])):
        if data_frame["WEEK"].iloc[i] not in week_list:
            week_list.append(data_frame["WEEK"].iloc[i])

    return week_list


def period_detection():
    week_list = ["ALL"]

    for i in range(len(data_frame["WEEK"])):
        if data_frame["WEEK"].iloc[i] not in week_list:
            week_list.append(data_frame["WEEK"].iloc[i])

    return tuple(week_list)


st.set_page_config(
    page_title="IMDB Dashboard",
    layout="wide",
    page_icon="logo.png",
    initial_sidebar_state="auto",
)

with open("style.css") as file:
    st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)

st.sidebar.header("IMDB DASHBOARD")

st.sidebar.subheader("asdasd")
detected_period = period_detection()
choosen_period = st.sidebar.selectbox("Time by week", detected_period)
if choosen_period != "ALL":
    data_frame = data_frame[data_frame["WEEK"] == choosen_period]
top = st.sidebar.selectbox("Top ", ("highest", "lowest"))
num_show = st.sidebar.selectbox(
    "Show top ", ("10", "9", "8", "7", "6", "5", "4", "3", "2", "1")
)

st.sidebar.markdown(
    """
---
By [{}](https://www.youtube.com/watch?v=dQw4w9WgXcQ)
""".format(
        "Team"
    )
)


# taking data by period
def fill_data_by_period(df):
    pass


def show_1_top(df, col, type):
    
    if type == "highest":
        sorted_df = df.sort_values(by=col, ascending=False)
    else:
        sorted_df = df.sort_values(by=col, ascending=True)

    if col == rating_col:
        for i in range(len(data_frame)):
            name = sorted_df[title_col].iloc[i]
            value = sorted_df[col].iloc[i]
            if 0 <= value <= 10:
                break
    else:
        name = sorted_df[title_col].iloc[0]
        value = sorted_df[col].iloc[0]

    if str(col) == gross_col:
        return name, str(value) + "%"

    return name, str(value)


def show_n_top(df, num, col, type):
    num = int(num)
    if type == "highest":
        sorted_df = df.sort_values(by=col, ascending=False)
    else:
        sorted_df = df.sort_values(by=col, ascending=True)

    output_list = ""
    for i in range(num):
        if col != rating_col:
            output_list += "{0}. {1} - {2}: {3}\n".format(
                i + 1, sorted_df[title_col].iloc[i], col, sorted_df[col].iloc[i]
            )
        else:
            output_list += "{0}. {1}\n".format(
                i + 1, sorted_df[title_col].iloc[i],
            )

    st.write("Top {} {}: ".format(num, type))
    st.write(output_list)


# Need uprade this function, search 'like' not 'exact'
def search_function(text, col):
    sub_cur = conn.cursor()
    sub_sql = "select * from data_lake.SILVER.MOVIES_DETAIL"
    sub_cur.execute(sub_sql)
    sub_data = sub_cur.fetch_pandas_all()
    sub_df = pd.DataFrame(sub_data)

    if text == "":
        return sub_df
    elif col == "GENRE":
        return sub_df[sub_df["GENRE"].str.contains(text, case=False, na=False)]
    elif col == "TITLE":
        return sub_df[sub_df[col].str.contains(text, case=False, na=False)]
    else:
        return sub_df[sub_df[col] == text]

def main():
    st.header("🎥 WEEKLY MOVIE IMDB DASHBOARD 🎞️")

    # DIV 1 -- list top div
    st.markdown("### Top {} value".format(top))

    col_1, col_1_blank = st.columns((9.5, 0.5))
    top_name, top_value = show_1_top(data_frame, rating_col, top)
    col_1.metric("----- Top rating", top_name, top_value)

    col_2, col_2_blank = st.columns((9.5, 0.5))
    top_name, top_value = show_1_top(data_frame, revenue_col, top)
    col_2.metric("----- Top revenue", top_name, top_value)

    col_3, col_3_blank = st.columns((9.5, 0.5))
    top_name, top_value = show_1_top(data_frame, rank_col, top)
    col_3.metric("----- Top rank change", top_name, top_value)

    col_4, col_4_blank = st.columns((9.5, 0.5))
    top_name, top_value = show_1_top(data_frame, gross_col, top)
    col_4.metric("----- Top gross change", top_name, top_value)

    # DIV 2
    c1, c2 = st.columns((6.5, 3.5))
    with c1:
        st.markdown("### Rating chart")
        st.bar_chart(data_frame[rating_col])

    with c2:
        st.markdown(f"### Top {num_show} {top}")
        show_n_top(data_frame, num_show, rating_col, top)

    # DIV 3
    c1, c2 = st.columns((6.5, 3.5))
    with c1:
        st.markdown("### Revenue chart")
        # plost.bar_chart(
        #     data=data_frame.sort_values(by=revenue_col, ascending=False),
        #     bar=title_col,
        #     value=revenue_col,
        #     color="blue",
        #     width=600,
        #     use_container_width=True,
        # )
        st.bar_chart(data_frame[revenue_col])
    with c2:
        st.markdown(f"### Top {num_show} {top}")
        show_n_top(data_frame, num_show, revenue_col, top)

    # DIV 4
    st.markdown("### Rank change chart")
    st.bar_chart(data_frame[rank_col])

    # DIV 5
    st.markdown("### Gross change chart")
    st.bar_chart(data_frame[gross_col])

    # DIV 6
    col, search_text = st.columns((3, 7))
    with col:
        col_name = st.selectbox("Column name:", ("TITLE", "ID", "RATING", "GENRE"))
    with search_text:
        search_text_value = st.text_input("Search box: ")

    res = search_function(search_text_value.title(), str(col_name))
    st.write(res)


main()
