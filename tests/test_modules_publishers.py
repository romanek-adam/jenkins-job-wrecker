# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root
from jenkins_job_wrecker.modules.publishers import groovypostbuildrecorder
from jenkins_job_wrecker.modules.publishers import extendedemailpublisher
import os
import unittest
from .helpers import compare_jjb_output

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'publishers')


class TestGroovyPostbuildPlugin(object):
    def test_v2(self):
        filename = os.path.join(fixtures_path, 'groovy-postbuild-v2.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        parent = []
        groovypostbuildrecorder(root, parent)
        assert len(parent) == 1
        assert 'groovy-postbuild' in parent[0]
        jjb_groovy_postbuild = parent[0]['groovy-postbuild']
        assert jjb_groovy_postbuild['matrix-parent'] is False
        assert jjb_groovy_postbuild['on-failure'] == 'nothing'
        assert jjb_groovy_postbuild['sandbox'] is False
        assert jjb_groovy_postbuild['script'] == 'foo bar'


class TestWorkspaceCleanupPublisherPlugin(object):
    def test_cleanup_workspace(self):
        compare_jjb_output(fixtures_path, "workspace-cleanup", "workspace-cleanup")


class TestRobotPublisherPlugin(object):
    def test_robot_publisher(self):
        compare_jjb_output(fixtures_path, "robot", "robot")


class TestTriggerParameterizedBuilds(object):
    def test_comparison(self):
        compare_jjb_output(fixtures_path, "trigger-parameterized-builds", "trigger-parameterized-builds")


class TestExtendedEmailPublisher(unittest.TestCase):
    def test_email_ext_with_multiple_triggers(self):
        compare_jjb_output(fixtures_path, "email-ext-with-multiple-triggers", "email-ext")

    def test_email_ext_with_single_trigger(self):
        compare_jjb_output(fixtures_path, "email-ext-with-single-trigger", "email-ext")

    def test_email_ext_with_multiple_different_triggers_001(self):
        filename = os.path.join(fixtures_path, 'email-ext-with-multiple-different-triggers001.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        with self.assertRaises(NotImplementedError):
            extendedemailpublisher(root, None)

    def test_email_ext_with_multiple_different_triggers_002(self):
        filename = os.path.join(fixtures_path, 'email-ext-with-multiple-different-triggers002.xml')
        root = get_xml_root(filename=filename)
        assert root is not None
        with self.assertRaises(NotImplementedError):
            extendedemailpublisher(root, None)

