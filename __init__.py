from mycroft.configuration.config import Configuration
from mycroft.skills.core import MainModule
from mycroft.util.parse import match_one
from os.path import exists, expanduser, join, dirname, isdir
from os import makedirs, listdir, remove
import requests
import subprocess

__author__ = "JarbasAI"


class MycroftSkillManager(object):
    DEFAULT_SKILLS = {}
    SKILLS_MODULES = "https://raw.githubusercontent.com/MycroftAI/mycroft-skills/master/.gitmodules"
    SKILLS_DEFAULTS_URL = "https://raw.githubusercontent.com/MycroftAI/mycroft-skills/master/DEFAULT-SKILLS"

    def __init__(self, emitter, skills_config=None, defaults_url=None, modules_url=None):
        self.skills_config = skills_config or Configuration.get().get("skills", {})
        self.skills_dir = self.skills_config.get("directory") or '/opt/mycroft/skills'
        self.modules_url = modules_url or self.SKILLS_MODULES
        self.defaults_url = defaults_url or self.SKILLS_DEFAULTS_URL
        self.emitter = emitter
        self.skills = {}
        self.default_skills = {}
        self.platform = Configuration.get().get("enclosure", {}).get("platform", "desktop")
        self.prepare_msm()

    def git_from_folder(self, path):
        try:
            website = subprocess.check_output(["git", "remote", "-v"], cwd=path)
            website = website.replace("origin\t", "").replace(" (fetch)", "").split("\n")[0]
        except:
            website = None
        return website

    def _is_skill(self, skill_folder):
        """
            Check if folder is a skill and perform mapping.
        """
        path = join(self.skills_dir, skill_folder)
        # check if folder is a skill (must have __init__.py)
        if not MainModule + ".py" in listdir(path):
            return False

        if skill_folder not in self.skills:
            self.skills[skill_folder] = {"id": hash(path)}
        git_url = self.git_from_folder(path)
        if git_url:
            author = git_url.split("/")[-2]
        else:
            author = "unknown"
        self.skills[skill_folder]["path"] = path
        self.skills[skill_folder]["folder"] = skill_folder
        if "name" not in self.skills[skill_folder].keys():
            self.skills[skill_folder]["name"] = skill_folder
        self.skills[skill_folder]["repo"] = git_url
        self.skills[skill_folder]["author"] = author
        self.skills[skill_folder]["installed"] = True
        return True

    def get_default_skills_list(self):
        """ get default skills list from url """
        defaults = {}
        try:
            # get core and common skillw
            text = requests.get(self.defaults_url).text
            core = text.split("# core")[1]
            core, common = core.split("# common")
            core = [c for c in core.split("\n") if c]
            common = [c for c in common.split("\n") if c]
        except:
            core = common = []
        defaults["core"] = core
        defaults["common"] = common
        # get picroft
        try:
            text = requests.get(self.defaults_url + ".picroft").text
            picroft = text.split("# picroft")[1]
            picroft = [c for c in picroft.split("\n") if c]
        except:
            picroft = []
        defaults["picroft"] = picroft
        # get kde
        try:
            text = requests.get(self.defaults_url+".kde").text
            kde = text.split("# desktop")[1]
            kde = [c for c in kde.split("\n") if c]
        except:
            kde = []
        defaults["desktop"] = kde
        # get mark 1
        try:
            text = requests.get(self.defaults_url+".mycroft_mark_1").text
            mk1 = text.split("# mark 1")[1]
            mk1 = [c for c in mk1.split("\n") if c]
        except:
            mk1 = []
        defaults["mycroft_mark_1"] = mk1
        # on error use hard coded defaults
        self.default_skills = defaults or self.DEFAULT_SKILLS
        return self.default_skills

    def prepare_msm(self):
        """ prepare msm execution """
        # find home dir
        if "~" in self.skills_dir:
            self.skills_dir = expanduser(self.skills_dir)

        # create skills dir if missing
        if not exists(self.skills_dir):
            makedirs(self.skills_dir)

        # update default skills list
        self.get_default_skills_list()

        # scan skills folder
        self.scan_skills_folder()

        # scan skills repo
        self.scan_skills_repo()

        # TODO permissions stuff

    def scan_skills_folder(self):
        """ scan installed skills """
        if exists(self.skills_dir):
            # checking skills dir and getting all skills there
            skill_list = [folder for folder in filter(
                lambda x: isdir(join(self.skills_dir, x)),
                listdir(self.skills_dir))]
            for skill_folder in skill_list:
                self._is_skill(skill_folder)
        return self.skills.keys()

    def scan_skills_repo(self):
        """ get skills list from skills repo """
        text = requests.get(self.modules_url).text
        modules = text.split('[submodule "')
        for module in modules:
            if not module:
                continue
            name = module.split('"]')[0].strip()
            url = module.split('url = ')[1].strip()
            skill_folder = url.split("/")[-1]
            skill_path = join(self.skills_dir, skill_folder)
            skill_id = hash(skill_path)
            skill_author = url.split("/")[-2]
            installed = False
            if skill_folder in self.skills:
                installed = True
            self.skills[skill_folder] = {"repo": url, "folder": skill_folder, "path": skill_path, "id": skill_id, "author": skill_author, "name": name, "installed": installed}

    def install_defaults(self):
        """ installs the default skills, updates all others """
        for skill in self.default_skills["core"]:
            self.install_from_name(skill)
        for skill in self.default_skills["common"]:
            self.install_from_name(skill)
        for skill in self.default_skills.get(self.platform, []):
            self.install_from_name(skill)
        self.update_skills()

    def install_from_name(self, name):
        """ installs the mycroft-skill matching <name> """
        folders = self.skills.keys()
        names = [self.skills[skill]["name"] for skill in folders]
        f_skill, f_score = match_one(name, folders)
        n_skill, n_score = match_one(name, names)
        if n_score > 0.5:
            for s in self.skills:
                if self.skills[s]["name"] == n_skill:
                    skill = self.skills[s]
                    if not self.skills[s]["installed"]:
                        return self.install_from_url[skill["repo"]]
        elif f_score > 0.5:
            skill = self.skills[f_skill]
            if not self.skills[s]["installed"]:
                return self.install_from_url[skill["repo"]]
        return False

    def remove_from_url(self, url):
        """ removes the specified github repo """
        for skill in self.skills:
            if url == self.skills[skill]["repo"]:
                if self.skills[skill]["installed"]:
                    remove(self.skills[skill]["path"])
                    return True
                break
        return False

    def remove_from_name(self, folder_name):
        """ removes the specified skill folder name """
        folders = self.skills.keys()
        names = [self.skills[skill]["name"] for skill in folders]
        f_skill, f_score = match_one(name, folders)
        n_skill, n_score = match_one(name, names)
        installed = False
        if n_score > 0.5:
            for s in self.skills:
                if self.skills[s]["name"] == n_skill:
                    skill = self.skills[s]
                    installed = skill["installed"]
                    self.skills[s]["installed"] = False
                    break
        elif f_score > 0.5:
            skill = self.skills[f_skill]
            installed = skill["installed"]
            self.skills[f_skill]["installed"] = False
        if not installed:
            return False
        remove(skill["path"])
        return True

    def list_skills(self):
        """ list all mycroft-skills in the skills repo and installed """
        return self.skills

    def update_skills(self):
        """ update all installed skills """
        for skill in self.skills:
            if self.skills[skill]["installed"]:
                self.install_from_url(self.skills[skill]["repo"])

    def url_info(self, url):
        """ shows information about the skill in the specified repo """
        for skill in self.skills:
            if url == self.skills[skill]["repo"]:
                return self.skills[skill]
        return {}

    def name_info(self, name):
        """ shows information about the skill matching <name> """
        folders = self.skills.keys()
        names = [self.skills[skill]["name"] for skill in folders]
        f_skill, f_score = match_one(name, folders)
        n_skill, n_score = match_one(name, names)
        installed = False
        if n_score > 0.5:
            for s in self.skills:
                if self.skills[s]["name"] == n_skill:
                    return self.skills[s]
        elif f_score > 0.5:
            return self.skills[f_skill]
        return {}

    # TODOS
    def install_from_url(self, url):
        """ installs from the specified github repo """
        return False

    def run_pip(self, skill_folder):
        return False

    def run_requirements_sh(self, skill_folder):
        return False
