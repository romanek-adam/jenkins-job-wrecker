# encoding=utf8
from __future__ import print_function

import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool, Mapper


class Publishers(jenkins_job_wrecker.modules.base.Base):
    component = 'publishers'

    def gen_yml(self, yml_parent, data):
        publishers = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            self.registry.dispatch(self.component, object_name, child, publishers)
        yml_parent.append(['publishers', publishers])


def artifactarchiver(top, parent):
    archive = {}
    for element in top:
        if element.tag == 'artifacts':
            archive['artifacts'] = element.text
        elif element.tag == 'allowEmptyArchive':
            archive['allow-empty'] = get_bool(element.text)
        elif element.tag == 'fingerprint':
            archive['fingerprint'] = get_bool(element.text)
        elif element.tag == 'onlyIfSuccessful':
            # only-if-success first available in JJB 1.3.0
            archive['only-if-success'] = get_bool(element.text)
        elif element.tag == 'defaultExcludes':
            # default-excludes is not yet available in JJB master
            archive['default-excludes'] = get_bool(element.text)
        elif element.tag == 'latestOnly':
            archive['latest-only'] = get_bool(element.text)
        elif element.tag == 'caseSensitive':
            archive['case-sensitive'] = get_bool(element.text)
        elif element.tag == 'excludes':
            archive['excludes'] = element.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)

    parent.append({'archive': archive})


def descriptionsetterpublisher(top, parent):
    setter = {}
    for element in top:
        if element.tag == 'regexp':
            setter['regexp'] = element.text
        elif element.tag == 'regexpForFailed':
            setter['regexp-for-failed'] = element.text
        elif element.tag == 'setForMatrix':
            setter['set-for-matrix'] = (element.text == 'true')
        elif element.tag == 'description':
            setter['description'] = element.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)

    parent.append({'description-setter': setter})


def fingerprinter(top, parent):
    fingerprint = {}
    for element in top:
        if element.tag == 'targets':
            fingerprint['files'] = element.text
        elif element.tag == 'recordBuildArtifacts':
            fingerprint['record-artifacts'] = (element.text == 'true')
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'fingerprint': fingerprint})


def __process_email(trigger, ext_email, provider_dict):
    email_contents = ["subject", "recipientProviders", "body",
                      "attachmentsPattern", "attachBuildLog", "compressBuildLog",
                      "replyTo", "contentType"]
    for email in trigger:
        if email.tag == "email":
            send_to = []
            for email_child in email:
                if email_child.tag == "recipientProviders":
                    for provider in email_child:
                        if provider.tag in provider_dict.keys():
                            send_to.append(provider_dict[provider.tag])
                        else:
                            raise NotImplementedError("Provider %s under recipientProviders is not implemented."
                                                      % provider.tag)
                elif email_child.tag in email_contents:
                    pass  # We only need to process recipientProviders here.
                else:
                    raise NotImplementedError("Subelement %s of email is not implemented."
                                                      % email_child.tag)
            ext_email["send-to"] = send_to
        elif email.tag == "failureCount":
            pass  # Handled in JJB.
        else:
            raise NotImplementedError("tag %s of trigger is not implemented." % email.tag)

    return ext_email


def __compare_triggers_and_process_email(trigger, ext_email, provider_dict):
    is_equal = True
    for email in trigger:
        if email.tag == "email":
            for email_child in email:
                if email_child.tag == "subject":
                    if email_child.text != "$PROJECT_DEFAULT_SUBJECT":
                        is_equal = False
                elif email_child.tag == "body":
                    if email_child.text != "$PROJECT_DEFAULT_CONTENT":
                        is_equal = False
                elif email_child.tag == "recipientProviders":
                    provider_count = 0
                    for provider in email_child:
                        if provider_dict[provider.tag] not in ext_email["send-to"]:
                            is_equal = False
                        else:
                            provider_count += 1
                    if provider_count != len(ext_email["send-to"]):
                        is_equal = False
    if not is_equal:
        raise NotImplementedError("Trigger values mismatch the global values.")

    __process_email(trigger, ext_email, provider_dict)


