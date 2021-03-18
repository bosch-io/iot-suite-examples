import os
import urllib.request
import subprocess

class ScriptExecutor:

    def executeFile(self, filePath)-> str:
        try:
            type = self.getExecutorType(filePath)
            print("executing '{}' command on file '{}'".format(type, filePath))
            execRes = self.executeLinuxCommands([type, filePath])
            res = ""
            for line in execRes:
                if(line):
                    res += line
            return res
        except:
          return "An exception occurred while executing" + filePath


    def getExecutorType(self,filePath):
        if filePath.endswith(".lua"):
            return "lua"
        elif filePath.endswith(".py"):
            return "python3"
        elif filePath.endswith(".sh"):
            return "bash"

    def executeLinuxCommands(self, bashCommands):
        popen = subprocess.Popen(bashCommands, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line 
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, bashCommands)
