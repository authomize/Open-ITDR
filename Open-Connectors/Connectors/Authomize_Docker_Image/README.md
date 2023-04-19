#### Authomize Docker Connectors (Release - .9 Beta)
- Here are the details for working directly with Authomize Docker Connectors. If you come across any issues or problems with a flow please [open an issue](https://github.com/authomize/Open-ITDR/issues).

### Getting Started

## Install Docker & Download the Open-ITDR GitHub Repo
- Ensure you have Docker installed, the following example assumes a Docker environment. https://www.docker.com/
- Clone the repository into a working directory, by using git clone like the following - 
`gh repo clone authomize/Open-ITDR` https://github.com/authomize/Open-ITDR

## Important Information
- This Docker image and its scripts contain references to Authentication Keys, Tokens and other variables. For security, simplification and easy of modifying these variables without interrupting the scripts, we use environment variables to set variables in the scripts.

## Setup Envirnnmet Variables
- Set via the .env file
- To add environment variables create a `.env` file add new lines in the following format: ENV_VARIABLE='VALUE'

Example file:
EXAMPLE_EMAIL='my_email@example.com'
ENVIRONMENT_API_KEY='my_api_key'
SERVER_DOMAIN='example.domain.net'
AUTHOMIZE_CHUNK_SIZE='1000'

## Docker Compose YML
- Edit your docker-compose.yml file. 
- Add a new `volume` for your .env file, your main Docker directory and for each script paths. 
- The format structure is: <PATH ON HOST>:<PATH ON CONTAINER>

## Schedule Setting 
- Set via schedule_config.py
- This file contains a list containing a dictionary of customizable cron and path variables. For example: `{'cron': '0 */12 * * *', 'path': '/app/atlassian/atlassian.py'}`
- Both cron and the path are customizable. We recommend however to keep each app in it's own directory.
- Once you have created your environment file, the docker-compose file and configured schedule_config.py save the changes and move on to the following steps.

## Build and Run Your Image
- In a Terminal change the directory to `<yourworkingdirectory>/Open-ITDR/Open-Connectors/Authomize_Docker_Image`
- Now create your image by typing in the following Docker command note the period '.' at the end of the line `docker build -t authomize-connectors .`
- Finally start the image by running the following command. `docker-compose up` Add the `-d` flad to run in Background Mode

## Congrats You are Now Running Authomize Docker Connectors.
- By default Connectors run at startup and then run at 0000 and 1200 thereafter.

## Hints & Example Commands:

- Build the image
`docker build -t authomize-connectors .`

- Run the Image
`docker-compose up`

- Run the Image in Background Mode
`docker-compose up -d`

- Stop the Container
`docker-compose down`

- View Docker Images
`docker images`

- View Docker Logs
`docker logs authomize-connectors`

- Remove Docker Image
`docker rmi authomize-connectors`

- Each Script Usually Outputs a Log into it's Directory
`/app/another_script/another_script.log`