def extendedemailpublisher(top, parent):
    ext_email = {}
    for element in top:
        if element.tag == 'disabled':
            ext_email['disable-publisher'] = get_bool(element.text)
        elif element.tag == 'recipientList':
            ext_email['recipients'] = element.text
        elif element.tag == 'replyTo':
            ext_email['reply-to'] = element.text
        elif element.tag == 'from':
            ext_email['from'] = element.text or ''
        elif element.tag == 'contentType':
            if element.text == "both":
                ext_email['content-type'] = "both-html-text"
            elif element.text == "text/html":
                ext_email['content-type'] = "html"
            elif element.text == "text/plain":
                ext_email['content-type'] = "text"
            elif element.text == "default":
                ext_email['content-type'] = "default"
            else:
                raise NotImplementedError('Content type %s not implemented' % element.text)
        elif element.tag == 'compressBuildLog':
            ext_email['compress-log'] = get_bool(element.text)
        elif element.tag == 'defaultSubject':
            ext_email['subject'] = element.text
        elif element.tag == 'defaultContent':
            ext_email['body'] = element.text
        elif element.tag in ['attachBuildLog', 'compressBuildLog']:
            ext_email['attach-build-log'] = (element.text == 'true')
        elif element.tag == 'attachmentsPattern':
            ext_email['attachments'] = element.text or ''
        elif element.tag == 'saveOutput':
            ext_email['save-output'] = get_bool(element.text)
        elif element.tag == 'preBuild':
            ext_email['pre-build'] = (element.text == 'true')
        elif element.tag == 'presendScript':
            ext_email['presend-script'] = element.text
        elif element.tag == 'postsendScript':
            ext_email['postsend-script'] = element.text
        elif element.tag == 'sendTo':
            ext_email['send-to'] = element.text
        elif element.tag == 'configuredTriggers':
            trigger_prefix = "hudson.plugins.emailext.plugins.trigger."
            trigger_dict = {
                "AlwaysTrigger": "always",
                "UnstableTrigger": "unstable",
                "FirstFailureTrigger": "first-failure",
                "FirstUnstableTrigger": "first-unstable",
                "NotBuiltTrigger": "not-built",
                "AbortedTrigger": "aborted",
                "RegressionTrigger": "regression",
                "FailureTrigger": "failure",
                "SecondFailureTrigger": "second-failure",
                "ImprovementTrigger": "improvement",
                "StillFailingTrigger": "still-failing",
                "SuccessTrigger": "success",
                "FixedTrigger": "fixed",
                "FixedUnhealthyTrigger": "fixed-unhealthy",
                "StillUnstableTrigger": "still-unstable",
                "PreBuildTrigger": "pre-build"
            }
            provider_dict = {
                "hudson.plugins.emailext.plugins.recipients.UpstreamComitterRecipientProvider": "upstream-committers",
                "hudson.plugins.emailext.plugins.recipients.DevelopersRecipientProvider": "developers",
                "hudson.plugins.emailext.plugins.recipients.RequesterRecipientProvider": "requester",
                "hudson.plugins.emailext.plugins.recipients.CulpritsRecipientProvider": "culprits",
                "hudson.plugins.emailext.plugins.recipients.ListRecipientProvider": "recipients",
                "hudson.plugins.emailext.plugins.recipients.FailingTestSuspectsRecipientProvider":
                    "failing-test-suspects-recipients",
                "hudson.plugins.emailext.plugins.recipients.FirstFailingBuildSuspectsRecipientProvider":
                    "first-failing-build-suspects-recipients"
            }
            trigger_result = {}  # To be able to print all on the output yaml
            for key in trigger_dict.keys():
                trigger_result[key] = False
            # JJB implementation only uses the default content-type/subject/message
            # and uses those in the trigger elements. Does not take information
            # from trigger element's content. This means that JJW can do the conversion
            # only if triggers use the defaults for subject and body. However, `sendTo`
            # must be taken from one of the triggers, in this case, first trigger will
            # be used in order to retrieve sendTo information. This also means that,
            # `sendTo` must be same in all triggers. If there are different triggers,
            # NotImplementedError will be raised to make sure JJW does not cause
            # information loss.
            for trigger in element:
                if "send-to" not in ext_email:
                    ext_email = __process_email(trigger, ext_email, provider_dict)
                else:
                    __compare_triggers_and_process_email(trigger, ext_email, provider_dict)
                tag = trigger.tag.split(trigger_prefix)[1]
                if tag in trigger_dict.keys():
                    trigger_result[tag] = True
                else:
                    raise NotImplementedError("Email-ext trigger %s is not implemented." % trigger.tag)
            for key, value in trigger_result.items():
                ext_email[trigger_dict[key]] = value
        elif element.tag == 'matrixTriggerMode':
            matrix_dict = {
                "BOTH": "both",
                "ONLY_CONFIGURATIONS": "only-configurations",
                "ONLY_PARENT": "only-parent"
            }
            if element.text in matrix_dict.keys():
                ext_email['matrix-trigger'] = matrix_dict[element.text]
            else:
                raise NotImplementedError("Matrix trigger mode %s is not implemented." % element.text)
        else:
            raise NotImplementedError("cannot handle XML %s" % element.tag)

    parent.append({'email-ext': ext_email})


