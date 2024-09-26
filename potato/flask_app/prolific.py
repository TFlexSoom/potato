def update_prolific_study_status():
    """
    Update the prolific study status
    This is the regular status update of prolific study object
    """

    global prolific_study
    global user_to_annotation_state

    print('update_prolific_study is called')
    prolific_study.update_submission_status()
    users_to_drop = prolific_study.get_dropped_users()
    users_to_drop = [it for it in users_to_drop if it in user_to_annotation_state] # only drop the users who are currently in the data
    remove_instances_from_users(users_to_drop)

    #automatically check if there are too many users working on the task and if so, pause it
    #
    if prolific_study.get_concurrent_sessions_count() > prolific_study.max_concurrent_sessions:
        print('Concurrent sessions (%s) exceed the predefined threshold (%s), trying to pause the prolific study'%
              (prolific_study.get_concurrent_sessions_count(), prolific_study.max_concurrent_sessions))
        prolific_study.pause_study()

        #use a separate thread to periodically check if the amount of active users are below a threshold
        th = threading.Thread(target=prolific_study.workload_checker)
        th.start()