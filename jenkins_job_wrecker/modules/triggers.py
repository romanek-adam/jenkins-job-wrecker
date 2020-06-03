# encoding=utf8
from builtins import NotImplementedError

import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.helpers import get_bool


class Triggers(jenkins_job_wrecker.modules.base.Base):
    component = 'triggers'

    def gen_yml(self, yml_parent, data):
        triggers = []
        for child in data:
            object_name = child.tag.split('.')[-1].lower()
            self.registry.dispatch(self.component, object_name, child, triggers)
        yml_parent.append(['triggers', triggers])


def scmtrigger(top, parent):
    pollscm = {}
    for child in top:
        if child.tag == 'spec':
            pollscm['cron'] = child.text
        elif child.tag == 'ignorePostCommitHooks':
            pollscm['ignore-post-commit-hooks'] = (child.text == 'true')
        else:
            raise NotImplementedError('cannot handle scm trigger '
                                      'setting %s' % child.tag)

    parent.append({'pollscm': pollscm})


def timertrigger(top, parent):
    parent.append({'timed': top[0].text})


def reversebuildtrigger(top, parent):
    reverse = {}
    for child in top:
        if child.tag == 'upstreamProjects':
            reverse['jobs'] = child.text
        elif child.tag == 'threshold':
            pass  # TODO
        elif child.tag == 'spec':
            pass  # TODO
        else:
            raise NotImplementedError('cannot handle reverse trigger '
                                      'setting %s' % child.tag)

    parent.append({'reverse': reverse})


def process_file_paths(attribute):
    file_paths = []
    for file_path_type in attribute:
        if file_path_type.tag == "com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.data.FilePath":
            file_path = {}
            for file_path_attribute in file_path_type:
                if file_path_attribute.tag == "compareType":
                    file_path["compare-type"] = file_path_attribute.text
                elif file_path_attribute.tag == "pattern":
                    file_path["pattern"] = file_path_attribute.text
            file_paths.append(file_path)
        else:
            raise NotImplementedError("Not implemented file path type: ", file_path_type.tag)
    return file_paths


