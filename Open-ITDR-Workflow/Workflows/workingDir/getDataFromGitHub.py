# This script allows to crawl information and repositories from
# GitHub using the GitHub REST API (https://developer.github.com/v3/search/).
#
# Given a query, the script downloads for each repository returned by the query its ZIP file.
# In addition, it also generates a CSV file containing the list of repositories queried.
# For each query, GitHub returns a json file which is processed by this script to get information
# about repositories.
#
# The GitHub API limits the queries to get 100 elements per page and up to 1,000 elements in total.
# To get more than 1,000 elements, the main query should be splitted in multiple subqueries
# using different time windows through the constant SUBQUERIES (it is a list of subqueries).
#
# As example, constant values are set to get the repositories on GitHub of the user 'rsain'.


#############
# Libraries #
#############
import json
import wget
import time
import csv
import requests
import math
import sys
import getopt

#############
# Constants #
#############

URL = "https://api.github.com/search/repositories?q="  # The basic URL to use the GitHub API
QUERY = "authomize/connectors-rest-api-client"  # The personalized query (for instance, to get repositories from user 'rsain')
SUB_QUERIES = ["+created%3A<%3D2021-03-31",
              "+created%3A>%3D2014-01-01"]  # Different sub-queries if you need to collect more than 1000 elements
PARAMETERS = "&per_page=100"  # Additional parameters for the query (by default 100 items per page)
DELAY_BETWEEN_QUERIES = 10  # The time to wait between different queries to GitHub (to avoid be banned)
OUTPUT_FOLDER = "/data/process/git/"  # Folder where ZIP files will be stored
OUTPUT_CSV_FILE = "/data/process/git/repositories.csv"  # Path to the CSV file generated as output


#############
# Functions #
#############

def getUrl(url):
    """ Given a URL it returns its body """
    response = requests.get(url)
    return response.json()


########
# MAIN #
########

#Modified to accept arguments to allow for query to be sent to github

def main(argv):
    GitOrg = ''
    GitRepo = ''
    opts, args = getopt.getopt(argv,"ho:r:",["GitOrg=","GitRepo="])
    for opt, arg in opts:
            if opt == '-h':
                print ('getDataFromGitHub.py -o <GitOrg> -r <GitRepo>')
                sys.exit()
            elif opt in ("-o", "--GitOrg"):
                GitOrg = arg
            elif opt in ("-r", "--GitRepo"):
                GitRepo = arg
    print ('Your GitHub Org: ', GitOrg)
    print ('Your GitHub Repo: ', GitRepo)
    #sys.exit()
    
    #Modify the Query so we can send data we want
    QUERY = str(GitOrg) + '/' + str(GitRepo)
    # To save the number of repositories processed
    countOfRepositories = 0
    # Output CSV file which will contain information about repositories
    csv_file = open(OUTPUT_CSV_FILE, 'w')
    repositories = csv.writer(csv_file, delimiter=',')

    # Run queries to get information in json format and download ZIP file for each repository
    for subquery in range(1, len(SUB_QUERIES) + 1):
        print("Processing subquery " + str(subquery) + " of " + str(len(SUB_QUERIES)) + " ...")
        # Obtain the number of pages for the current subquery (by default each page contains 100 items)
        url = URL + QUERY + str(SUB_QUERIES[subquery - 1]) + PARAMETERS
        data = json.loads(json.dumps(getUrl(url)))
        numberOfPages = int(math.ceil(data['total_count'] / 100.0))
        print("No. of pages = " + str(numberOfPages))
        print("No. of pages = " + str(numberOfPages))

        # Results are in different pages
        for currentPage in range(1, numberOfPages + 1):
            print("Processing page " + str(currentPage) + " of " + str(numberOfPages) + " ...")
            url = URL + QUERY + str(SUB_QUERIES[subquery - 1]) + PARAMETERS + "&page=" + str(currentPage)
            data = json.loads(json.dumps(getUrl(url)))
            # Iteration over all the repositories in the current json content page
            for item in data['items']:
                # Obtain user and repository names
                user = item['owner']['login']
                repository = item['name']
                # Download the zip file of the current project
                print("Downloading repository '%s' from user '%s' ..." % (repository, user))
                url = item['clone_url']
                fileToDownload = url[0:len(url) - 4] + "/archive/refs/heads/master.zip"
                fileName = item['full_name'].replace("/", "-") + ".zip"
                try:
                    wget.download(fileToDownload, out=OUTPUT_FOLDER + fileName)
                    repositories.writerow([user, repository, url, "downloaded"])
                except Exception as e:
                    print("Could not download file {}".format(fileToDownload))
                    print(e)
                    repositories.writerow([user, repository, url, "error when downloading"])
                # Update repositories counter
                countOfRepositories = countOfRepositories + 1

        # A delay between different sub-queries
        if subquery < len(SUB_QUERIES):
            print("Sleeping " + str(DELAY_BETWEEN_QUERIES) + " seconds before the new query ...")
            time.sleep(DELAY_BETWEEN_QUERIES)

    print("DONE! " + str(countOfRepositories) + " repositories have been processed.")
    csv_file.close()

if __name__ == "__main__":
    main(sys.argv[1:])
