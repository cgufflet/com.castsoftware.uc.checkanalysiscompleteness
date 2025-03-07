'''
Created on 23 déc. 2015

Take an application and add a worksheet to an excel for unanalyzed files

@todo : add also existing analyzer for some languages (name and url)

@todo : what to do with project files ? pom, .eclipse, .csproj etc...


@author: MRO
'''
import os, re, logging
import math

from deliveryanalyzer import DeliveryFolderAnalyzer
from determinator import get_extension_from_keywords
from loganalyzer import LogAnalyzer
from sortedcontainers import SortedDict, SortedSet
from pathlib import PureWindowsPath
from magic import run_magic
from linguist import recognise_language, get_language_type, get_primary_file_extension
from commonpath import CommonPath
from detect_class_name import search_classes


def generate_report(application, workbook, version=None, previously_unanalysed=set()):
    """
    Generate a worksheet report for files not analyzed in application
    """
    
    app = Application(application, version, previously_unanalysed)
    return app.generate_report(workbook)



class Application:
    """
    Application discovery for users.
    
    """
    def __init__(self, application, version=None, previously_unanalysed=set()):
        
        self.languages = SortedDict()
        
        self.application = application
        self.version = version
        self.__previously_unanalysed = previously_unanalysed
        
        # file count limits for each root
        self.root_limit = {}
        self.cms_roots = False
        self.delivery_path = self.application.get_managment_base().get_delivery_path()

        # TODO : get from CastGlobalSettings.ini
        self.log_root_path = os.path.expandvars("%ProgramData%\\CAST\\CAST\\Logs\\") + self.application.name
        # analyze logs
        for root, dirs, files in os.walk(self.log_root_path):
            for dir in dirs:
                if dir.startswith("Execute_Analysis"):
                    self.last_analysis_path = os.path.join(self.log_root_path, dir)


        self.packages = []
        
        self.file_count_01 = 0
        self.file_count_02 = 0
        self.file_count_03 = 0

        # first calculate deployment root path
        self.root_path = self.__get_root_path()

        # then compute list of DMT source location (to see which files have been ignored)
        self.delivery_root_paths = self.__get_delivery_root_paths()

        self.languages_with_delivered_files = SortedSet()
        self.delivered_files_per_languages = SortedDict()

        # then get all files from delivery source folders
        self.all_files = self.__get_all_files()

        # then get all the analysed files
        self.analyzed_files = self.__get_analysed_file_pathes()
         
        # then scan folder to find the files that where not taken into account
        self.unanalyzed_files = self.__get_unanalysed_files()
         

        self.languages_with_unanalysed_files = SortedSet()
        self.unanalysed_files_per_languages = SortedDict()

        self.languages_with_analysed_files = SortedSet()
        self.analysed_files_per_languages = SortedDict()
         
        # get the missing languages
        self.__get_languages()
        
        # scan xml files...
        #self.__scan_xml_files()
        
    
    def generate_report(self, workbook):
        """
        Generate a worksheet report for files not analyzed in application
        """
        # new file report per file extension
        self.list_files_per_extension(workbook)
        # summary
        percentage, summary = self.summary(workbook)
        
        # for debug 
        self.list_files(workbook)
        
        # un analysed files per language
        self.list_unanalysed(workbook)
        
        # delta
        new_unanalysed_count = self.list_new_unanalysed(workbook)
        
        analyzed_count = len(self.analyzed_files)
        unanalyzed_count = len(self.unanalyzed_files)
        total = analyzed_count + unanalyzed_count
        
        percentage_of_new_unanalysed = new_unanalysed_count / total * 100
               
        summary.write(2, 2, 'Percentage of new unanalyzed files')
        percent_format = workbook.add_format({'num_format': '0.00"%"'}) 
        summary.write(2, 3, math.ceil(percentage_of_new_unanalysed), percent_format)
        # end delta
        
        # debug infos
        self.debug(workbook)


        
        return percentage, percentage_of_new_unanalysed
    
    def summary(self, workbook):
        
        worksheet = workbook.add_worksheet('Summary')
    
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 50)
        worksheet.set_column(3, 3, 50)
            
        worksheet.write(0, 0, 'Analyzed files count')
        worksheet.write(0, 1, len(self.analyzed_files))
        
        worksheet.write(1, 0, 'Unanalyzed files count')
        worksheet.write(1, 1, len(self.unanalyzed_files))
        
        percent_format = workbook.add_format({'num_format': '0.00"%"'}) 
        
        worksheet.write(2, 0, 'Percentage of unanalyzed files')
        
        analyzed_count = len(self.analyzed_files)
        unanalyzed_count = len(self.unanalyzed_files)
        total = analyzed_count + unanalyzed_count
        percentage = 0
        
        if total:
            percentage = unanalyzed_count / total * 100
            worksheet.write(2, 1, math.ceil(percentage), percent_format)
        
        # unhandled detected languages and their remediation
        
        format = workbook.add_format({'bold': True, 'font_color': 'green'})
        
        worksheet.write(4, 0, 'Detected languages with unanalyzed files', format)
        worksheet.write(4, 1, 'Number of files', format)
        worksheet.write(4, 2, 'Can be analysed with', format)
        worksheet.write(4, 3, 'Documentation', format)
        row = 5
        
        important = []
        unknown = []
        useless = []

        for language in self.languages_with_unanalysed_files:
            
            core = language.has_core()
            extension = language.has_ua()
            if core or extension or language.name == 'XML Framework':
                important.append(language)
            elif language.is_useless():
                useless.append(language)
            else:
                unknown.append(language)
        
        def print_language(language, row, format):
            worksheet.write(row, 0, language.name, format)
            worksheet.write(row, 1, len(self.unanalysed_files_per_languages[language]), format)
            
            core = language.has_core()
            extension = language.has_ua()
            
            if core:
                worksheet.write(row, 2, 'Use %s analyzer' % core)
            elif extension:
                worksheet.write(row, 2, 'Use extension %s' % extension[0])
                worksheet.write(row, 3, '%s' % extension[1])
            elif language.name == 'XML Framework':
                worksheet.write(row, 2, 'Those XML files contain references to classes, maybe an unsupported framework')

        important_format = workbook.add_format()
        important_format.set_bg_color('#FFC7CE')
            
        unknown_format = workbook.add_format()

        useless_format = workbook.add_format()
        useless_format.set_bg_color('#C6EFCE')
        
        # severe issues
        for language in important:
            print_language(language, row, important_format)
            row += 1
            
        row += 2

        for language in unknown:
            print_language(language, row, unknown_format)
            row += 1
            
        row += 2

        for language in useless:
            print_language(language, row, useless_format)
            row += 1
            
        row += 2
            
        return percentage, worksheet
    
    def list_files(self, workbook):
        """
        For debug. 
        Fill in a worksheet with list of files + types
        """
        worksheet = workbook.add_worksheet('Analyzed Files List')
        
        worksheet.write(0, 0, 'Type')
        worksheet.write(0, 1, 'Path')
        
        row = 1
        
        for f in self.application.get_files():
            if hasattr(f,'get_path') and f.get_path():
                if not ".net generated files" in f.get_path():
    
                    worksheet.write(row, 0, f.get_type())
                    worksheet.write(row, 1, f.get_path())
                    
                    row += 1
    
        # add filters from (0, 0) to (1, row)
        worksheet.autofilter(0, 0, row, 0)        
    
    def list_unanalysed(self, workbook):
    
        # unanalysed files
        worksheet = workbook.add_worksheet('Files Not Analyzed')
    
        # order the data according to something stable : language name + path 
        files_per_language = self.unanalysed_files_per_languages
    
        # fill in report
        worksheet.write(0, 0, 'Language')
        worksheet.write(0, 1, 'Path')
        worksheet.write(0, 2, 'CMS Package')
        
        row = 1
        width = 30 
        
        for language in files_per_language:
            
            for _file in files_per_language[language]:
                worksheet.write(row, 0, str(language))
                worksheet.write(row, 1, str(_file.path))
                worksheet.write(row, 2, str(_file.get_package_name()))
                
                row += 1
                
                width = max(width, len(str(_file.path)))
        
        # auto set width of column (max width have been calculated along the way)
        worksheet.set_column(1, 1, width)
        
        # add filters from (0, 0) to (1, row)
        worksheet.autofilter(0, 0, row-1, 2)        
    
    
    def list_new_unanalysed(self, workbook):
        
        worksheet = workbook.add_worksheet('New Files Not Analyzed')
        
        # order the data according to something stable : language name + path 
        files_per_language = self.unanalysed_files_per_languages
    
        # fill in report
        worksheet.write(0, 0, 'Language')
        worksheet.write(0, 1, 'Path')
        worksheet.write(0, 2, 'CMS Package')
        
        row = 1
        width = 30 
        new_unanalysed_count = 0
        
        
        for language in files_per_language:
            
            for _file in files_per_language[language]:
                
                if str(_file.path) not in self.__previously_unanalysed: 
                    worksheet.write(row, 0, str(language))
                    worksheet.write(row, 1, str(_file.path))
                    worksheet.write(row, 2, str(_file.get_package_name()))
                    
                    row += 1
                    
                    width = max(width, len(str(_file.path)))
                    
                    new_unanalysed_count += 1
        
        # auto set width of column (max width have been calculated along the way)
        worksheet.set_column(1, 1, width)
        
        # add filters from (0, 0) to (1, row)
        worksheet.autofilter(0, 0, row-1, 2)        
        
        return new_unanalysed_count
        
    
    def debug(self, workbook):
    
        kb = self.application.get_knowledge_base()
    
        worksheet = workbook.add_worksheet('Debug')

        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 100)
        worksheet.set_column(2, 2, 50)

        worksheet.write(0, 0, 'CAIP version')
        worksheet.write(0, 1, str(kb.get_caip_version()))
    
        line = 1
        if self.version:

            worksheet.write(line, 0, str(self.version))
            line += 1
            
    
        worksheet.write(line, 0, 'Extensions')
        
        line += 1
        
        for extension, version in kb.get_extensions():
            
            worksheet.write(line, 1, extension)
            worksheet.write(line, 2, str(version))
            line += 1
        

        worksheet.write(line, 0, 'Root pathes')
        line+= 1
        
        for path in self.root_path:
            
            worksheet.write(line, 1, str(path))
            line += 1
        
        worksheet.write(line, 0, 'roots found with')
        worksheet.write(line, 1, 'CMS' if self.cms_roots else 'KB')
        line+= 1
        
        for path in self.root_limit:
            
            worksheet.write(line, 0, 'limit reached')
            worksheet.write(line, 1, str(path))
            line += 1
            
        worksheet.write(line, 0, 'file count 01')
        worksheet.write(line, 1, self.file_count_01)
        line+= 1
            
        worksheet.write(line, 0, 'file count 02')
        worksheet.write(line, 1, self.file_count_02)
        line+= 1

        worksheet.write(line, 0, 'file count 03')
        worksheet.write(line, 1, self.file_count_03)
        line+= 1

    def list_files_per_extension(self, workbook):

        # analyze logs
        logAnalyzer = LogAnalyzer(self.last_analysis_path)
        logAnalyzer.scan()


        # create worksheet
        worksheet = workbook.add_worksheet('Files per technology')

        worksheet.write(0, 0, 'File extension')
        worksheet.write(0, 1, 'Linked Technology')
        worksheet.write(0, 2, 'Nb Files found')
        worksheet.write(0, 3, 'Nb Files excluded')
        worksheet.write(0, 4, 'Nb Files processed')
        worksheet.write(0, 5, 'Nb Files saved')
        worksheet.write(0, 6, 'Nb Files skipped')
        worksheet.write(0, 7, 'Nb Files partially analyzed')
        worksheet.write(0, 8, 'Nb Files Not resolved')
        worksheet.write(0, 9, 'Supported by')


        worksheet.set_column(0, 0, 15)
        worksheet.set_column(0, 1, 20)
        worksheet.set_column(0, 2, 20)
        worksheet.set_column(0, 3, 20)
        worksheet.set_column(0, 4, 20)
        worksheet.set_column(0, 5, 20)
        worksheet.set_column(0, 6, 20)
        worksheet.set_column(0, 7, 20)
        worksheet.set_column(0, 8, 20)
        worksheet.set_column(0, 9, 20)

        row = 0
        list_files = SortedSet()
        for language in self.analysed_files_per_languages:
            if language.is_programming() and not language.is_useless():
                row += 1
                worksheet.write(row, 0, language.get_primary_file_extension())
                worksheet.write(row, 1, language.name)
                nb_analyzed_files = len(self.analysed_files_per_languages[language])
                nb_skipped_files = 0

                try:
                    for unanalyzed_files in self.unanalysed_files_per_languages[language]:
                        path = str(unanalyzed_files.path)
                        if path in logAnalyzer.files_skipped:
                            nb_skipped_files +=1
                except KeyError:
                    pass

                delivered_files_count = len(self.delivered_files_per_languages[language])

                worksheet.write(row, 2, delivered_files_count)

                try:
                    unanalysed_files_count = len(self.unanalysed_files_per_languages[language])
                    worksheet.write(row, 4, nb_analyzed_files + unanalysed_files_count)
                    worksheet.write(row, 3, delivered_files_count - nb_analyzed_files - unanalysed_files_count)
                except KeyError:
                    worksheet.write(row, 4, nb_analyzed_files)
                    worksheet.write(row, 3, delivered_files_count - nb_analyzed_files )
                    pass


                worksheet.write(row, 5, nb_analyzed_files)
                worksheet.write(row, 6, nb_skipped_files)

                worksheet.write(row, 9, language.get_extension_id())

        # loop on languages not analyzed at all
        for language in self.unanalysed_files_per_languages:
            if language.is_useless() or not language.is_programming():
                continue

            if language in self.analysed_files_per_languages:
                continue

            row += 1
            worksheet.write(row, 0, language.get_primary_file_extension())
            worksheet.write(row, 1, language.name)
            delivered_files_count = len(self.delivered_files_per_languages[language])
            worksheet.write(row, 2, delivered_files_count)

            try:
                unanalysed_files_count = len(self.unanalysed_files_per_languages[language])
                worksheet.write(row, 4, unanalysed_files_count)
                if unanalysed_files_count > delivered_files_count:
                    worksheet.write(row, 2, unanalysed_files_count)
                    worksheet.write(row, 3, 0)
                else:
                    worksheet.write(row, 3, delivered_files_count - unanalysed_files_count)

            except KeyError:
                worksheet.write(row, 4, 0)


            worksheet.write(row, 5, 'N/A')
            worksheet.write(row, 6, 'N/A')
            worksheet.write(row, 7, 'N/A')
            worksheet.write(row, 8, 'N/A')
            worksheet.write(row, 9, language.get_extension_id())

    def get_language(self, name):
        """
        Get a language per name.
        """
        if name in self.languages:
            return self.languages[name]
        
        result = Language(name)
        self.languages[name] = result 
        return result
    
    def __get_unanalysed_files(self):
        """
        Find all unanalyzed file of an application
        
        :rtype: collection of File
        
        Those files are not present in KB's application
        They are text files or xml files
        Some files are excluded by known extensions
        """
        all_files = set()
        # get root path
        for root in self.root_path:
        
            logging.info("Using Source root path : %s", root)
            
            # paranoid : if root path is too short (C: for example) skip
            if root == PureWindowsPath('C:\\') or root == PureWindowsPath('C:'):
                logging.info("Source root path found is invalid, aborting.")
                continue
        
            logging.info("Scanning Source root path content...")
            all_files |= self.__scan_all_files(str(root))

    
        analysed_files = self.analyzed_files
    
        logging.info("Comparing files...")
        
        unanalysed_files = all_files - analysed_files
        self.file_count_01 = len(unanalysed_files)

        # first exclude some useless, already known files
        #unanalysed_files = list(self.__filter_known(unanalysed_files))

        self.file_count_02 = len(unanalysed_files)
        
        logging.info("Recognizing text files using magic. May take some time...")
        
        #unanalysed_files = self.__filter_text(unanalysed_files)
        
        self.file_count_03 = len(unanalysed_files)
        logging.info("Found  %s unanalyzed text files", len(unanalysed_files))
        
        return unanalysed_files

    def __get_all_files(self):
        """
        Find all files from delivery folders (and not from deployment folder) of an application

        :rtype: collection of File

        They are text files or xml files
        Some files are excluded by known extensions
        """
        all_files = set()
        # get root path
        for root in self.delivery_root_paths:

            logging.info("Using Delivery Source root path : %s", root)

            # paranoid : if root path is too short (C: for example) skip
            if root == PureWindowsPath('C:\\') or root == PureWindowsPath('C:'):
                logging.info("Source root path found is invalid, aborting.")
                continue

            logging.info("Scanning Source root path content...")
            all_files |= self.__scan_all_files(str(root))

        # first exclude some useless, already known files
        #all_files = list(self.__filter_known(all_files))

        #logging.info("Recognizing text files using magic. May take some time...")
        #all_files = self.__filter_text(all_files)

        logging.info("Found  %s files", len(all_files))

        logging.info('Scanning languages for all delivered files...')
        for _file in all_files:
            language = _file.get_language(self)
            self.languages_with_delivered_files.add(language)
            if not language in self.delivered_files_per_languages:
                # sorted also here
                self.delivered_files_per_languages[language] = SortedSet()

            self.delivered_files_per_languages[language].add(_file)

        for language in self.languages_with_delivered_files:
            print ('Count %s : %d' % (language.name, len(self.delivered_files_per_languages[language])))

        return all_files

    def __get_root_path(self):
        """
        Access the root source pathes of an application if found.
        
        :return: list of PureWindowsPath
        
        It is an approximation of the reality. 
        
        We take all files of the application and take the most common path of those.
        
        Example : 
          
          - S:\SOURCES\D1\f1.txt
          - S:\SOURCES\D2\f1.txt
          
          --> S:\SOURCES
          
        It will miss folders for how no file is analysed : 
        
        root 
          D1 ... some analysed files   
          D2.. no analysed files
          
        --> root/D1 and missed D2.
          
        """
        logging.info("Searching for source root path...")
        
        try:
            app = self.application.get_application_configuration()
            
            result = set()
            for package in app.get_packages():
                result.add(PureWindowsPath(package.get_path()))
                self.packages.append(package)

            logging.info("Using packages from CMS")
            self.cms_roots = True
            return result
        
        except:
            logging.info("Using KB heuristic")
            self.cms_roots = False
        
        pathes = set()
        
        for f in self.application.get_files():
            if hasattr(f,'get_path') and f.get_path():
                
                path = f.get_path()
                
                # exclude some known generated files
                if ".net generated files" in path:
                    continue
                
                if path.startswith('['):
                    # inside a jar 
                    continue
                
                pathes.add(path.lower())
    
        common = CommonPath(pathes)
        
        # try common first
        result = common.common()
        if not result or result.endswith(':'):
            # if pathological then natural
            result = common.natural()

        result = result.lower()

        # convention : normally application root is ...\deploy\<application name>
        guess = '\\deploy\\' + self.application.name.lower()
        if guess in result:
            logging.info('Found deploy\<app name>. Thank you, following convention renders my job easier.')
            result = result[0:result.find(guess)]+guess

        return [PureWindowsPath(result)]
    
    
    def __get_analysed_file_pathes(self):
    
        files = [f for f in self.application.get_files(external=False) if hasattr(f, 'get_path')]
        return set([File(f.get_path()) for f in files if f.get_path()])
        
    
    def __scan_all_files(self, root):
        """
        Give all file of a folder
        
        """
        
        # give a limit of number of scanned files to avoid pathological cases 
        limit = 200000
        
        result = set()

        # find package         
        package = None
        if self.packages:
            
            # there may be several packages containing the path...
            for p in self.packages:
                
                if str(PureWindowsPath(p.get_path())) in root:
                    
                    if package:
                        # ambiguity
                        # take the longest one
                        if len(p.get_path()) > len(package.get_path()):
                            package = p
                    else:                    
                        package = p
        
        for dirname, _, filenames in os.walk(root):
        
            # print path to all filenames.
            for filename in filenames:
                result.add(File(os.path.join(dirname, filename), package))
                
                # paranoid
                if len(result) > limit:
                    self.root_limit[root] = True
                    return result
                
                
        return result
    
    
    def __filter_known(self, files):
        """
        Filter out files considered as not interesting.
        
        jars, dlls, txt files etc...
        VAST....uax, VAST...src
        """
        
        # skipping by glob style file patterns
        # @see https://docs.python.org/3.4/library/glob.html
        excluded_patterns = [
                             # cast extractions
                             "VAST*.src", 
                             "*.uax",
                             "*.uaxdirectory",
                             
                             # assembly extraction
                             "PE.CastPeDescriptor",
                             
                             # binaries
                             "*.jar",
                             "*.dll",
                             "*.exe",
                             "*.pdf",
                             
                             # ms build
                             "*/Debug/*",
                             "*/Release/*",
                             
                             # cvs
                             ".cvsignore",
                             
                             # Team Foundation 
                             ".tfignore", 
                             
                             # svn
                             "*.mine",
                             "*.theirs", 
                             
                             # Git 
                             ".gitignore", 
                             "*.gitattributes",
                             ".ratignore", 
                             ".gitmodules",
                             "CNAME", 
                             
                             # Apache
                             "*.htaccess",
                             "mod_jk.conf", 
                             "httpd.conf",
                             "deny-access.conf", 
                             "default_mod_jk.conf",
                             "cgi.conf", 
                                                          
                             # csslint
                             ".csslintrc",
                             
                             # Bower 
                             ".bowerrc", 
                             
                             # Checkstyle 
                             "checkstyle.xml", 
                             
                             # Eclipse
                             "oracle.eclipse.tools.webtier.ui.prefs", 
                             "org.jboss.ide.eclipse.as.core.prefs", 
                             ".faces-config.xml.jsfdia", 
                             
                             # Forge de devpt Safran 
                             "Checks_Spi4j.xml", 
                             "PMD_Spi4j.xml", 
                             
                             # StyleCop 
                             "StyleCop.Cache", 
                             "Settings.StyleCop", 
                             
                             # SharpCover
                             "*.SharpCover", 
                             
                             # Travis 
                             "travis.yml", 
                             
                             # sonar 
                             "sonar.yml",    
                             
                             # Gatling Performance Testing 
                             "gatling.conf",    
                             
                             # BitHound Code and Dependencies Analysis 
                             "*.bithoundrc", 
                             
                             # Node Version Manager 
                             "*.nvmrc", 
                             
                             # Mocha 
                             "mocha.opts", 
                             
                             # GUI prototyping tool  
                             "*.ep", 
                             
                             # Modeling tools 
                             "*.aird", 
                             "*.ois", 
                             
                             # HTTP Archive Valider 
                             "har-validator", 
                             
                             # Docker 
                             "Dockerfile",
                             ".dockerignore",              
                                                          
                             # Ansible 
                             "*.conf.j2", 
                             
                             # npm
                             ".npmignore", 
                             
                             # jshint
                             "jshint", 
                             ".jshintrc",
                             ".jshintignore", 
                             ".jshintrc-spec",
                             
                             # TSLint 
                             ".lint", 
                             ".lintignore", 
                             
                             "lcov.info", 
                             
                             # CoffeeScript  
                             "Cakefile", 
                             
                             # JSCS : Javascript code style linter and formatter 
                             ".jscsrc", 
                             ".eslintignore", 
                             ".eslintrc", 
                             
                             # Tern : a stand-alone code-analysis engine for JavaScript
                             ".tern-project", 
                             
                             # uglifyjs
                             "uglifyjs", 
                             
                             # JS and CSS SourceMaps 
                             "*.js.map", 
                             "*.css.map",    
                             "*.min.map",
                             "*-min.map", 
                             
                             # Android Studio build files
                             "settings.gradle",      
                             "build.gradle",     
                             "cordova.gradle",   
                             "build-extras.gradle",                       
                             
                             # Maven wrappers 
                             "mvnw", 
                             
                             # Maven integrity checksums, ... 
                             "*.jar.sha1", 
                             "*.pom.sha1", 
                             "*.libd.sha1", 
                             "*.pom.sha1-in-progress", 
                             "*.jar.sha1-in-progress", 
                             "*.pom",
                             "*.md5",
                             "_maven.repositories",
                             "m2e-lastUpdated.properties",
                             "_remote.repositories", 
                             "*.pom.lastUpdated",
                             "*.jar.lastUpdated",
                             
                             # EditorConfig 
                             ".editorconfig", 
                             
                             # Dreamweaver or Contribute Macromedia Design Note files 
                             "*.mno", 
                                                          
                             # Eclipse, do we need to exclude ?
                             "pom.xml", 
                             ".project",
                             ".classpath",
                             
                             ".vbproj",
                             
                             # Various
                             "*.log",
                             "*.txt",
                             ".hidden", 
                             ".ignore", 
                             "*.md", # markdown
                             "*.csv",
                             "*.xsd", # schema definition... not interesting 
                             
                             # License file 
                             "LICENSE",
                             "LICENCE", 
                             "LICENSE-MIT",
                             "LICENSE.MIT", 
                             "LICENSE.BSD", 
                             "MIT.LICENSE", 
                             "LICENSE.APACHE2", 

                             "UNLICENSE",                
                             "COPYING", 
                             "BUGS",

                             "AUTHORS",
                             "OWNERS", 
                             "CONTRIBUTORS", 
                             "CREDITS", 
                             "MAINTAINERS", 
                             "TESTERS",
                             "Testers", 

                             "VERSION",
                             "WhatsNew", 
                             "NEWS", 
                             "CHANGELOG", 
                             "changelog", 
                             "Changelog", 
                             "NOTICE", 
                             "USAGE",
                             "TODO",                              
                             "IDEAS", 
                             "Ideas",
                             "STATUS", 
                             "Status", 
                             
                             "PKG-INFO", 
                             
                             "README", 
                             "README.*", 
                             "TROUBLESHOOTING",
        
                             # Excel
                             "*.xls",
                             "*.xlsx",
                             
                             # c++ headers are not interesting, for example external .h 
                             # interesting is .cpp
                             "*.hh",
                             "*.h++",
                             "*.hpp",
                             "*.hcc",
                             "*.h",
                             "*.hxx",
                             "*.ph", # see https://castsoftware.zendesk.com/agent/tickets/16477
                             
                             # skipped by analyser
                             "package-info.java",
                             
                             # java deployment
                             "MANIFEST.MF",
                        
                             # microsoft database project
                             "*.dbp",
                             # microsoft project...
                             "*.sln",
                             "*.vspscc",
                             "*.vdproj",
                             "*.csproj",
                             "*.vssscc",
                             "*.csproj.user",
                             
                             # Public Private Key Certificate 
                             "*.pkcs8.base64", 
                             "*.key", 
                             "*.crt", 
                             "*.pem",
                             "*.priv",  
                             
                             # xcode 
                             "*.xcbkptlist", # breakpoints
                             "*.xcwordspacedata",
                             
                             # do not laugh, I have seen it 
                             "tnsnames.ora",
                             
                             # abap useless extracted files
                             '*CT.abap',
                             '*CP.abap',
                             'SAP*.sap.xml',
                             'SAP*.SQLTABLESIZE',
                             
                             # some useless files 
                             '*.factorypath', 
                             '*.script',
                             
                             # images
                             '*.svg', 
                             
                             # various
                             '*.dtd',
                             '*.tld',
                             "folder.info", 
                             
                             ]
        
        # this time full regular expressions
        complex_patterns = [
                            # svn example : .r2681
                            ".*\.r[0-9]+",
                            ".*\\\.svn\\.*",
                            # git 
                            ".*\\\.git\\.*",
                            # eclipse config
                            ".*org\.eclipse\..*", 
                            # abap program description
                            ".*\\PG_DESCR_.*\.xml",
                            # abap 
                            ".*\=CCAU\.abap", 
                            ".*\=IP\.abap", 
                            # cast extracts; e.g:
                            # S:\Sources\DB\GCP_EEN\EIR01PRW\DT.62.src
                            ".*\\.*\.[0-9]+\.src",
                            # DL.PUBLIC.A1ENB1D1.DB.ATT.COM.src
                            r".*\.PUBLIC\..*\.src",
                            # \CAST_TLG_PB\ap\src\apbill\apbill.pbl_CASTExtractor\d_bl_ur_thresholds_list.srd
                            r".*\.pbl_CASTExtractor.*",
                            # obvious node modules
                            r".*\node_modules\.*",
                            ]
        
        # special case for html5
        selected_javascript_pathes = []
        
        try:
            mngt_app = self.application.get_application_configuration()
            for analysis_unit in mngt_app.get_analysis_units():
                if 'HTML5/Javascript' in analysis_unit.get_technologies():
                    selected_javascript_pathes += [PureWindowsPath(p) for p in analysis_unit.get_included_selection()]

        except:
            pass

        def is_javascript_selected(f):
            # @type f: PureWindowsPath
            if f.suffix != '.js':
                return False
            for selected in selected_javascript_pathes:
                if str(selected) in str(f):
                    return True                
            return False

        
        def is_excluded(f):
            
            for pattern in excluded_patterns:
                if f.match(pattern):
                    return True
    
            for pattern in complex_patterns:
                
                if re.match(pattern, str(f)):
                    return True
                
            if is_javascript_selected(f):
                return True
            
            return False
        
    
        for f in files:
    
            # skip some
            if is_excluded(f.path):
                continue
            
            yield f
        
    
    def __filter_text(self, files):
        """
        return text files only
        """
        result = []
        
        m = {}
        
        for f in files:
            m[f.path] = f
        
        
        # consider only those that are text only
        magic = run_magic(m.keys())
    
        for f in magic:
            
            mime = f[1]
            content_type = mime[0]
            
            # @todo : may have other combinations to handle 
            if content_type == 'text' or len(mime) > 1 and mime[1] == 'xml':
                
                try:
                    _file = m[PureWindowsPath(f[0])]
                    # stores mime info on the file object
                    _file.mime_type = mime
                    result.append(_file)
                    
                except KeyError:
                    pass
                    
        return result

    def __get_languages(self):

        logging.info('Scanning languages for unanalyzed files...')
        for _file in self.unanalyzed_files:
            language = _file.get_language(self)
            self.languages_with_unanalysed_files.add(language)
            if not language in self.unanalysed_files_per_languages:
                # sorted also here
                self.unanalysed_files_per_languages[language] = SortedSet()
            
            self.unanalysed_files_per_languages[language].add(_file)

        logging.info('Scanning languages for analyzed files...')
        for _file in self.analyzed_files:
            language = _file.get_language(self)
            self.languages_with_analysed_files.add(language)
            if not language in self.analysed_files_per_languages:
                # sorted also here
                self.analysed_files_per_languages[language] = SortedSet()

            self.analysed_files_per_languages[language].add(_file)

    def __scan_xml_files(self):
        """
        Scan xml files and search for classes names.
        
        exclude tld files...
        """
        try:
            xml_files = self.unanalysed_files_per_languages[Language('XML')]
    
            logging.info('Scanning XML files for classes names...')
            
            files_with_classes = search_classes(xml_files, self.application.objects().has_type('Java').is_class())
            
            xml_framework_language = Language('XML Framework')
            
            xml_frameworks = SortedSet()
            
            for _file in files_with_classes:
                
                xml_frameworks.add(_file)
                self.languages_with_unanalysed_files.add(xml_framework_language)
                _file.language = xml_framework_language
                
            self.unanalysed_files_per_languages[Language('XML')] = xml_files - xml_frameworks
            self.unanalysed_files_per_languages[xml_framework_language] = xml_frameworks
        except:
            # no XML files
            pass

    def __get_application_guid(self):
        query = "select field_value from cms_dynamicfields dyn_fields join cms_portf_application apps on (dyn_fields.object_id = apps.object_id and dyn_fields.entity_guid='pmcportfolio.Application' and dyn_fields.field_guid='entry' and apps.object_name='" + self.application.name + "');"
        result = self.application.get_managment_base().execute_query(query)
        app_guid = None
        for guid in result:
            if app_guid:
                logging.warn('More than one app guid returned. Returning.')
                return None
            else:
                self.application_uuid = guid[0][5:]

        logging.info('App GUID: ' + self.application_uuid);

        return self.application_uuid

    def __get_version_guid(self):
        query = "select field_value from cms_dynamicfields dyn_fields join cms_portf_application apps on (dyn_fields.object_id = apps.version_id and dyn_fields.entity_guid='pmcdeliveryunit.ApplicationVersion' and dyn_fields.field_guid='entry' and apps.object_name='" + self.application.name + "');"
        result = self.application.get_managment_base().execute_query(query)
        version_guid = None
        for guid in result:
            if version_guid:
                logging.warn('More than one app guid returned. Returning.')
                return None
            else:
                self.version_uuid = guid[0][6:]

        logging.info('version GUID: ' + self.version_uuid);

        return self.version_uuid

    def __get_delivery_root_paths(self):
        list_root = []
        # get application and version uuid from management to scan delivery folder
        application_uuid = self.__get_application_guid()
        version_uuid = self.__get_version_guid()

        deliveryFolderAnalyzer = DeliveryFolderAnalyzer(self.delivery_path, '{' + application_uuid + '}', '{' + version_uuid + '}')
        list_root = deliveryFolderAnalyzer.scan()

        return list_root