def junitresultarchiver(top, parent):
    junit_publisher = {}
    for element in top:
        if element.tag == 'testResults':
            junit_publisher['results'] = element.text
        elif element.tag == 'keepLongStdio':
            junit_publisher['keep-long-stdio'] = \
                (element.text == 'true')
        elif element.tag == 'healthScaleFactor':
            junit_publisher['health-scale-factor'] = element.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'junit': junit_publisher})


def buildtrigger(top, parent):
    build_trigger = {}

    for element in top:
        if element.tag == 'configs':
            build_triggers = []
            for sub in element:
                project = {
                    "current-parameters": False,
                    "node-parameters": False
                }
                for config in sub:
                    if config.tag == 'projects':
                        project['project'] = [x.strip() for x in config.text.split(',')]
                    elif (config.tag == 'condition' and
                          config.text in ['SUCCESS', 'UNSTABLE', 'FAILED_OR_BETTER',
                                          'UNSTABLE_OR_BETTER', 'UNSTABLE_OR_WORSE',
                                          'FAILED', 'ALWAYS']):
                        project['condition'] = config.text
                    elif config.tag == 'triggerFromChildProjects':
                        project['trigger-from-child-projects'] = get_bool(config.text)
                    elif config.tag == 'triggerWithNoParameters':
                        project['trigger-with-no-params'] = \
                            (config.text == 'true')
                    elif config.tag == 'configs':
                        for subconf in config:
                            if subconf.tag == 'hudson.plugins.parameterizedtrigger.PredefinedBuildParameters':
                                for bottom in subconf:
                                    if bottom.tag == 'properties':
                                        project['predefined-parameters'] = bottom.text
                                    else:
                                        raise NotImplementedError("cannot handle PredefinedBuildParameters "
                                                                  "sub-element %s " % bottom.tag)
                            elif subconf.tag == 'hudson.plugins.parameterizedtrigger.FileBuildParameters':
                                for parameter in subconf:
                                    if parameter.tag == "propertiesFile":
                                        project["property-file"] = parameter.text
                                    elif parameter.tag == "failTriggerOnMissing":
                                        project["fail-on-missing"] = get_bool(parameter.text)
                                    elif parameter.tag == "textParamValueOnNewLine":
                                        project["property-multiline"] = get_bool(parameter.text)
                                    elif parameter.tag == "useMatrixChild":
                                        project["use-matrix-child-files"] = get_bool(parameter.text)
                                    elif parameter.tag == "onlyExactRuns":
                                        project["only-exact-matrix-child-runs"] = get_bool(parameter.text)
                                    elif parameter.tag == "encoding":
                                        project["file-encoding"] = parameter.text
                                    else:
                                        raise NotImplementedError("cannot handle FileBuildParameters sub-element %s"
                                                                  % parameter.tag)
                            elif subconf.tag == 'hudson.plugins.git.GitRevisionBuildParameters':
                                git_revision = {}
                                for parameter in subconf:
                                    if parameter.tag == "combineQueuedCommits":
                                        git_revision["combine-queued-commits"] = get_bool(parameter.text)
                                    else:
                                        raise NotImplementedError("cannot handle GitRevisionBuildParameters "
                                                                  "sub-element %s " % parameter.tag)
                                project["git-revision"] = git_revision
                            elif subconf.tag == 'hudson.plugins.parameterizedtrigger.matrix.MatrixSubsetBuildParameters':
                                for parameter in subconf:
                                    if parameter.tag == "filter":
                                        project["restrict-matrix-project"] = parameter.text
                                    else:
                                        raise NotImplementedError("cannot handle MatrixSubsetBuildParameters "
                                                                  "sub-element %s " % parameter.tag)
                            elif subconf.tag == 'org.jvnet.jenkins.plugins.nodelabelparameter.parameterizedtrigger.NodeLabelBuildParameter':
                                for element in subconf:
                                    if element.tag == "name":
                                        project["node-label-name"] = element.text
                                    elif element.tag == "nodeLabel":
                                        project["node-label"] = element.text
                                    else:
                                        raise NotImplementedError("cannot handle NodeLabelBuildParameter "
                                                                  "sub-element %s " % element.tag)
                            elif subconf.tag == 'hudson.plugins.parameterizedtrigger.CurrentBuildParameters':
                                project["current-parameters"] = True
                            elif subconf.tag == 'hudson.plugins.parameterizedtrigger.NodeParameters':
                                project["node-parameters"] = True
                            elif subconf.tag == 'hudson.plugins.parameterizedtrigger.SubversionRevisionBuildParameters':
                                project["svn-revision"] = True
                                for element in subconf:
                                    if element.tag == 'includeUpstreamParameters':
                                        project["include-upstream"] = get_bool(element.text)
                                    else:
                                        raise NotImplementedError("cannot handle SubversionRevisionBuildParameters "
                                                                  "sub-element %s " % element.tag)
                            elif subconf.tag == 'hudson.plugins.parameterizedtrigger.BooleanParameters':
                                for config in subconf:
                                    if config.tag == "configs":
                                        boolean_config = {}
                                        for bool_param_config in config:
                                            if bool_param_config.tag == \
                                                    "hudson.plugins.parameterizedtrigger.BooleanParameterConfig":
                                                if len(bool_param_config) == 2 and bool_param_config[0].tag == "name" \
                                                        and bool_param_config[1].tag == "value":
                                                    boolean_config[bool_param_config[0].text] = \
                                                        get_bool(bool_param_config[1].text)
                                                else:
                                                    raise NotImplementedError("cannot handle BooleanParameters"
                                                                          "sub-element %s " % bool_param_config.tag)
                                            else:
                                                raise NotImplementedError("cannot handle BooleanParameters.configs"
                                                                          "sub-element %s " % bool_param_config.tag)
                                        project["boolean-parameters"] = boolean_config
                                    else:
                                        raise NotImplementedError("cannot handle BooleanParameters"
                                                                  "sub-element %s " % config.tag)
                            else:
                                raise NotImplementedError("cannot handle subconfig XML %s" % subconf.tag)
                    else:
                        raise NotImplementedError("cannot handle "
                                                  "XML %s" % config.tag)

                build_triggers.append(project)

            parent.append({'trigger-parameterized-builds': build_triggers})
            return
        elif element.tag == 'childProjects':
            build_trigger['project'] = element.text
        elif element.tag == 'threshold':
            for item in element:
                if item.tag == 'name' and item.text in ['SUCCESS', 'UNSTABLE', 'FAILURE']:
                    build_trigger['threshold'] = item.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % element.tag)
    parent.append({'trigger': build_trigger})
    return


