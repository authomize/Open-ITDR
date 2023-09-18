## Install and Configuration Instructions for Quick Deployment of Script - Syslog-NG config - Syslog Splunk Config
## Instructions for Quick Deployment
1. Get an Authomize Token from your tenant
     - ```authomizeToken``` - this is the Token generated in your Authomize tenant. Go to the configurations page, click API Tokens and select a Platform Token. Insert that token into the ```config.cfg``` file.
2. DO NOT CHANGE:
    - ```authomizeURL = https://api.authomize.com/v2/incidents/search```
    - ```sentinelLog = Authomize_v2```
    - ```DateFileCFG = processdate.cfg```
3. PLEASE CHANGE:
    - ```syslog_host = 127.0.0.1 - change to remote if you have remote server setup ```
    - ```syslog_port = 514 - this is default```
4. Copy ```Azure-Sentinel\Solutions\Authomize\Data Connectors``` to a working directory ```<YourLocalWorkingDirectory>\Authomize\Data Connectors\```
5. Update the ```config.cfg``` file within the ```<YourLocalWorkingDirectory>\Authomize\Data Connectors\``` with the data you collected from points 1 and 2 above and save the file.

## Using syslog-ng with the Authomize Syslog script

`syslog-ng` is a popular syslog server used for log management. If you're using `syslog-ng`, the main configuration file is typically located at:

```
/etc/syslog-ng/syslog-ng.conf
```

However, it's not the only configuration file you might come across. Depending on your distribution and setup, `syslog-ng` might also have additional configuration files in a separate directory, such as:

```
/etc/syslog-ng/conf.d/
```

In this directory, you might find individual configuration files that are included by the main `syslog-ng.conf` file. It's a common practice to split configuration into smaller, more manageable chunks, especially in more complex setups.

To check which configuration file(s) `syslog-ng` is using, you can run the following command:

```
syslog-ng --version
```

This will display the version information and the paths to the used configuration files.

Following are basic configuration examples used by Authomize in testing and validating the syslog scripts.

The following file is an example of using syslog NG in an environment. You will need to make modifications as necessary for your environment. For detailed information please see the [syslog-ng documentation](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.33/administration-guide).

Here is an example syslog-ng.conf file:
``````
@version: 3.25
@include "scl.conf"
#
options {
    time-reap(30);
    mark-freq(10);
    time_reopen (10);
    flush_lines (0);
    log_fifo_size (1000);
    chain_hostnames (off);
    use_dns (no);
    use_fqdn (no);
    create_dirs (no);
    keep-hostname(yes);
};
#
# Reading local file as source
source s_audit {
    file("/var/log/audit/audit.log");
};
#
# All servers in 192.168.0.0/24 network will sent logs to 192.168.0.29.
source s_network {
    syslog(ip(10.0.0.6) transport("udp"));
};
#
# The received logs are saved to a specific location by segregating it to Year, month, date and hostname.
destination d_linux_logs {
    file(
        "/var/log/linuxsyslog/${YEAR}/${MONTH}/${DAY}/${HOST}-syslog.log"
        owner("root")
        group("root")
        perm(0600)
        dir_perm(0600)
        create_dirs(yes)
        );
    };
# Rule defined to save the Linux logs
log {
    source(s_network); destination(d_linux_logs);
};
#
# Audit Logs
destination d_audit_logs {
     file(
         "/var/log/linuxsyslog/audit/audit.log"
         owner("root")
         group("root")
         perm(0600)
         dir_perm(0600)
         create_dirs(yes)
         );
     };
# Rule defined to save the audit logs
log {
    source(s_audit); destination(d_audit_logs);
};
#

``````





## Using Splunk with Syslog
Authomize currently does not have a specific Application for Splunk, however depending on the version of splunk you use (cloud or on premise) you can set up Authomize to connect to your version of splunk. This document covers aspects of setting up splunk to receive Syslog information from Authomize. This requires you to deploy the syslog python script into your environment. To setup Authomize to work with HECS on your Splunk cloud instance please refer to the [following](https://github.com/authomize/Open-ITDR/blob/main/Open-Connectors/Webhooks/SplunkIncidentProcessing/README.md).

Splunk allows for ingesting, indexing, and visualizing a variety of data types, including syslog data. Here's a step-by-step guide to sending syslog data directly to Splunk:

### Prerequisites:

1. **Splunk Instance:** Have a Splunk instance up and running.
2. **Syslog Data:** Ensure that you have a device or application sending syslog data.

### Steps:

1. **Setup a Syslog Receiver on Splunk:**
   
    - You'll be configuring Splunk's built-in syslog capability. To do this, you'll need to add a data input in Splunk to listen on a specific UDP or TCP port for syslog data. Be aware the Authomize scripts have been configured for UDP only.
   
    - Navigate to **Settings** > **Data Inputs** in the Splunk web interface.
   
    - Choose **UDP**, you will need to mofify the scripts to support ***TCP***.
   
    - Click on **New** and set the port you want Splunk to listen on (e.g., `514` is the default for syslog, but it might require running Splunk as root/administrator). Ensure this port is allowed through any firewall you have.
   
    - Specify the source type as `syslog`.

2. **Configuring your Syslog Device/Application:**

    - Go to the settings or configuration section of the device or application that's generating the syslog data.
   
    - Set the syslog server to the IP address (or hostname) of your Splunk instance and specify the port you set up in the previous step.
   
    - Choose the protocol (UDP/TCP) based on your Authomize with  Splunk configuration.

3. **Data Verification in Splunk:**

    - Once the device starts sending syslog data to Splunk, you should be able to search for this data within Splunk.
    
    - In Splunk's search & reporting app, execute a broad search such as `sourcetype=syslog` to see the incoming syslog data.
    
4. **Further Configurations (Optional):**

    - **Indexing:** You may want to send the syslog data to a specific index in Splunk. When setting up the data input, you can specify the index you want to use.
   
    - **Field Extractions:** Depending on the format of your syslog data, you may want to set up field extractions in Splunk to make searching and analyzing the data easier.
   
    - **Alerting:** If you want to receive alerts based on certain syslog messages or patterns, you can set up alerts in Splunk.

5. **Considerations:**

    - **Heavy Traffic:** If you expect heavy syslog traffic, consider using Splunk's Heavy Forwarder or a dedicated syslog server (like rsyslog or syslog-ng) to preprocess the data before sending it to Splunk. This can help in load distribution and efficient processing.

    - **Secure Data Transfer:** If you're transferring sensitive data or transferring data across untrusted networks, consider using syslog over TLS or forwarding data to Splunk over SSL.

By following the above steps, you should be able to send syslog data directly to Splunk and start monitoring and analyzing your syslog data using Splunk's features.
