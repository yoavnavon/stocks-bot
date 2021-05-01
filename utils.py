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


def plot_history(hist, ticker):
    # Prepare data
    hist.index.rename('index', inplace=True)
    hist = hist.reset_index()
    hist['index_str'] = hist['index'].astype(str)
    hist['index_str'] = hist.index_str.apply(lambda label: label[5:-9])

    # Plot
    _, valueax = plt.subplots(figsize=(12, 8))
    sns.lineplot(x='index_str', y='Close', data=hist, ax=valueax)
    valueax.set_xticks(np.linspace(0, len(hist)-1, num=5, dtype=int))
    valueax.set_xlabel(ticker)
    valueax.set_ylabel('value')
    valueax.tick_params(axis='x', rotation=30)
    valueax.set_ylim([hist['Close'].min() * 0.98, hist['Close'].max()])

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

    plt.savefig('image.png')
    plt.clf()