def mailer(top, parent):
    email_settings = {}
    for element in top:
        if element.tag == 'recipients':
            email_settings['recipients'] = element.text
        elif element.tag == 'dontNotifyEveryUnstableBuild':
            email_settings['notify-every-unstable-build'] = \
                (element.text == 'false')
        elif element.tag == 'sendToIndividuals':
            email_settings['send-to-individuals'] = \
                (element.text == 'true')
        else:
            raise NotImplementedError("cannot handle "
                                      "email %s" % element.tag)
    parent.append({'email': email_settings})


def htmlpublisher(top, parent):
    html_publisher = {}
    element = top[0]
    if element.tag != 'reportTargets':
        raise NotImplementedError("Cannot handle XML %s" % element.tag)
    for subelement in element:
        if subelement.tag != 'htmlpublisher.HtmlPublisherTarget':
            raise NotImplementedError("Cannot handle XML %s" % element.tag)
        for config in subelement:
            if config.tag == 'reportName':
                html_publisher['name'] = config.text
            if config.tag == 'reportDir':
                html_publisher['dir'] = config.text
            if config.tag == 'reportFiles':
                html_publisher['files'] = config.text
            if config.tag == 'keepAll':
                html_publisher['keep-all'] = (config.text == 'true')
            if config.tag == 'allowMissing':
                html_publisher['allow-missing'] = (config.text == 'true')
            if config.tag == 'alwaysLinkToLastBuild':
                html_publisher['link-to-last-build'] = (config.text == 'true')
            if config.tag == 'wrapperName':
                # Apparently, older versions leakded this wrapper name
                # to the job configuration.
                pass

    if len(html_publisher) > 0:
        parent.append({'html-publisher': html_publisher})


