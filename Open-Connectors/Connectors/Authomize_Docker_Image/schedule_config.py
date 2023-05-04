# schedule_config.py
scripts_to_schedule = [
    {'cron': '0 */12 * * *', 'path': '/app/atlassian/atlassian.py'}, # cron for every 12 hours at 0000 % 1200.
    {'cron': '0 */12 * * *', 'path': '/app/splunk/splunk.py'}  
    # {'cron': '0 */12 * * *', 'path': 'path/to/your/script2.py'}  # add other scripts here
]
