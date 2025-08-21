import pandas as pd
import re

def preprocess(data):
    # Pattern to match start of each message
    pattern = r'(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}) - '

    # Split into parts (first empty element is before first match)
    messages = re.split(pattern, data)[1:]  # skip first empty chunk
    dates = []
    users = []
    texts = []

    # messages comes in chunks: date, time, text, date, time, text...
    for i in range(0, len(messages), 3):
        date_str = f"{messages[i]} {messages[i+1]}"
        text = messages[i+2].strip()

        if ": " in text:
            user, msg = text.split(": ", 1)
        else:
            user = "group_notification"
            msg = text

        dates.append(date_str)
        users.append(user)
        texts.append(msg)

    df = pd.DataFrame({
        "date": pd.to_datetime(dates, format='%d/%m/%Y %H:%M', errors='coerce'),
        "user": users,
        "message": texts
    })
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour
    df['day_name'] = df['date'].dt.day_name()
    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(f"{hour}-00")
        elif hour == 0:
            period.append(f"00-{hour + 1}")
        else:
            period.append(f"{hour}-{hour + 1}")
    df['period'] = period
    return df
