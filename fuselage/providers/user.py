# Copyright 2011-2014 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fuselage import error, resources, provider, platform
from fuselage.changes import ShellCommand


class User(provider.Provider):

    policies = (resources.user.UserApplyPolicy,)

    def get_user_info(self):
        fields = ("name", "passwd", "uid", "gid", "gecos", "dir", "shell")

        username = self.resource.name

        try:
            info_tuple = platform.getpwnam(username)
        except KeyError:
            info = dict((f, None) for f in fields)
            info["exists"] = False
            info['disabled-login'] = False
            info['disabled-password'] = False
            return info

        info = {"exists": True,
                "disabled-login": False,
                "disabled-password": False,
                }
        for i, field in enumerate(fields):
            info[field] = info_tuple[i]

        try:
            shadow = platform.getspnam(username)
            info['passwd'] = shadow.sp_pwd
            if shadow.sp_pwd == "!":
                info['disabled-login'] = True
        except KeyError:
            info['passwd'] = ''
            info['disabled-login'] = False

        return info

    def apply(self):
        info = self.get_user_info()

        if info['exists']:
            command = ['usermod']
            changed = False  # we may not change anything yet
        else:
            command = ['useradd', '-N']
            changed = True  # we definitely make a change

        name = self.resource.name

        fullname = self.resource.fullname
        if fullname and info["gecos"] != fullname:
            command.extend(["--comment", self.resource.fullname])
            changed = True

        password = self.resource.password
        if password and not info["exists"]:
            command.extend(["--password", self.resource.password])
            changed = True

        home = self.resource.home
        if home and info["dir"] != home:
            command.extend(["--home", self.resource.home])
            command.append("-m")
            changed = True

        uid = self.resource.uid
        if uid and info["uid"] != int(uid):
            command.extend(["--uid", str(self.resource.uid)])
            changed = True

        gid = self.resource.gid
        group = self.resource.group
        if gid or group:
            if gid:
                gid = int(gid)
                if gid != info["gid"]:
                    command.extend(["--gid", str(self.resource.gid)])
                    changed = True
            else:
                try:
                    gid = platform.getgrnam(group).gr_gid
                except KeyError:
                    self.raise_or_log(error.InvalidGroup('Group "%s" is not valid' % group))
                    gid = "GID_CURRENTLY_UNASSIGNED"

                if gid != info["gid"]:
                    command.extend(["--gid", str(gid)])
                    changed = True

        groups = self.resource.groups
        if groups:
            desired_groups = set(groups)
            current_groups = set(
                g.gr_name for g in platform.getgrall() if name in g.gr_mem)

            append = self.resource.append
            if append and len(desired_groups - current_groups) > 0:
                if info["exists"]:
                    command.append("-a")
                command.extend(["-G", ",".join(desired_groups - current_groups)])
                changed = True
            elif not append and desired_groups != current_groups:
                command.extend(["-G", ",".join(desired_groups)])
                changed = True

        shell = self.resource.shell
        if shell and shell != info["shell"]:
            command.extend(["--shell", str(self.resource.shell)])
            changed = True

        disabled_login = self.resource.disabled_login
        if disabled_login and not info["disabled-login"]:
            command.extend(["--password", "!"])
            changed = True

        system = self.resource.system
        if not info["exists"] and system:
            command.extend(["--system"])
            changed = True

        command.extend([self.resource.name])

        if changed:
            try:
                self.change(ShellCommand(command))
            except error.SystemError as exc:
                raise error.UserAddError("useradd returned error code %d" % exc.returncode)
        return changed


class UserRemove(provider.Provider):

    policies = (resources.user.UserRemovePolicy,)

    def apply(self):
        try:
            platform.getpwnam(self.resource.name.encode("utf-8"))
        except KeyError:
            # If we get a key errror then there is no such user. This is good.
            return False

        command = ["userdel", self.resource.name]

        try:
            self.change(ShellCommand(command))
        except error.SystemError as exc:
            raise error.UserAddError("Removing user %s failed with return code %d" % (self.resource, exc.returncode))

        return True
