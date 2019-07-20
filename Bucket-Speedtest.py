import time
import os
import pycurl
import sys
import numpy as np
from prettytable import PrettyTable
import argparse
import csv

# File Lists
gcp_gcs = {
    "Coldline": "https://storage.googleapis.com/rgreaves-coldline/coldline-file-100mb.txt",
    "Multi-Regional" : "https://storage.googleapis.com/rgreaves-multi-regional/multi-regional-file-100mb.txt",
    "Regional" : "https://storage.googleapis.com/rgreaves-regional/regional-file-100mb.txt",
    "Nearline" : "https://storage.googleapis.com/rgreaves-nearline/nearline-file-100mb.txt"
}
aws_s3 = {
    "Standard" : "https://rgreaves-public.s3-us-west-2.amazonaws.com/standard-100mb.txt",
    "Infrequent Access" : "https://rgreaves-public.s3-us-west-2.amazonaws.com/standard-ia-100mb.txt",
    "One Zone Infrequent Access" : "https://rgreaves-public.s3-us-west-2.amazonaws.com/one_zone-ia-100mb.txt"
}
azure_blobs = {
    "Premium Local Redundant Hot" : "https://lrshotpremium.blob.core.windows.net/public/lrshotpremium-100mb.txt",
    "Hot Local Redundant" : "https://lrsblobhot.blob.core.windows.net/public/lrsblobhot-100mb.txt",
    "Cool Local Redundant" : "https://lrsblobcool.blob.core.windows.net/public/lrsblobcool-100mb.txt",
    "Hot Regionally Redundant" : "https://rahot.blob.core.windows.net/public/rahot-100mb.txt",
    "Cool Regionally Redundant" : "https://racool.blob.core.windows.net/public/racool-100mb.txt"
}

# Parameters
version=1.0
NumItterations=''

# Results
GCP_Results = []
AWS_Results = []
AZURE_Results = []

def main():
    # Config Commandline arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--itterations", required=False,
    	help="Number of Itterations")
    ap.add_argument("-gcp", required=False, help="CSV File of two columns for GCP Files to download. CSV Format is 'Storage Type, Public URL'")
    ap.add_argument("-aws", required=False, help="CSV File of two columns for AWS Files to download. CSV Format is 'Storage Type, Public URL'")
    ap.add_argument("-azure", required=False, help="CSV File of two columns for Azure Files to download. CSV Format is 'Storage Type, Public URL'")
    args = vars(ap.parse_args())

    # Read arguments
    global NumItterations
    if args["itterations"] is not None:
        NumItterations = int(args["itterations"])
    else:
        NumItterations = 3

    # Read CSV File
    global gcp_gcs
    if args["gcp"] is not None:
        gcp_gcs = {}
        ReadTypes(args["gcp"],gcp_gcs)

    global aws_s3
    if args["aws"] is not None:
        aws_s3 = {}
        ReadTypes(args["aws"],aws_s3)

    global azure_blobs
    if args["azure"] is not None:
        azure_blobs = {}
        ReadTypes(args["azure"],azure_blobs)

    IntroText()

    # GCP Sets
    print("----- GCP Benchmark -----")
    for key, value in gcp_gcs.items():
        print("--- " + key)
        CurlFiles(key,value, GCP_Results)

    # Output results nicely
    OutPutResults(GCP_Results)

    # AWS Sets
    print("----- AWS Benchmark -----")
    for key, value in aws_s3.items():
        print("--- " + key)
        CurlFiles(key,value, AWS_Results)

    # Output results nicely
    OutPutResults(AWS_Results)

    # Azure Sets
    print("----- Azure Benchmark -----")
    for key, value in azure_blobs.items():
        print("--- " + key)
        CurlFiles(key,value, AZURE_Results)

    # Output results nicely
    OutPutResults(AZURE_Results)

def ReadTypes(InputFile, FileListArray):
    # Try to read CSV File
    try:
        # Parase CSV File and save to File List Array
        with open(InputFile) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                FileListArray[row[0]] = row[1]
    except:
        print("Unable to access file : " + InputFile)
        quit()

def IntroText():
    print("##########################")
    print("# Version: " + str(version))
    print("# Running on default parameters")
    print("# Number of Itterations Per Download: " + str(NumItterations))

    print("# GCP Files:")
    for key, value in gcp_gcs.items():
        print("# - " + key + " file = " +  value)

    print("# AWS Files:")
    for key, value in aws_s3.items():
        print("# - " + key + " file = " + value)

    print("# Azure Files:")
    for key, value in azure_blobs.items():
        print("# - " + key + " file = " +  value)

    print("##########################")