def gerrittrigger(top, parent):
    gerrit_trigger = {}
    for child in top:
        print(child.tag)
        if child.tag == "gerritProjects":
            projects = []
            for gerrit_project in child:
                project = {}
                for attribute in gerrit_project:
                    if attribute.tag == "compareType":
                        project["project-compare-type"] = attribute.text
                    elif attribute.tag == "pattern":
                        project["project-pattern"] = attribute.text
                    elif attribute.tag == "branches":
                        branches = []
                        for branch_type in attribute:
                            if branch_type.tag == "com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.data.Branch":
                                branch = {}
                                for branch_attribute in attribute[0]:
                                    if branch_attribute.tag == "compareType":
                                        branch["branch-compare-type"] = branch_attribute.text
                                    elif branch_attribute.tag == "pattern":
                                        branch["branch-pattern"] = branch_attribute.text
                                    else:
                                        raise NotImplementedError("Not implemented branch attribute: ",
                                                                  branch_attribute.tag)
                                branches.append(branch)
                            else:
                                raise NotImplementedError("Not implemented branch type: ", branch_type.tag)
                        project["branches"] = branches

                    elif attribute.tag == "disableStrictForbiddenFileVerification":
                        project["disable-strict-forbidden-file-verification"] = get_bool(attribute.text)
                    elif attribute.tag == "filePaths":
                        file_paths = process_file_paths(attribute)
                        project["file-paths"] = file_paths
                    elif attribute.tag == "forbiddenFilePaths":
                        forbidden_file_paths = process_file_paths(attribute)
                        project["forbidden-file-paths"] = forbidden_file_paths
                    elif attribute.tag == "topics":
                        topics = process_file_paths(attribute)
                        project["topics"] = topics
                    else:
                        raise NotImplementedError("Not implemented attribute: ", attribute.tag)

                projects.append(project)
            gerrit_trigger["projects"] = projects
        elif child.tag == "dynamicGerritProjects":
            pass
        elif child.tag == "spec":
            pass
        elif child.tag == "skipVote":
            skip_vote = {}
            for attribute in child:
                if attribute.text == "onSuccessful":
                    skip_vote["successful"] = get_bool(attribute.text)
                if attribute.text == "onFailed":
                    skip_vote["failed"] = get_bool(attribute.text)
                if attribute.text == "onUnstable":
                    skip_vote["unstable"] = get_bool(attribute.text)
                if attribute.text == "onNotBuilt":
                    skip_vote["notbuilt"] = get_bool(attribute.text)
            gerrit_trigger["skip_vote"] = skip_vote
        elif child.tag == "gerritBuildStartedVerifiedValue":
            gerrit_trigger["gerrit-build-started-verified-value"] = int(child.text)
        elif child.tag == "gerritBuildStartedCodeReviewValue":
            gerrit_trigger["gerrit-build-started-codereview-value"] = int(child.text)
        elif child.tag == "gerritBuildSuccessfulVerifiedValue":
            gerrit_trigger["gerrit-build-successful-verified-value"] = int(child.text)
        elif child.tag == "gerritBuildSuccessfulCodeReviewValue":
            gerrit_trigger["gerrit-build-successful-codereview-value"] = int(child.text)
        elif child.tag == "gerritBuildFailedVerifiedValue":
            gerrit_trigger["gerrit-build-failed-verified-value"] = int(child.text)
        elif child.tag == "gerritBuildFailedCodeReviewValue":
            gerrit_trigger["gerrit-build-failed-codereview-value"] = int(child.text)
        elif child.tag == "gerritBuildUnstableVerifiedValue":
            gerrit_trigger["gerrit-build-unstable-verified-value"] = int(child.text)
        elif child.tag == "gerritBuildUnstableCodeReviewValue":
            gerrit_trigger["gerrit-build-unstable-codereview-value"] = int(child.text)
        elif child.tag == "gerritBuildNotBuiltVerifiedValue":
            gerrit_trigger["gerrit-build-notbuilt-verified-value"] = int(child.text)
        elif child.tag == "gerritBuildNotBuiltCodeReviewValue":
            gerrit_trigger["gerrit-build-notbuilt-codereview-value"] = int(child.text)
        elif child.tag == "silentMode":
            gerrit_trigger["silent"] = get_bool(child.text)
        elif child.tag == "notificationLevel":
            if child.text is None:
                gerrit_trigger["notification-level"] = "NONE"
            else:
                gerrit_trigger["notification-level"] = child.text
        elif child.tag == "silentStartMode":
            gerrit_trigger["silent-start"] = get_bool(child.text)
        elif child.tag == "escapeQuotes":
            gerrit_trigger["escape-quotes"] = get_bool(child.text)
        elif child.tag == "dependencyJobsNames":
            gerrit_trigger["dependency-jobs"] = child.text
        elif child.tag == "nameAndEmailParameterMode":
            gerrit_trigger["name-and-email-parameter-mode"] = child.text
        elif child.tag == "commitMessageParameterMode":
            gerrit_trigger["commit-message-parameter-mode"] = child.text
        elif child.tag == "changeSubjectParameterMode":
            gerrit_trigger["change-subject-parameter-mode"] = child.text
        elif child.tag == "commentTextParameterMode":
            gerrit_trigger["comment-text-parameter-mode"] = child.text
        elif child.tag == "buildStartMessage":
            gerrit_trigger["start-message"] = child.text
        elif child.tag == "buildFailureMessage":
            gerrit_trigger["failure-message"] = child.text
        elif child.tag == "buildSuccessfulMessage":
            gerrit_trigger["successful-message"] = child.text
        elif child.tag == "buildUnstableMessage":
            gerrit_trigger["unstable-message"] = child.text
        elif child.tag == "buildNotBuiltMessage":
            gerrit_trigger["notbuilt-message"] = child.text
        elif child.tag == "buildUnsuccessfulFilepath":
            gerrit_trigger["failure-message-file"] = child.text
        elif child.tag == "customUrl":
            gerrit_trigger["custom-url"] = child.text
        elif child.tag == "serverName":
            gerrit_trigger["server-name"] = child.text
        elif child.tag == "triggerOnEvents":
            trigger_on = []
            sonyericsson_prefix = "com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.events."
            for event in child:
                if event.tag == sonyericsson_prefix + "PluginChangeAbandonedEvent":
                    trigger_on.append("change-abandoned-event")
                elif event.tag == sonyericsson_prefix + "PluginChangeMergedEvent":
                    trigger_on.append("change-merged-event")
                elif event.tag == sonyericsson_prefix + "PluginChangeRestoredEvent":
                    trigger_on.append("change-restored-event")
                elif event.tag == sonyericsson_prefix + "PluginCommentAddedEvent":
                    comment_added_event = {}
                    for element in event:
                        if element.tag == "verdictCategory":
                            if element.text == "Code-Review":
                                comment_added_event["approval-category"] = "CRVW"
                            elif element.text == "Verified":
                                comment_added_event["approval-category"] = "VRIF"
                        elif element.tag == "commentAddedTriggerApprovalValue":
                            comment_added_event["approval-value"] = element.text
                    trigger_on.append({"comment-added-event": comment_added_event})
                elif event.tag == sonyericsson_prefix + "PluginCommentAddedContainsEvent":
                    trigger_on.append({"comment-added-contains-event": {"comment-contains-value": event[0].text}})
                elif event.tag == sonyericsson_prefix + "PluginDraftPublishedEvent":
                    trigger_on.append("draft-published-event")
                elif event.tag == sonyericsson_prefix + "PluginPatchsetCreatedEvent":
                    patchset_created_event = {}
                    for attribute in event:
                        if attribute.tag == "excludeDrafts":
                            patchset_created_event["exclude-draft"] = get_bool(attribute.text)
                        elif attribute.tag == "excludeTrivialRebase":
                            patchset_created_event["exclude-trivial-rebase"] = get_bool(attribute.text)
                        elif attribute.tag == "excludeNoCodeChange":
                            patchset_created_event["exclude-no-code-change"] = get_bool(attribute.text)
                        elif attribute.tag == "excludePrivateState":
                            patchset_created_event["exclude-private"] = get_bool(attribute.text)
                        elif attribute.tag == "excludeWipState":
                            patchset_created_event["exclude-wip"] = get_bool(attribute.text)
                    trigger_on.append({"patchset-created-event": patchset_created_event})
                elif event.tag == sonyericsson_prefix + "PluginPrivateStateChangedEvent":
                    trigger_on.append("private-state-changed-event")
                elif event.tag == sonyericsson_prefix + "PluginRefUpdatedEvent":
                    trigger_on.append("ref-updated-event")
                elif event.tag == sonyericsson_prefix + "PluginTopicChangedEvent":
                    trigger_on.append("topic-changed-event")
                elif event.tag == sonyericsson_prefix + "PluginWipStateChangedEvent":
                    trigger_on.append("wip-state-changed-event")
            gerrit_trigger["trigger-on"] = trigger_on
        elif child.tag == "dynamicTriggerConfiguration":
            gerrit_trigger["dynamic-trigger-enabled"] = get_bool(child.text)
        elif child.tag == "triggerConfigURL":
            gerrit_trigger["dynamic-trigger-url"] = child.text
        elif child.tag == "gerritTriggerTimerTask":
            pass
        elif child.tag == "triggerInformationAction":
            pass
        else:
            raise NotImplementedError("Not implemented Gerrit Trigger Plugin's attribute: ", child.tag)
    parent.append({'gerrit': gerrit_trigger})


