FROM nodered/node-red
# Authomize Special Build version 1.0
# Copy package.json to the WORKDIR so npm builds all
# of your added nodes modules for Node-RED 
COPY package.json .
RUN npm install --unsafe-perm --no-update-notifier --no-fund --only=production
# install python
USER root
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

# setup for files
RUN mkdir -p /data/process/git
RUN mkdir -p /data/workingDir

COPY ./workingDir/getDataFromGitHub.py /data/workingDir/getDataFromGitHub.py
COPY ./workingDir/requirements.txt /data/workingDir/requirements.txt

# Run PIP after requirements in place.
RUN pip install -r /data/workingDir/requirements.txt

# Install AWS CLI
RUN apk add --no-cache \
        python3 \
        py3-pip \
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir \
        awscli \
    && rm -rf /var/cache/apk/*

RUN aws --version



# Copy _your_ Node-RED project files into place
# NOTE: This will only work if you DO NOT later mount /data as an external volume.
#       If you need to use an external volume for persistence then
#       copy your settings and flows files to that volume instead.

COPY settings.js /data/settings.js
# COPY flows_cred.json /data/flows_cred.json
COPY flows.json /data/flows.json
COPY NewAWSPolicy.json /data/NewAWSPolicy.json



# You should add extra nodes via your package.json file but you can also add them here:
#WORKDIR /usr/src/node-red
#RUN npm install node-red-node-smooth
#RUN npm install node-red-node-email