def groovypostbuildrecorder(top, parent):
    groovy = {}
    for groovy_element in top:
        # Groovy Postbuild plugin v1.X tags below
        if groovy_element.tag == 'groovyScript':
            groovy['script'] = groovy_element.text
        elif groovy_element.tag == 'classpath':
            classpaths = []
            for child1 in groovy_element:
                for child2 in child1:
                    if child2.tag == 'path':
                        classpaths.append(child2.text)
            groovy['classpath'] = classpaths
        # Groovy Postbuild plugin v2.X tags below
        elif groovy_element.tag == 'script':
            for child in groovy_element:
                if child.tag == 'script':
                    groovy['script'] = child.text
                elif child.tag == 'sandbox':
                    groovy['sandbox'] = (child.text == 'true')
                else:
                    raise NotImplementedError("cannot handle groovy-postbuild script elements")
        elif groovy_element.tag == 'behavior':
            # https://github.com/jenkinsci/groovy-postbuild-plugin/blob/groovy-postbuild-2.5/src/main/java/org/jvnet/hudson/plugins/groovypostbuild/GroovyPostbuildRecorder.java#L395
            behavior = {
                '0': 'nothing',
                '1': 'unstable',
                '2': 'failed'
            }
            groovy['on-failure'] = behavior.get(groovy_element.text)
            if groovy['on-failure'] is None:
                raise NotImplementedError("cannot handle groovy-postbuild behavior value")
        elif groovy_element.tag == 'runForMatrixParent':
            groovy['matrix-parent'] = (groovy_element.text == 'true')
        else:
            raise NotImplementedError("cannot handle groovy-postbuild elements")
    parent.append({'groovy-postbuild': groovy})


def robotpublisher(top, parent):
    robot = {}
    mapper_robot_publisher = Mapper({
        "outputPath": ("output-path", str),
        "logFileLink": ("log-file-link", str),
        "reportFileName": ("report-html", str),
        "logFileName": ("log-html", str),
        "outputFileName": ("output-xml", str),
        "passThreshold": ("pass-threshold", float),
        "unstableThreshold": ("unstable-threshold", float),
        "onlyCritical": ("only-critical", bool),
        "enableCache": ("enable-cache", bool)
    })
    for child in top:
        if mapper_robot_publisher.map_element(child, robot):
            pass  # Handled by the mapper.
        elif child.tag == "disableArchiveOutput":
            robot["archive-output-xml"] = not get_bool(child.text)
        elif child.tag == "otherFiles":
            robot["other-files"] = [item.text for item in child if item.tag == "string"]
        else:
            raise NotImplementedError("Robot Publisher tag: %s not implemented." % child.tag)
    parent.append({'robot': robot})


