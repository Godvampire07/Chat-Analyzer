import re
import pandas as pd


url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-z]{2,})'
def fetch_data(selected_user,df):
    if selected_user == "Overall":
        num_msgs = df.shape[0]
        words = []
        for message in df['message']:
            words.extend(message.split())
        num_media = df[df['message'] == '<Media omitted>'].shape[0]
        total_urls = df['message'].apply(lambda msg: len(re.findall(url_pattern, msg))).sum()
        return num_msgs, len(words), num_media , total_urls
    else:
        filtered_df = df[df['user'] == selected_user]
        num_msgs = filtered_df.shape[0]
        words = []
        for message in filtered_df['message']:
            words.extend(message.split())
        num_media = df[df['message'] == '<Media omitted>'].shape[0]
        total_urls = df['message'].apply(lambda msg: len(re.findall(url_pattern, msg))).sum()
        return num_msgs, len(words), num_media , total_urls

def user_summary(selected_user, df):
    if selected_user != "Overall":
        user_df = df[df['user'] == selected_user]
    else:
        user_df = df.copy()
    total_users = df["user"].nunique()
    messages = user_df.shape[0]
    percent = round((messages / df.shape[0]) * 100, 2) if df.shape[0] > 0 else 0
    rank = df['user'].value_counts().reset_index().reset_index()
    rank.columns = ['rank', 'user', 'messages']
    rank['rank'] += 1
    user_rank = rank.loc[rank['user'] == selected_user, 'rank'].values[0] if selected_user != "Overall" else None

    # Busy day & hour
    busy_day = user_df['date'].dt.day_name().value_counts().idxmax()
    busy_hour = user_df['date'].dt.hour.value_counts().idxmax()

    # Streaks & inactivity
    longest_streak, longest_gap = streaks_inactivity(selected_user,df)

    # Reply time
    reply_df = user_df.sort_values("date").reset_index(drop=True)
    reply_df["reply_time"] = reply_df["date"].diff().dt.total_seconds().div(60)
    avg_reply_time = round(reply_df["reply_time"].mean(), 2) if not reply_df["reply_time"].empty else 0

    # Categorize reply speed
    if avg_reply_time <= 2:
        reply_category = "⚡ Instant Replier"
    elif avg_reply_time <= 100:
        reply_category = "⏱️ Quick Responder"
    elif avg_reply_time <= 200:
        reply_category = "⌛ Moderate"
    else:
        reply_category = "🐢 Slow Replier"

    return {
        "user": selected_user,
        "messages": messages,
        "percent": percent,
        "rank": int(user_rank) if user_rank else "N/A",
        "busy_day": busy_day,
        "busy_hour": busy_hour,
        "longest_streak": longest_streak,
        "longest_gap": longest_gap,
        "avg_reply_time": avg_reply_time,
        "reply_category": reply_category,   # 👈 now included
        "total_users": total_users
    }



emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002600-\U000026FF"  # misc symbols
    "]+", flags=re.UNICODE
)
def extract_emojis(s):
    return emoji_pattern.findall(s)

def emoji_stats(selected_user, df):
    if selected_user != "Overall":
        df = df[df['user'] == selected_user]

    # Extract emojis from each message
    df['emojis'] = df['message'].apply(extract_emojis)

    # Flatten list of emojis
    all_emojis = sum(df['emojis'], [])  # concatenates lists

    # Emoji frequency
    from collections import Counter
    emoji_count = Counter(all_emojis)

    # Usage frequency: emojis per message
    total_messages = df.shape[0]
    total_emojis = sum(emoji_count.values())
    freq_per_message = total_emojis / total_messages if total_messages > 0 else 0

    return emoji_count, total_emojis, freq_per_message

def busiest_user(selected_user, df):
    if selected_user == "Overall":
        x = df['user'].value_counts().head(5)
        return x

def timeline(selected_user, df):
    if selected_user != "Overall":df = df[df['user'] == selected_user]
    daily_timeline = (df.groupby(df['date'].dt.date).size().reset_index(name="Message Count"))
    monthly_timeline = (df.groupby(df['date'].dt.to_period("M")).size().reset_index(name="Message Count"))
    monthly_timeline['date'] = monthly_timeline['date'].dt.to_timestamp()
    weekly_timeline = (df.groupby(df['date'].dt.to_period("W")).size().reset_index(name="Message Count"))
    weekly_timeline['date'] = weekly_timeline['date'].dt.start_time

    return daily_timeline, monthly_timeline, weekly_timeline

def weekday_timeline(selected_user, df):
    if selected_user != "Overall":df = df[df['user'] == selected_user]
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    return df['day_name'].value_counts(), df['hour'].value_counts().sort_index()

def activity_heatmap(selected_user, df):
    if selected_user != "Overall":
        df = df[df['user'] == selected_user]
    heatmap = df.pivot_table(index='day_name',columns='period', values='message', aggfunc='count').fillna(0)

    return heatmap


def reply_time_analysis(selected_user, df):
    # Filter for a specific user or overall
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # Sort by datetime
    df = df.sort_values("date").reset_index(drop=True)

    # Calculate time difference between consecutive messages
    df["reply_time"] = df["date"].diff().dt.total_seconds().div(60)  # in minutes

    # Ignore group notifications
    reply_times = df[df["user"] != "group_notification"].groupby("user")["reply_time"].mean().sort_values()
    return reply_times

def streaks_inactivity(selected_user, df):
    # filter if not overall
    if selected_user != "Overall":
        df = df[df['user'] == selected_user]

    # make sure we only use datetime
    active_days = df['date'].dt.normalize().dropna().unique()  # keep only date part
    active_days = pd.to_datetime(sorted(active_days))          # ensure datetime index
    active_days = pd.Series(active_days)

    # differences in days
    gaps = active_days.diff().dt.days.fillna(1)

    # longest streak of consecutive days
    longest_streak = (gaps == 1).astype(int).groupby((gaps != 1).cumsum()).cumsum().max()
    longest_gap = int(gaps.max())

    return int(longest_streak), longest_gap


def reply_summary(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # Remove group notifications
    reply_df = df[df["user"] != "group_notification"].copy()

    if reply_df.empty:  # No valid messages
        return {"avg_reply_time": None, "reply_category": "No Replies ❌"}

    # Sort & calculate reply time (in minutes)
    reply_df = reply_df.sort_values("date").reset_index(drop=True)
    reply_df["reply_time"] = reply_df["date"].diff().dt.total_seconds().div(60)

    avg_reply_time = reply_df["reply_time"].mean()

    if pd.isna(avg_reply_time):
        reply_category = "No Replies ❌"
    else:
        if avg_reply_time < 2:
            reply_category = "Instant Replier ⚡"
        elif avg_reply_time < 10:
            reply_category = "Fast Replier 🚀"
        elif avg_reply_time < 60:
            reply_category = "Normal Chatter 💬"
        elif avg_reply_time < 360:
            reply_category = "Slow Replier 🐢"
        else:
            reply_category = "Ghost 👻"

    return {
        "avg_reply_time": round(avg_reply_time, 2) if not pd.isna(avg_reply_time) else None,
        "reply_category": f"{reply_category} ({round(avg_reply_time, 2)} min)" if avg_reply_time else reply_category
    }