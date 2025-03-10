"""
module: prolific
filename: module.py
date: 09/26/2024
author: David Jurgens
desc: Defines Prolific Service for Potato
"""

import logging
from requests import request
import yaml
import os
import os.path
import pandas as pd
import requests
from collections import OrderedDict, defaultdict
import time
import json
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("Prolific Logger")

@module_getter
def __get_module():
    return Module(
        configuration=ProlificConfiguration,
        start=start_prolific,
    )

@config
class ProlificConfiguration:
    use_prolific: bool = False
    prolific_config_file_path = ""
    output_annotation_dir: str = os.getcwd()
    debug: bool = False
    verbose: bool = False

def start_prolific():
    #load prolific configurations
    if not ProlificConfiguration.use_prolific:
        return
    
    config_file_path = ProlificConfiguration.prolific_config_file_path
    if not config_file_path is None and config_file_path != "":
        raise RuntimeError(f"{config_file_path} does not exist. Please configure `prolific_config_file_path` to use prolific")
    
    # load multitask annotation config
    with open(config_file_path, "rt") as f:
        prolific_config = yaml.safe_load(f)
        max_concurrent_sessions = prolific_config.get('max_concurrent_sessions') if prolific_config.get('max_concurrent_sessions') else 30
        workload_checker_period = prolific_config.get('workload_checker_period') if prolific_config.get('workload_checker_period') else 300
        prolific_study = ProlificStudy(prolific_config['token'], prolific_config['study_id'],
                                        saving_dir = ProlificConfiguration.output_annotation_dir,
                                        max_concurrent_sessions=max_concurrent_sessions,
                                        workload_checker_period=workload_checker_period)
        
    study_basic_info = prolific_study.get_basic_study_info()
    _logger.debug('Prolific configurations successfully loaded for study: %s'%study_basic_info['internal_name'])
    for k,v in study_basic_info.items():
        _logger.debug("%s: %s"%(k, v))

    #update the submission status
    #prolific_study.update_submission_status()
    #users_to_drop = prolific_study.get_dropped_users()
    #remove_instances_from_users(users_to_drop)

def is_using_prolific():
    return ProlificConfiguration.use_prolific

def login_prolific():
    if not is_using_prolific():
        return
    
    url_arguments = ['PROLIFIC_PID']
    username = '&'.join([request.args.get(it) for it in url_arguments])
    _logger.debug("prolific logging in with %s=%s" % ('&'.join(url_arguments),username))

    # check if the provided study id is the same as the study id defined in prolific configuration file, if not,
    # pause the studies and terminate the program
    if request.args.get('STUDY_ID') != prolific_study.study_id:
        _logger.debug('ERROR: Study id (%s) does not match the study id in %s (%s), trying to pause the prolific study, \
                please check if study id is defined correctly on the server or if the study link if provided correctly \
                on prolific'%(request.args.get('STUDY_ID'),
                config['prolific']['config_file_path'], prolific_study.study_id))
        prolific_study.pause_study(study_id=request.args.get('STUDY_ID'))
        prolific_study.pause_study(study_id=prolific_study.study_id)
        quit(1)


