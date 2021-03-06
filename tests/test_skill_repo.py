# Copyright (c) 2018 Mycroft AI, Inc.
#
# This file is part of Mycroft Skills Manager
# (see https://github.com/MatthewScholefield/mycroft-light).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from os import chdir
from os.path import abspath, dirname, join
from shutil import rmtree

from msm import SkillRepo


class TestSkillRepo(object):
    def setup(self):
        root = dirname(abspath(__file__))
        chdir(root)
        self.repo = SkillRepo(
            join(root, 'repo-instance'),
            'https://github.com/mycroftai/mycroft-skills-manager', 'test-repo'
        )
        self.repo.update()

    def test_read_file(self):
        assert self.repo.read_file('test_file.txt') == 'test'

    def test_get_skill_data(self):
        """ generates tuples of name, path, url """
        assert set(self.repo.get_skill_data()) == {
            (
                'skill-a', 'skill-a',
                'https://github.com/MycroftAI/skill-hello-world',
                'a45e9b476884cfa463a50158d1131e02da072634'
            ),
            (
                'skill-b', 'skill-b',
                'https://github.com/MycroftAI/skill-ip.git',
                '880c2f90310844f62728e762f0a2fad328c0a008'
            ),
            (
                'skill-ce', 'skill-ce',
                'https://github.com/MycroftAI/skill-alarm.git',
                '16e717dfacef8c10390c6f4184d4c07877950894'
            ),
            (
                'skill-cd', 'skill-cd',
                'https://github.com/MycroftAI/skill-joke.git',
                '4ac8c0da55c2f38f9bcf04c2b369602851ccd38f'
            )
        }

    def test_get_shas(self):
        assert set(self.repo.get_shas()) == {
            ('skill-a', 'a45e9b476884cfa463a50158d1131e02da072634'),
            ('skill-b', '880c2f90310844f62728e762f0a2fad328c0a008'),
            ('skill-ce', '16e717dfacef8c10390c6f4184d4c07877950894'),
            ('skill-cd', '4ac8c0da55c2f38f9bcf04c2b369602851ccd38f')
        }

    def test_get_default_skill_names(self):
        assert dict(self.repo.get_default_skill_names()) == {
            'default': ['skill-a'],
            'platform-1': ['skill-b']
        }

    def teardown(self):
        rmtree('repo-instance')