def slacknotifier(top, parent):
    slacknotifier = {}
    notifications = {
        "startNotification": "notify-start",
        "notifySuccess": "notify-success",
        "notifyAborted": "notify-aborted",
        "notifyNotBuilt": "notify-not-built",
        "notifyUnstable": "notify-unstable",
        "notifyFailure": "notify-failure",
        "notifyBackToNormal": "notify-back-to-normal",
        "notifyRegression": "notify-regression",
        "notifyRepeatedFailure": "notify-repeated-failure"
    }
    for child in top:
        if child.tag == 'teamDomain':
            if child.text:
                slacknotifier['team-domain'] = child.text
        elif child.tag == 'authToken':
            if child.text:
                slacknotifier['auth-token'] = child.text
        elif child.tag == 'authTokenCredentialId':
            if child.text:
                slacknotifier['auth-token-credential-id'] = child.text
        elif child.tag == 'buildServerUrl':
            slacknotifier['build-server-url'] = child.text
        elif child.tag == 'room':
            slacknotifier['room'] = child.text
        elif child.tag in notifications:
            slacknotifier[notifications[child.tag]] = get_bool(child.text)
        elif child.tag == 'includeTestSummary':
            slacknotifier['include-test-summary'] = get_bool(child.text)
        elif child.tag == 'includeFailedTests':
            slacknotifier['include-failed-tests'] = get_bool(child.text)
        elif child.tag == 'commitInfoChoice':
            slacknotifier['commit-info-choice'] = child.text
        elif child.tag == 'includeCustomMessage':
            slacknotifier['include-custom-message'] = get_bool(child.text)
        elif child.tag == 'customMessage':
            if child.text:
                slacknotifier['custom-message'] = child.text
        elif child.tag == 'botUser':
            slacknotifier['bot-user'] = get_bool(child.text)
        elif child.tag == 'baseUrl':
            if child.text:
                slacknotifier['base-url'] = child.text
        else:
            raise NotImplementedError("cannot handle "
                                      "XML %s" % child.tag)
    parent.append({'slack': slacknotifier})


def postbuildtask(top, parent):
    post_tasks = []
    for pt in top[0]:
        post_task = {}
        for ptel in pt:
            if ptel.tag == 'logTexts':
                matches = []
                for logtext in ptel:
                    match = {}
                    for logtextel in logtext:
                        if logtextel.tag == 'logText':
                            match['log-text'] = logtextel.text
                        elif logtextel.tag == 'operator':
                            match['operator'] = logtextel.text
                    matches.append(match)
                post_task['matches'] = matches
            elif ptel.tag == 'EscalateStatus':
                post_task['escalate-status'] = get_bool(ptel.text)
            elif ptel.tag == 'RunIfJobSuccessful':
                post_task['run-if-job-successful'] = get_bool(ptel.text)
            elif ptel.tag == 'script':
                post_task['script'] = ptel.text
        post_tasks.append(post_task)
    parent.append({'post-tasks': post_tasks})


def wscleanup(top, parent):
    cleanup = {'include': [], 'exclude': [], 'clean-if': []}
    for cleanupel in top:
        if cleanupel.tag == 'patterns':
            for pattern in cleanupel:
                pattern_glob = None
                pattern_type = None
                for patternel in pattern:
                    if patternel.tag == 'pattern':
                        pattern_glob = patternel.text
                    elif patternel.tag == 'type':
                        pattern_type = patternel.text
                cleanup[pattern_type.lower()].append(pattern_glob)
        elif cleanupel.tag == 'deleteDirs':
            cleanup['dirmatch'] = get_bool(cleanupel.text)
        elif cleanupel.tag == 'cleanWhenSuccess':
            cleanup['clean-if'].append({'success': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenUnstable':
            cleanup['clean-if'].append({'unstable': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenFailure':
            cleanup['clean-if'].append({'failure': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenNotBuilt':
            cleanup['clean-if'].append({'not-built': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'cleanWhenAborted':
            cleanup['clean-if'].append({'aborted': get_bool(cleanupel.text)})
        elif cleanupel.tag == 'notFailBuild':
            cleanup['fail-build'] = not get_bool(cleanupel.text)
        elif cleanupel.tag == 'cleanupMatrixParent':
            cleanup['clean-parent'] = get_bool(cleanupel.text)
        elif cleanupel.tag == 'disableDeferredWipeout':
            cleanup['disable-deferred-wipeout'] = get_bool(cleanupel.text)
        elif cleanupel.tag == 'externalDelete':
            cleanup['external-deletion-command'] = cleanupel.text or ''
    parent.append({'workspace-cleanup': cleanup})
