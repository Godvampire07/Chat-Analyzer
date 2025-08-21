#streamlit run app.py
import streamlit as st
import pandas as pd
import re
import helper
import preprocessor
import matplotlib.pyplot as plt
import seaborn as sns

st.title('Overall Chats:')
st.sidebar.header('WhatsApp Chat Analyzer')
st.sidebar.write('By - Godvampire07')

# File upload
file = st.sidebar.file_uploader("Upload a file")

# Ensure session state exists for selected_user
if "selected_user" not in st.session_state:
    st.session_state.selected_user = "Overall"

user_list = ["Overall"]  # Default before file upload

if file is not None:
    byte_data = file.getvalue()
    data = byte_data.decode('utf-8')
    df = preprocessor.preprocess(data)

    col1, col2 = st.columns(2)
    with col1:
      st.dataframe(df[['date', 'user', 'message']])
    with col2:
        if st.session_state.selected_user != "Overall":
            summary = helper.user_summary(st.session_state.selected_user, df)
            reply_info = helper.reply_summary(st.session_state.selected_user, df)
            summary["avg_reply_time"] = reply_info["avg_reply_time"]
            summary["reply_category"] = reply_info["reply_category"]

            if summary:
                with st.container():
                    st.title(f"📊 User Profile: {summary['user']} ")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rank", f"({summary['rank']}/{summary['total_users']})")
                        st.metric("Total Messages", summary['messages'])
                        st.metric("Contribution %", f"{summary['percent']}%")
                        st.metric("Most Active Day", summary['busy_day'])
                    with col2:
                        st.metric("🔥 Longest Streak", f"{summary['longest_streak']} days")
                        st.metric("😴 Longest Inactivity", f"{summary['longest_gap']} days")
                        st.metric("⏰ Peak Hour", f"{summary['busy_hour']}:00")
                        st.metric("⚡ Reply Speed", summary['reply_category'].split("(")[0])  # Big text
                        st.caption(f"⏱️ {summary['avg_reply_time']} min")  # Small text

    # Create user list from data
    user_list = df['user'].unique().tolist()
    if 'group_notification' in user_list:
        user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, 'Overall')

# Selectbox always visible
st.session_state.selected_user = st.sidebar.selectbox(
    'Select User', user_list, index=user_list.index(st.session_state.selected_user)
)

url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-z]{2,})'

# Analyze button
if st.sidebar.button('Analyze'):
    st.title("Analyzing for:   "+st.session_state.selected_user)

    num_msgs, words , num_media , num_links = helper.fetch_data(st.session_state.selected_user, df)

    col1, col2, col3 , col4 = st.columns(4)
    with col1:
        st.header('Number of Messages')
        st.title(num_msgs)
    with col2:
        st.header('Number of Words')
        st.title(words)
    with col3:
        st.header('Number of Media shared')
        st.title(num_media)
    with col4:
        st.header('Number of Links shared')
        st.title(num_links)

    monthly, weekly, daily = helper.timeline(st.session_state.selected_user, df)
    st.title("Monthly Status")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(monthly['date'], monthly['Message Count'], marker='o', color='blue')
    ax.set_xlabel("Month")
    ax.set_ylabel("Messages")
    ax.set_title(f"Messages per Month - {st.session_state.selected_user}")
    plt.xticks(rotation=90)
    st.pyplot(fig)
    st.title("Weekly Status")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(weekly['date'], weekly['Message Count'], marker='o', color='blue')
    ax.set_xlabel("Week")
    ax.set_ylabel("Messages")
    ax.set_title(f"Messages per Week - {st.session_state.selected_user}")
    plt.xticks(rotation=90)
    st.pyplot(fig)
    col1 , col2 = st.columns(2)
    busy_day,busy_hour = helper.weekday_timeline(st.session_state.selected_user, df)
    with col1:
        st.title("Most busy day:")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(busy_day.index, busy_day.values)
        st.pyplot(fig)
    with col2:
        st.title("Most busy hour:")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(busy_hour.index, busy_hour.values)
        st.pyplot(fig)

    col1 , col2 = st.columns(2)
    with col1:
     if st.session_state.selected_user != "Overall":
       st.write("Messages sent by:", st.session_state.selected_user)
       filtered_df = df[df['user'] == st.session_state.selected_user]
       st.dataframe(filtered_df)
       counts, total, freq = helper.emoji_stats(st.session_state.selected_user, filtered_df)
       st.write(f"### Emoji Stats for {st.session_state.selected_user}")
       st.write(f"**Total emojis used:** {total}")
       st.write(f"**Average emojis per message:** {freq:.2f}")
       st.write("**Top 10 Emojis:**")
       top_emojis = pd.DataFrame(counts.most_common(10), columns=['Emoji', 'Count'])
       st.dataframe(top_emojis)
     else:
        st.write(f"Most Unemployed Users:")
        unemp = helper.busiest_user("Overall",df)
        st.dataframe(unemp)
    with col2:
       st.write('Links shared by :',st.session_state.selected_user)
       st.dataframe( df['message'].apply(lambda msg: re.findall(url_pattern, msg)).loc[lambda s: s.str.len() > 0])
       heat_map = helper.activity_heatmap("Overall", df)
    if st.session_state.selected_user == "Overall":
      st.title("Reply Time Analysis")
      reply = helper.reply_time_analysis(st.session_state.selected_user, df)
      fig, ax = plt.subplots(figsize=(8, 4))
      ax.bar(reply.index, reply.values)
      ax.set_ylabel("Average Reply Time (minutes)")
      ax.set_xlabel("User")
      plt.xticks(rotation=90)
      st.pyplot(fig)
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(heat_map, ax=ax)
    st.pyplot(fig)




