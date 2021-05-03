import os
import boto3
from botocore.exceptions import NoCredentialsError
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=os.environ['ACCESS_KEY'],
                      aws_secret_access_key=os.environ['SECRET_KEY'])

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


def parse_date(date):
    return f"{date.day}/{date.month}-{date.hour}:{date.minute}"


def plot_history(hist, ticker):
    # Prepare data
    hist.index.rename('index', inplace=True)
    hist = hist.reset_index()
    hist['index_str'] = hist['index'].apply(parse_date)

    # Plot
    width = len(hist)//4
    height = width // 2
    _, valueax = plt.subplots(figsize=(width, height), dpi=100)
    for _, row in hist.iterrows():
        color = 'green' if row['Close'] > row['Open'] else 'red'
        valueax.vlines(row['index_str'], row['Low'], row['High'], color=color)
        valueax.vlines(row['index_str'], row['Close'],
                       row['Open'], color=color, linewidth=4)
    valueax.set_xticks(np.linspace(0, len(hist)-1, num=5, dtype=int))
    valueax.set_xlabel(ticker)
    valueax.set_ylabel('value')
    valueax.tick_params(axis='x', rotation=30)
    valueax.set_ylim([hist['Low'].min() * 0.96, hist['High'].max() * 1.01])

    volumeax = valueax.twinx()
    sns.barplot(x='index_str', y='Volume', data=hist,
                ax=volumeax, color="salmon")
    volumeax.tick_params(
        axis='y',
        right=False,
        labelright=False)
    volumeax.set_xticks(np.linspace(0, len(hist)-1, num=5, dtype=int))
    volumeax.set_ylim([0, 5 * hist['Volume'].max()])
    volumeax.set_ylabel('')
    volumeax.grid(False)
