# Bucket Speed Test

Python based script to curl a collection of files from different Cloud Bases Storage solutions multiple times. Then data is collected to track:
* IP/TCP Handshake duration
* Time To First Byte (TTFB)
* Download Size
* Time to Download
* Download speed (calculated on download size / time to download)
* Total time of request

After this is gathered for each download itteration the following averages are calculated:
* 50th Percentile
* 95th Percentile
* 99th Percentile

Default files are baked into the script, and can be over-ridden via flags below.
Each file is downloaded 3 times by default to generate statistics, this can be over-ridden via flags below

## Requirements
* Python3
* pip3
* libcurl4-openssl-dev
* libssl-dev

*Debian*
```
sudo apt-get update
sudo apt-get install -y libcurl4-openssl-dev libssl-dev python3 python3-pip python-pycurl
```

## Install Steps
```
git clone https://github.com/greavr/bucket-speedtest/
cd bucket-speedtest
pip3 install -r requirements.txt
```

## Steps to run the script
```
python3 Bucket-Speedtest.py
```
This will download a set of sample file from GCP, AWS, Azure which repesents each class of storage. Some Caveats:
AWS Glacier is not able to make files publicly accessible, and must be called via API.

## Advanced
```
python Bucket-Speedtest.py -h
```
This will output a list of all *optional* parameters, listed below:
```
-i Is the number of times each file should be downloaded to generate the averages
-gcp This points to a CSV file which contains the GCS Storage Class and path to public file
-aws This points to a CSV file which contains the AWS Storage Class and path to public file
-azure This points to a CSV file which contains the Azure Storage Class and path to public file
```

### Example
```
python Bucket-Speedtest.py -5 -gcp gcp-files.csv
```
This will download each file 5 times, and will use a custom list of GCP files parsed from gcp-files.csv

## Questions
Please reach out to rgreaves@google.com