# The base wrapper of prolific apis
class ProlificBase(object):
    def __init__(self, token):
        self.headers = {
            'Authorization': f'Token {token}',
        }

    # list all the studies
    def list_all_studies(self):
        url = 'https://api.prolific.com/api/v1/studies/'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()  # If the response contains JSON data
            studies = pd.DataFrame.from_records(data['results'])
            _logger.debug('You currently have %s studies'%len(data['results']))
            _logger.debug(studies[['id','name','study_type','internal_name','status']].to_records())
            return studies
        else:
            _logger.debug(f"Error: {response.status_code} - {response.text}")
            return None

    # get the information of a prolific study using the study id
    def get_study_by_id(self, study_id):
        if study_id == None:
            study_id = self.study_id
        url = f'https://api.prolific.com/api/v1/studies/{study_id}/'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()  # If the response contains JSON data
            return data
        else:
            _logger.debug(f"Error: {response.status_code} - {response.text}")
            return None

    #get all submissions, might be super slow when you have a long list of submissions
    def get_submissions(self):
        url = 'https://api.prolific.com/api/v1/submissions/'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()  # If the response contains JSON data
            _logger.debug('You currently have %s submissions'%len(data['results']))
            return data['results']
        else:
            _logger.debug(f"Error: {response.status_code} - {response.text}")
            return None

    # get the list of submissions from a study
    def get_submissions_from_study(self, study_id = None):
        if study_id == None:
            study_id = self.study_id
        api_endpoint = 'https://api.prolific.com/api/v1/submissions?study={}'
        url = api_endpoint.format(study_id)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()['results']
            _logger.debug('Successfully fetched %s submissions from study %s' % (len(data), study_id))
            return data
        else:
            _logger.debug(f"Error: {response.status_code} - {response.text}")
            return None
        #_logger.debug(len(data))
        #_logger.debug(data.keys())


    # get the status of a specific submission
    def get_submission_from_id(self, submission_id):
        url = f'https://api.prolific.com/api/v1/submissions/{submission_id}/'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()  # If the response contains JSON data
            return data
        else:
            _logger.debug(f"Error: {response.status_code} - {response.text}")
            return None

    # get the list of recent submissions from a study
    def get_recent_study_submissions(self, study_id):
        if study_id == None:
            study_id = self.study_id
        url = f'https://api.prolific.com/api/v1/studies/{study_id}/submissions/'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()  # If the response contains JSON data
            _logger.debug('You currently have %s submissions' % len(data['results']))
            return (data['results'])
        else:
            _logger.debug(f"Error: {response.status_code} - {response.text}")
            return None

    #get study status
    def get_study_status(self, study_id = None):
        if study_id == None:
            study_id = self.study_id
        data = self.get_study_by_id(study_id)
        if data:
            return data['status']
        else:
            return None

    #pause study based on the given study id, if id not given, use the study id
    #in the current object
    def pause_study(self, study_id = None):
        if study_id == None:
            study_id = self.study_id
        api_endpoint = 'https://api.prolific.com/api/v1/studies/{}/transition/'
        url = api_endpoint.format(study_id)
        data = {
                  "action": "PAUSE"
        }
        response = requests.post(url, headers=self.headers, json=data)
        data = response.json()
        _logger.debug(study_id, self.get_study_status(study_id))
        return data

    #start study based on the given study id, if id not given, use the study id
    #in the current object
    def start_study(self, study_id = None):
        if study_id == None:
            study_id = self.study_id
        api_endpoint = 'https://api.prolific.com/api/v1/studies/{}/transition/'
        url = api_endpoint.format(study_id)
        data = {
                  "action": "START"
        }
        response = requests.post(url, headers=self.headers, json=data)
        data = response.json()
        _logger.debug(study_id, self.get_study_status(study_id))
        return data


