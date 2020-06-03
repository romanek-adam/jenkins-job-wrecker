from __future__ import print_function

import jenkins_job_wrecker.modules.base
from jenkins_job_wrecker.registry import Registry
from jenkins_job_wrecker.helpers import get_bool


class Handlers(jenkins_job_wrecker.modules.base.Base):
    component = 'handlers'

    def gen_yml(self, yml_parent, data):
        for child in data:
            handler_name = child.tag.lower()
            settings = []
            try:
                self.registry.dispatch(self.component, handler_name, child, settings)
                if not settings:
                    continue
                for setting in settings:
                    key, value = setting
                    if key in yml_parent:
                        if not value:
                            continue
                        if type(yml_parent[key]) is dict:
                            yml_parent[key].update(value)
                        elif type(yml_parent[key]) is list:
                            yml_parent[key].append(value[0])
                    else:
                        yml_parent[key] = value
            except Exception:
                print('last called %s' % handler_name)
                raise


# Handle "<actions/>"
def actions(top, parent):
    # Nothing to do if it's empty.
    # Otherwise...
    if list(top) and len(list(top)) > 0:
        raise NotImplementedError("Don't know how to handle a "
                                  "non-empty <actions> element.")


# Handle "<authToken>tokenvalue</authToken>"
def authtoken(top, parent):
    parent.append(['auth-token', top.text])


# Handle "<description>my cool job</description>"
def description(top, parent):
    if top.text:
        parent.append(['description', top.text])


# Handle "<keepDependencies>false</keepDependencies>"
def keepdependencies(top, parent):
    # JJB cannot handle any other value than false, here.
    # There is no corresponding YAML option.
    pass


# Handle "<canRoam>true</canRoam>"
def canroam(top, parent):
    # JJB doesn't have an explicit YAML setting for this; instead, it
    # infers it from the "node" parameter. So there's no need to handle the
    # XML here.
    pass


# Handle "<disabled>false</disabled>"
def disabled(top, parent):
    parent.append(['disabled', get_bool(top.text)])


# Handle "<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>" NOQA
def blockbuildwhendownstreambuilding(top, parent):
    parent.append(['block-downstream', get_bool(top.text)])


# Handle "<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>" NOQA
def blockbuildwhenupstreambuilding(top, parent):
    parent.append(['block-upstream', get_bool(top.text)])


def concurrentbuild(top, parent):
    parent.append(['concurrent', get_bool(top.text)])


def axes(top, parent):
    axes = []
    mapper = {
        'hudson.matrix.LabelExpAxis': 'label-expression',
        'hudson.matrix.LabelAxis': 'slave',
        'hudson.matrix.TextAxis': 'user-defined',
        'jenkins.plugins.shiningpanda.matrix.PythonAxis': 'python',
    }
    for child in top:
        try:
            axis = {'type': mapper[child.tag]}
        except KeyError:
            raise NotImplementedError("cannot handle XML %s" % child.tag)
        for axis_element in child:
            if axis_element.tag == 'name':
                axis['name'] = axis_element.text
            if axis_element.tag == 'values':
                values = []
                for value_element in axis_element:
                    values.append(value_element.text)
                axis['values'] = values
        axes.append({'axis': axis})

    parent.append(['axes', axes])


def executionstrategy(top, parent):
    strategy = {}
    for child in top:

        if child.tag == 'runSequentially':
            strategy['sequential'] = get_bool(top.text)
        elif child.tag == 'sorter':
            # Is there anything but NOOP?
            pass
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append(['execution-strategy', strategy])


# Handle "<logrotator>...</logrotator>"'
def logrotator(top, parent):
    logrotate = {}
    for child in top:

        if child.tag == 'daysToKeep':
            logrotate['daysToKeep'] = child.text
        elif child.tag == 'numToKeep':
            logrotate['numToKeep'] = child.text
        elif child.tag == 'artifactDaysToKeep':
            logrotate['artifactDaysToKeep'] = child.text
        elif child.tag == 'artifactNumToKeep':
            logrotate['artifactNumToKeep'] = child.text
        elif child.tag == 'discardOnlyOnSuccess':
            logrotate['discardOnlyOnSuccess'] = child.text
        else:
            raise NotImplementedError("cannot handle XML %s" % child.tag)

    parent.append(['logrotate', logrotate])


# Handle "<combinationFilter>a != &quot;b&quot;</combinationFilter>"
def combinationfilter(top, parent):
    strategy = {}
    strategy['combination-filter'] = top.text
    parent.append(['execution-strategy', strategy])


# Handle "<assignedNode>server.example.com</assignedNode>"
def assignednode(top, parent):
    parent.append(['node', top.text])


# Handle "<displayName>my cool job</displayName>"
def displayname(top, parent):
    parent.append(['display-name', top.text])


# Handle "<quietPeriod>5</quietPeriod>"
def quietperiod(top, parent):
    parent.append(['quiet-period', top.text])


# Handle "<scmCheckoutRetryCount>8</scmCheckoutRetryCount>"
def scmcheckoutretrycount(top, parent):
    parent.append(['retry-count', top.text])


def customworkspace(top, parent):
    parent.append(['workspace', top.text])

def childcustomworkspace(top, parent):
    parent.append(['child-workspace', top.text])


def jdk(top, parent):
    parent.append(['jdk', top.text])


def definition(top, parent):
    reg = Registry()
    handlers = Handlers(reg)
    # Create register
    reg = Registry()

    # sub-level "definition" data
    definition = {}
    if 'class' in top.attrib:  # Pipeline script
        if top.attrib['class'] == 'org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition':
            #  Using pipeline-scm (getting jenkinsfile from repo)
            parent.append(['pipeline-scm', definition])
        elif top.attrib['class'] == 'org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition':
            # Using DSL (passing raw pipeline script)
            for child in top.getchildren():
                if child.tag == 'script':
                    parent.append(['dsl', child.text])
                elif child.tag == 'sandbox':
                    parent.append(['sandbox', get_bool(child.text)])
            # Don't pass anything to handlers.gen_yml, handled it here
            top = ''
    else:
        parent.append(['definition', definition])
    reg = Registry()
    handlers = Handlers(reg)
    handlers.gen_yml(definition, top)
