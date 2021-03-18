#!/usr/bin/python3

import os
import urllib.request


class DownloadManager:

    def download(self, artifact):
        dirPath = os.getcwd() + "/downloads"
        print ("Desired download directory is %s" % dirPath)
        if  not os.path.isdir(dirPath):
            print("Download directory must be created")
            try:
                os.mkdir(dirPath)
                print ("Successfully created the directory %s " % dirPath)
            except OSError:
                print ("Creation of the directory %s failed" % dirPath)
    
        filePath = dirPath + "/" + artifact.name
        urllib.request.urlretrieve(artifact.url, filePath)
        print('downloaded ' + artifact.name)
        return filePath
