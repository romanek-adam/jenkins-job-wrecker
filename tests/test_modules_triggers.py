# -*- coding: utf-8 -*-
from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml
from jenkins_job_wrecker.modules.triggers import gerrittrigger
import os, yaml

from tests.helpers import compare_jjb_output

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'triggers')


class TestGerritTrigger(object):
    def test_gerrit_trigger_comparison(self):
        compare_jjb_output(fixtures_path, "gerrit_trigger", "gerrit-trigger")


class TestGithubPullRequest(object):
    def test_github_pull_request_builder(self):
        compare_jjb_output(fixtures_path, "github-pull-request-full", "github-pull-request-full")