class File:
    """
    Represent a file and informations found on it
    """
    
    def __init__(self, path, package=None):
        self.path = PureWindowsPath(path)
        self.mime_type = None
        # languages recognized by extensions
        self.languages = recognise_language(path)
        if not self.languages:
            #print("unrecognized language for file '%s'", path )
            pass
        else:
            try:
                if self.languages[0][1]['type'] == 'programming':
                    self.is_programming = True
                else:
                    self.is_programming = False
            except KeyError:
                self.is_programming = False

        self.language = "unknown"
        self.package = package
    
    def set_mime(self, mime):
        """
        Set mime type recognized by libmagic
        
        :param: mime a pair of string
        
        @see  http://www.iana.org/assignments/media-types/media-types.xhtml   
        """
        self.mime_type = mime

    def get_language(self, application):
        """
        Get the recognized language of the file. 
        """
        
        if self.languages:
            # if several choices... ????
            self.language = self.languages[0][0]
        else:
            
            # try mime type :
            if self.mime_type == ['application', 'xml']:
                self.language = 'XML'
            elif self.mime_type == ['text', 'html']:
                self.language = 'HTML'
        
        return application.get_language(self.language)
    
    def get_package_name(self):
        """
        CMS package name in which this file is found
        """
        if self.package:
            return self.package.name
        else:
            return "?"
    
    def __eq__(self, other):
        return self.path == other.path    

    def __lt__(self, other):
        return self.path < other.path
        
    def __hash__(self):
        return hash(self.path)


