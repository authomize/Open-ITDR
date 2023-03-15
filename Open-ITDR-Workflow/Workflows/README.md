# Authomize Open Workflow Projects
## Workflows
In this area workflows will be posted, these workflows are in JSON format, exported from Node-RED hence you will be able to import these files into any Node-RED system. We have created build files specifically so that you can quickly get started.

If you wish to submit your own flows, the requirements for publishing here is as follows:

- Develop a working flow in Node-RED leveraging the Authomize APIs
- Export the workflow and dependancies
- Document workflow and store with exported JSON of your workflow
- Put in a pull request with a new directory with the above content in the Open-ITDR-Workflow area

The specific setup instructions for the Authomize flows published here can be found [here.](https://github.com/authomize/Open-ITDR/blob/main/Open-ITDR-Workflow/README.md)

## Auhomize NodeRed Docker Build version 1.0
The following build is based on the current node-red Docker [release](https://hub.docker.com/r/nodered/node-red).

We have added a few components to support the current  workflows implemented with the release Open-ITDR. Following is a list of items added:

- Python 3 along with 
    - requests==2.28.1
    - wget==3.2
- PIP 3
- AWS CLI install [more details here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Python scripts and other files to support the existing workflows

Workflows are an initial release and can be found [here](./flows.json). Import this JSON into any nodered ennvironment, note that these flows do have additional requirements and need the installation files located in this repository.