# The class to manage the status of a prolific study
class ProlificStudy(ProlificBase):
    def __init__(self, token, study_id, saving_dir, max_concurrent_sessions = 30, workload_checker_period = 60):
        ProlificBase.__init__(self, token)
        self.study_id = study_id
        self.study_info = self.get_study_by_id(study_id)
        self.submission_info_path = os.path.join(saving_dir, 'submissions.json')
        self.sessions = OrderedDict()
        self.user2session = {}
        #self.user_status_dict = {'RESERVED':set(), 'AWAITING REVIEW':set(), 'RETURNED':set(), 'TIMED-OUT':set(), 'ACTIVE': set(), 'APPROVED':set(), 'REJECTED':set()}
        self.study_status = None
        self.status_path = None
        self.max_concurrent_sessions = max_concurrent_sessions # How many users can work on the study at the same time
        self.checker_period = workload_checker_period
        self.workload_checker_remaining_time = workload_checker_period
        self.workload_checker_on = False

    #get the basic study information and return them as a dict
    def get_basic_study_info(self):
        keys = ['id', 'name', 'internal_name',
                'reward', 'average_reward_per_hour', 'external_study_url', 'status', 'total_available_places', 'places_taken']
        return {key:self.study_info[key] for key in keys}

    #update the submission status
    def update_submission_status(self):
        submission_data = self.get_submissions_from_study()
        with open(self.submission_info_path, "wt") as f:
            for v in submission_data:
                f.writelines(json.dumps(v) + "\n")
        self.user_status_dict = defaultdict(set)
        for v in submission_data:
            self.sessions[v['id']] = v
            #self.user2session[v['participant_id']] = v['id']
            self.user_status_dict[v['status']].add(v['participant_id'])

    # return a full list of usernames who have returned/timed-out the task or who have been rejected
    def get_dropped_users(self):
        return list(self.user_status_dict['RETURNED'] | self.user_status_dict['TIMED-OUT'] | self.user_status_dict['REJECTED'])

    # return the amount of ACTIVE session/users
    def get_concurrent_sessions_count(self):
        return len(self.user_status_dict['ACTIVE'])


    # periodically check the amount of active users, if the amount of active users is below 20% of the
    # max_concurrent_sessions resume the study on prolific
    def workload_checker(self):
        if self.workload_checker_on:
            _logger.debug('Workload checker already in process, time remaining: %s seconds' % self.workload_checker_remaining_time)
            return None
        else:
            _logger.debug('Workload checker started, checking every %s seconds'%self.checker_period)
            while True:
                self.workload_checker_remaining_time = self.checker_period
                self.workload_checker_on = True
                _logger.debug(f"\rChecking workload in: {self.checker_period} seconds")
                #time.sleep(self.checker_period)
                for i in range(self.checker_period, 0, -1):
                    #_logger.debug(f"\rChecking workload in: {i}s", end='', flush=True)
                    self.workload_checker_remaining_time -= 1
                    time.sleep(1)
                self.update_submission_status()
                if self.get_concurrent_sessions_count() < 0.2 * self.max_concurrent_sessions:
                    self.workload_checker_on = False
                    _logger.debug('current workload: ', self.get_concurrent_sessions_count(), ', resuming study %s'%self.study_id)
                    self.start_study()
                    return None
                else:
                    _logger.debug('current workload: ', self.get_concurrent_sessions_count(), ', starting another workload checker')
    '''
    
    def update_active_session_status(self):
        updated_active_session_ids = []
        for sess_id in self.session_status_sets['active']:
            status = self.get_submission_from_id(sess_id)['status']
            self.sessions[sess_id] = status
            if status != 'ACTIVE':
                self.session_status_dict[status].append(sess_id)
            else:
                updated_active_session_ids.append(sess_id)
        self.session_status_sets['active'] = updated_active_session_ids
    '''

    def update_session_status(self, sess_id):
        status = self.get_submission_from_id(sess_id)['status']
        self.sessions[sess_id]['status'] = status

    def add_new_user(self, user):
        status = self.get_submission_from_id(user['SESSION_ID'])['status']
        self.sessions[user['SESSION_ID']] = {'username':user['PROLIFIC_PID'], 'status':status}
        self.session_status_dict[status].append(user['SESSION_ID'])

def update_prolific_study_status():
    """
    Update the prolific study status
    This is the regular status update of prolific study object
    """

    global prolific_study
    global user_to_annotation_state

    _logger.debug('update_prolific_study is called')
    prolific_study.update_submission_status()
    users_to_drop = prolific_study.get_dropped_users()
    users_to_drop = [it for it in users_to_drop if it in user_to_annotation_state] # only drop the users who are currently in the data
    remove_instances_from_users(users_to_drop)

    #automatically check if there are too many users working on the task and if so, pause it
    #
    if prolific_study.get_concurrent_sessions_count() > prolific_study.max_concurrent_sessions:
        _logger.debug('Concurrent sessions (%s) exceed the predefined threshold (%s), trying to pause the prolific study'%
              (prolific_study.get_concurrent_sessions_count(), prolific_study.max_concurrent_sessions))
        prolific_study.pause_study()

        #use a separate thread to periodically check if the amount of active users are below a threshold
        th = threading.Thread(target=prolific_study.workload_checker)
        th.start()