class Language:
    
    def __init__(self, name):
        self.name = name

    def has_core(self):
        """
        Return the associated core analyzer when available
        """
        map = {'C#':'.Net',
               'C++':'C/C++',
               'C':'C/C++',
               'Java':'JEE', 
               'Java Server Pages':'JEE',
               'COBOL':'Mainframe',
               'Pascal':'PowerBuilder',
               'ABAP':'SAP',
               'Visual Basic':'VisualBasic',
               }
        
        try:
            return map[self.name]
        except:
            pass
        

    def has_ua(self):
        """
        returns the extension/ua when available
        
        a couple : extension id + link to documentation
        """
        # @todo : list them all... 
        map = {
               'ActionScript':('com.castsoftware.flex', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.flex/'),
               'BIRT':('com.castsoftware.uc.birt', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.uc.birt/'),
               'CSS':('com.castsoftware.html5', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.html5/'),
               'EGL':('com.castsoftware.egl', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.egl/'),
               'FORTRAN':('com.castsoftware.fortran', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.fortran/'),
               'Objective-C':('com.castsoftware.ios', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.ios/'),
               'HTML':('com.castsoftware.html5', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.html5/'),
               'JavaScript':('com.castsoftware.html5', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.html5/'),
               'Perl':('com.castsoftware.perl', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.uc.Perl/'),
               'PHP':('com.castsoftware.php', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.php/'),
               'PL1':('com.castsoftware.pl1', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.pl1/'),
               'Python':('com.castsoftware.python', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.python/'),
               'RPG':('com.castsoftware.rpg', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.rpg/'),
               'Shell':('com.castsoftware.shell', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.shell/'),
               'SQL':('com.castsoftware.sqlanalyzer', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.sqlanalyzer/'),
               'TypeScript':('com.castsoftware.typescript', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.typescript/'),
               'Swift':('com.castsoftware.swift', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.swift/'),
               'BPEL':('com.castsoftware.bpel', 'https://extend.castsoftware.com/V2/packages/com.castsoftware.bpel/'),
               }

        try:
            return map[self.name]
        except:
            pass

    def get_extension_id(self):
        determinator_response = get_extension_from_keywords([self.name], "8.3.36")
        for lang in determinator_response:
            message = None
            for i in range(len(determinator_response[lang])):
                extension_uid = determinator_response[lang][i]['extensionuid']
                if extension_uid is None:
                    message = 'Not supported'
                elif extension_uid == 'com.castsoftware.aip':
                    # priority to extension above AIP
                    if message is None:
                        message = 'AIP'
                    continue
                else:
                    recommended_version = determinator_response[lang][i]['recommendedversion']
                    if recommended_version is None:
                        message = extension_uid
                    else:
                        message = extension_uid + ' (recommended=' + recommended_version + ')'

        return message

    def is_useless(self):
        """
        Some 'languages' are known as useless. 
        for example : ini, json, css ... 
        """
        
        useless = {'INF',
                   'INI',
                   'JSON',
                   'Puppet',
                   'Tag Library Descriptor',
                   'XSLT'
                   }
        
        return self.name in useless

    def get_language_type(self):
        return get_language_type(self.name)

    def is_programming(self):
        return get_language_type(self.name)=="programming"

    def get_primary_file_extension(self):
        return get_primary_file_extension(self.name)



    def __eq__(self, other):
        return self.name == other.name    

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name



    
    