def CurlFiles(FileType, FileToGet, ResultsSet):
    # Used to save results
    results = []

    global NumItterations

    z = 0
    while z < NumItterations:
        # Used to time event
        start = time.time()

        # Build CURL event and capture metrics
        c = pycurl.Curl()
        c.setopt(pycurl.URL, FileToGet)              #set url
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        content = c.perform()                        #execute
        conn_time = c.getinfo(pycurl.CONNECT_TIME)   #TCP/IP 3-way handshaking time
        starttransfer_time = c.getinfo(pycurl.STARTTRANSFER_TIME)  #time-to-first-byte time
        total_time = c.getinfo(pycurl.TOTAL_TIME)  #last requst time
        file_size = c.getinfo(pycurl.CONTENT_LENGTH_DOWNLOAD) # File Size
        c.close()

        # Total time
        end = time.time()
        timetaken = end - start

        # Calculating download speed
        Speed = ((file_size / 1024) / 1024) / total_time

        # Save results
        results.append([conn_time,total_time,Speed])

        # Console Out Results
        print("  Itteration: " + str(z) + " | TCP/IP Handshake time: " + str(conn_time) + " (secs) | File Size: " + str(file_size) + " bytes | TTFB: " + str(starttransfer_time) + " (secs) | Time to Download: " + str(total_time) + " (secs) | Download Speed: " + str(Speed) + " (MB/s) | Total Time To Execute: " + str(timetaken) + " (secs)")

        #Increament itterations
        z += 1

    ResultsSet.append(CalcAverages(results, FileType))
    print("-------------------------")

def CalcAverages(results, FileType):
    # Used to calculate the 50%, 95% and 99% average
    # Items to average:
    # 0 = TTFB
    # 1 = Time to download
    # 2 = Speed

    TTFB_Metrics = []
    DownloadTime_Metrics = []
    Speed_Metrics = []

    # Itterate over Results
    for aResult in results:
        TTFB_Metrics.append(aResult[0])
        DownloadTime_Metrics.append(aResult[1])
        Speed_Metrics.append(aResult[2])

    # Get the Percentiles
    temp_np = np.array(TTFB_Metrics)
    TTFB_50 = np.percentile(temp_np, 50)
    TTFB_95 = np.percentile(temp_np, 95)
    TTFB_99 = np.percentile(temp_np, 99)

    temp_np = np.array(DownloadTime_Metrics)
    DownloadTime_50 = np.percentile(temp_np, 50)
    DownloadTime_95 = np.percentile(temp_np, 95)
    DownloadTime_99 = np.percentile(temp_np, 99)

    temp_np = np.array(Speed_Metrics)
    Speed_50 = np.percentile(temp_np, 50)
    Speed_95 = np.percentile(temp_np, 95)
    Speed_99 = np.percentile(temp_np, 99)

    # Output results
    print("- Averages Time To First Byte:")
    print("  50th " + str(TTFB_50) + " | 95th " + str(TTFB_95) + " | 99th " + str(TTFB_99))
    print("- Average Download Time:")
    print("  50th " + str(DownloadTime_50) + " | 95th " + str(DownloadTime_95) + " | 99th " + str(DownloadTime_99))
    print("- Average Download Speed:")
    print("  50th " + str(Speed_50) + " | 95th " + str(Speed_95) + " | 99th " + str(Speed_99))

    #Return Results
    return ([FileType,TTFB_50,TTFB_95,TTFB_99,DownloadTime_50,DownloadTime_95,DownloadTime_99,Speed_50,Speed_95,Speed_99])

def OutPutResults(ResultsSet):
    # Create a nicely formatted table
    t = PrettyTable(['Storage Type', 'TTFB 50th (secs)', 'TTFB 95th (secs)', 'TTFB 99th (secs)', 'Download Time 50th (secs)', 'Download Time 95th (secs)', 'Download Time 99th (secs)', 'Download Speed 50th (MB/s)', 'Download Speed 95th (MB/s)', 'Download Speed 99th (MB/s)'])

    for aResult in ResultsSet:
        t.add_row(aResult)
    print(t)



if __name__== "__main__":
    main()
