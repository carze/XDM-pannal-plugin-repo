# Author: panni <panni@fragstore.net>
# URL: https://github.com/pannal/XDM-pannal-plugin-repo/
#
# This file is part of a XDM plugin.
# based on de.lad1337.simple.mover and de.lad1337.movie.simplemover
#
# XDM plugin.
# Copyright (C) 2014  panni
#
# This plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm.plugins import *
from xdm import helper
import time
import os
import shutil

class AdvancedMover(PostProcessor):
    """
    more or less advanced moving postprocessor
    """
    identifier = 'de.pannal.advancedmover'
    version = "0.1"
    _config = {
                'copy': False,
                'skip_sample': False,
                "replace_space_with": " ",
                'final_path': "",
                "rename_folders_to_element": False,
                "rename_files_to_element": False,
                'allowed_extensions': {
                        "options": [".avi", ".mkv", ".iso", ".mp4", ".m4v", ".mp3", ".flac",
                                    ".aac", ".nfo", ".png", ".gif", ".bmp", ".jpg"],
                        "selected": [".avi", ".mkv"],
                        "use_checkboxes": True,
                        "required": True,
                    }
    }
    screenName = 'Advanced Mover'
    config_meta = {'plugin_desc': 'This will move all the files with the given extensions from the path that is given to the path specified.',
                   'replace_space_with': {'desc': 'All spaces for the final file will be replaced with this.'},
                   'copy': {'desc': 'If this is on the Folder will be copied instead of moved.'},
                   'skip_sample': {'desc': 'Skip sample files (mostly movies/TV)'},
                   }
    addMediaTypeOptions = "runFor"
    #useConfigsForElementsAs = 'Enable'
    _allowed_extensions = []
    _selected_extensions = []

    def __init__(self, instance='Default'):
        PostProcessor.__init__(self, instance=instance)
        self._allowed_extensions = self.c.allowed_extensions.options
        self._allowed_extensions_selected = self.c.allowed_extensions.selected

    def postProcessPath(self, element, filePath):
        destPath = self.c.final_path
        if not destPath:
            msg = "Destination path for %s is not set. Stopping PP." % element
            log.warning(msg)
            return (False, msg)
        # log of the whole process routine from here on except debug
        # this looks hacky: http://stackoverflow.com/questions/7935966/python-overwriting-variables-in-nested-functions
        processLog = [""]

        def processLogger(message):
            log.info(message)
            createdDate = time.strftime("%a %d %b %Y / %X", time.localtime()) + ": "
            processLog[0] = processLog[0] + createdDate + message + "\n"

        def fixName(name, replaceSpace):
            return helper.fileNameClean(name.replace(" ", replaceSpace))

        allFileLocations = []
        if os.path.isdir(filePath):
            processLogger("Starting file scan on %s" % filePath)
            for root, dirnames, filenames in os.walk(filePath):
                processLogger("I can see the files %s" % filenames)
                for filename in filenames:
                    if filename.endswith(self._allowed_extensions_selected):
                        if self.c.skip_sample and 'sample' in filename.lower():
                            processLogger("Skipping sample: %s" % filename)
                            continue
                        curImage = os.path.join(root, filename)
                        allFileLocations.append(curImage)
                        processLogger("Found file: %s" % curImage)
            if not allFileLocations:
                processLogger("No files found!")
                return (False, processLog[0])
        else:
            allFileLocations = [filePath]

        processLogger("Possibly renaming and moving Files")
        success = True
        allFileLocations.sort()
        dest = None
        for index, curFile in enumerate(allFileLocations):
            processLogger("Processing file: %s" % curFile)
            try:
                extension = os.path.splitext(curFile)[1]
                folderName = element.getName() if self.c.rename_folders_to_element else os.path.basename(os.path.dirname(curFile))
                fileNameBase = element.getName() if self.c.rename_files_to_element else os.path.splitext(os.path.basename(curFile))[0]
                if len(allFileLocations) > 1:
                    newFileName = u"%s CD%s%s" % (fileNameBase, (index + 1), extension)
                else:
                    newFileName = fileNameBase + extension
                newFileName = fixName(newFileName, self.c.replace_space_with)
                processLogger("New Filename shall be: %s" % newFileName)

                destFolder = os.path.join(destPath, folderName, self.c.replace_space_with)
                if not os.path.isdir(destFolder):
                    os.mkdir(destFolder)
                dest = os.path.join(destFolder, newFileName)

                if self.c.copy:
                    msg = "Copying %s to %s" % (curFile, dest)
                    shutil.copytree(curFile, dest)
                else:
                    msg = "Moving %s to %s" % (curFile, dest)
                    shutil.move(curFile, dest)

            except Exception, msg:
                processLogger("Unable to rename and move Movie: %s. Please process manually" % curFile)
                processLogger("given ERROR: %s" % msg)
                success = False

        processLogger("File processing done")
        # write process log
        logFileName = fixName("%s.log" % element.getName(), self.c.replace_space_with)
        logFilePath = os.path.join(filePath, logFileName)
        try:
            # This tries to open an existing file but creates a new file if necessary.
            logfile = open(logFilePath, "a")
            try:
                logfile.write(processLog[0])
            finally:
                logfile.close()
        except IOError:
            pass

        return (success, dest, processLog[0])