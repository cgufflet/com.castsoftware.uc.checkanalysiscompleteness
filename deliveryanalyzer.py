"""
delivery folder analyzer

Author: CGU - September 2021
"""
import os
import lxml.etree as ET

class DeliveryFolderAnalyzer:
    """
        class to get list of source folders from all DMT file system packages for a given app and version
    """
    def __init__(self, delivery_root_path, application_uuid, version_uuid):
        # version comes from mngt schema
        self.version_uuid = version_uuid

        # concatenate application uuid to obtain folder containing versions for giving app
        s = (delivery_root_path + ',data,' + application_uuid + ',' + version_uuid).split(',')
        self.packages_root_path = os.path.join(*s)
        #self.packages_root_path = delivery_root_path


    def scan(self):
        list_source_folders = []
        # get source location before deployment (from file system packages)
        for root, dirs, files in os.walk(self.packages_root_path):
           for file in files:
               if file == 'config.DmtExtraction':
                    root = ET.parse(os.path.join(root, file))
                    extractor = root.xpath(r'/document/entity[@type="Extractor"]')
                    java_class_name = extractor[0].find(r'javaClassName')
                    # only keep
                    if java_class_name.text == 'com.castsoftware.dmt.extractor.filesystem.FileSystemExtractor':
                        source_root = extractor[0].find(r'connectionURL')
                        list_source_folders.append(source_root.text.strip())

        return list_source_folders


if __name__ == "__main__":
    deliveryFolderAnalyzer = DeliveryFolderAnalyzer('C:\\CAST\\AipConsole\\data\\AipNode\\delivery\\{0d538473-e280-47ae-b779-1593cda180ff}', '{0d538473-e280-47ae-b779-1593cda180ff}', '{8ce41aed-59a7-4b78-aaea-0db385367167}')
    #deliveryFolderAnalyzer = DeliveryFolderAnalyzer('C:\\CAST\\AipConsole\\data\\AipNode\\delivery', '')
    list_root = deliveryFolderAnalyzer.scan()
    for source_folder in list_root:
        print(source_folder)