def githubpushtrigger(top, parent):
    parent.append('github')


def ghprbtrigger(top, parent):
    ghpr = {}
    for child in top:
        if child.tag == 'spec' or child.tag == 'cron':
            ghpr['cron'] = child.text
        elif child.tag == 'adminlist' and child.text:
            ghpr['admin-list'] = child.text.strip().split('\n')
        elif child.tag == 'allowMembersOfWhitelistedOrgsAsAdmin':
            ghpr['allow-whitelist-orgs-as-admins'] = get_bool(child.text)
        elif child.tag == 'whitelist' and child.text is not None:
            ghpr['white-list'] = child.text.strip().split('\n')
        elif child.tag == 'orgslist' and child.text is not None:
            ghpr['org-list'] = child.text.strip().split('\n')
        elif child.tag == 'buildDescTemplate':
            ghpr['build-desc-template'] = child.text
        elif child.tag == 'triggerPhrase':
            ghpr['trigger-phrase'] = child.text
        elif child.tag == 'onlyTriggerPhrase':
            ghpr['only-trigger-phrase'] = get_bool(child.text)
        elif child.tag == 'useGitHubHooks':
            ghpr['github-hooks'] = get_bool(child.text)
        elif child.tag == 'permitAll':
            ghpr['permit-all'] = get_bool(child.text)
        elif child.tag == 'autoCloseFailedPullRequests':
            ghpr['auto-close-on-fail'] = get_bool(child.text)
        elif child.tag == 'whiteListTargetBranches':
            ghpr['white-list-target-branches'] = []
            for branch in child:
                if branch[0].text is not None:
                    ghpr['white-list-target-branches'].append(branch[0].text.strip())
        elif child.tag == 'gitHubAuthId':
            ghpr['auth-id'] = child.text

    parent.append({'github-pull-request': ghpr})
