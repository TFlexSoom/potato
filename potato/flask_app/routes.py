
@app.route("/")
def home():
    global user_config

    if config["__debug__"]:
        print("debug user logging in")
        return annotate_page("debug_user", action="home")
    if "login" in config:

        try:
            if config["login"]["type"] == "url_direct":
                url_arguments = (
                    config["login"]["url_argument"] if "url_argument" in config["login"] else "username"
                )
                if type(url_arguments) == str:
                    url_arguments = [url_arguments]
                username = '&'.join([request.args.get(it) for it in url_arguments])
                print("url direct logging in with %s=%s" % ('&'.join(url_arguments),username))
                return annotate_page(username, action="home")
            elif config["login"]["type"] == "prolific":
                #we force the order of the url_arguments for prolific logins, so that we can easily retrieve
                #the session and study information
                #url_arguments = ['PROLIFIC_PID','STUDY_ID', 'SESSION_ID']

                #Currently we still only use PROLIFIC_PID as the username, however, in the longer term, we might switch to
                # a combination of PROLIFIC_PID and SESSION id
                url_arguments = ['PROLIFIC_PID']
                username = '&'.join([request.args.get(it) for it in url_arguments])
                print("prolific logging in with %s=%s" % ('&'.join(url_arguments),username))

                # check if the provided study id is the same as the study id defined in prolific configuration file, if not,
                # pause the studies and terminate the program
                if request.args.get('STUDY_ID') != prolific_study.study_id:
                    print('ERROR: Study id (%s) does not match the study id in %s (%s), trying to pause the prolific study, \
                          please check if study id is defined correctly on the server or if the study link if provided correctly \
                          on prolific'%(request.args.get('STUDY_ID'),
                         config['prolific']['config_file_path'], prolific_study.study_id))
                    prolific_study.pause_study(study_id=request.args.get('STUDY_ID'))
                    prolific_study.pause_study(study_id=prolific_study.study_id)
                    quit()

                return annotate_page(username, action="home")
            print("password logging in")
            return render_template("home.html", title=config["annotation_task_name"])

        except:
            return render_template(
                "error.html",
                error_message="Please login to annotate or you are using the wrong link",
            )
    print("password logging in")
    return render_template("home.html", title=config["annotation_task_name"])

