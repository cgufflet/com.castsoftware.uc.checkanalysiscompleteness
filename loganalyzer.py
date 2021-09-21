"""
Log analyzer

Author: CGU - September 2021
"""
import os

class LogAnalyzer:
    def __init__(self, analysis_root_path):
        self.analysis_root_path = analysis_root_path
        self.files_skipped = []
        self.files_processed = []

    def scan(self):
        exclude_file_patterns = ["MA_", "Run_CSV", "BeforeApplicationExtensions", "ApplicationExtensions"]

        list_analyzer_files = []
        # filter only on analyzer castlog files
        for root, dirs, files in os.walk(self.analysis_root_path):
            for logfile in files:
                exclude = False
                # exclude non analyzer logs
                for exclude_pattern in exclude_file_patterns:
                    if logfile.startswith(exclude_pattern):
                        exclude = True
                        break

                if not logfile.endswith('.castlog'):
                    exclude = True

                if not exclude:
                    list_analyzer_files.append(logfile)
        # detect technologies for each log file
        for logfile in list_analyzer_files:
            if logfile.startswith('HTML5'):
                self.process_html5_log(logfile)
            elif '_PHP_' in logfile:
                self.process_php_log(logfile)
            elif '_Python_' in logfile:
                self.process_python_log(logfile)
            elif '_SHELL_' in logfile:
                self.process_shell_log(logfile)
            elif 'UA-SQL_' in logfile:
                self.process_sql_log(logfile)
            else:
                with open(os.path.join(self.analysis_root_path, logfile), 'r', encoding='utf-8') as smart_job_file:
                    for line in smart_job_file:
                        if "About to run" in line:
                            if 'CAST_DotNet_Job_NewAnalyzer' in line:
                                self.process_dotnet_log(logfile)
                            elif 'JOB_JSP_ANALYZER' in line:
                                self.process_jee_log(logfile)
                            elif 'CAST_Web_Asp_JobAnalyzer' in line:
                                self.process_asp_log(logfile)
                            elif 'JOB_C_ANALYZER' in line:
                                self.process_c_log(logfile)
                            elif 'JOB_FORMS_ANALYZER' in line:
                                self.process_forms_log(logfile)
                            elif 'JOB_MAINFRAME_ANALYZER' in line:
                                self.process_mainframe_log(logfile)




    def process_html5_log(self,logfilename):
        print("Processing HTML5 analyzer log...")
        with open(os.path.join(self.analysis_root_path, logfilename), 'r', encoding='utf-8') as html_log_file:
            processed = 0
            skipped = 0
            for line in html_log_file:
                if 'Starting processing of file' in line:
                    processed +=1
                    filepath = line[line.rfind('\a') + 1:].strip()
                    self.files_processed.append(filepath)
                elif 'has been skipped' in line or 'Skipping TypeScript declaration file' in line:
                    if 'Starting processing of file' in previous_line:
                        skipped +=1
                        self.files_skipped.append(filepath)

                previous_line = line

            print("Files processed: ", processed )
            print("Files skipped: ", skipped)

    """
            extension_split = dict()

            for file_skipped in self.files_skipped:
                extension = file_skipped[file_skipped.rfind('.') + 1:].lower()
                if not extension in extension_split:
                    extension_split[extension] = 0

                extension_split[extension] += 1


            for extension in extension_split:
                print(extension, extension_split[extension])
    """


    def process_dotnet_log(self,logfile):
        print("Processing .NET analyzer log...")
        pass

    def process_jee_log(self,logfile):
        print("Processing JEE analyzer log...")
        pass

    def process_sql_log(self,logfile):
        print("Processing SQL analyzer log...")
        pass

    def process_php_log(self,logfile):
        print("Processing PHP analyzer log...")
        pass

    def process_python_log(self,logfile):
        print("Processing Python analyzer log...")
        pass

    def process_shell_log(self,logfile):
        print("Processing SHELL analyzer log...")
        pass

    def process_mainframe_log(self,logfile):
        print("Processing Mainframe analyzer log...")
        pass

    def process_c_log(self,logfile):
        print("Processing C/C++ analyzer log...")
        pass

    def process_asp_log(self, logfile):
        print("Processing ASP analyzer log...")
        pass

    def process_forms_log(self, logfile):
        print("Processing Oracle Forms analyzer log...")
        pass


if __name__ == "__main__":
    logAnalyzer = LogAnalyzer('C:\\ProgramData\\CAST\\CAST\\Logs\\eTraq\\Execute_Analysis_164')
    logAnalyzer.scan()