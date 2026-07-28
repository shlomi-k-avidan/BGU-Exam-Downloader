welcome_str = '''\033[0m\033[s\033[1;33;40m
                        ############################################################
                        #                                                          #
                        #       *******************************************        #
                        #                                                          #
                        #             /$$$$$$$  /$$$$$$$  /$$   /$$                #
                        #            | $$__  $$| $$____/ | $$  | $$                #
                        #            | $$  \ $$| $$      | $$  | $$                #
                        #            | $$$$$$$ | $$ $$$$$| $$  | $$                #
                        #            | $$__  $$| $$ _  $$| $$  | $$                #
                        #            | $$  \ $$| $$  \ $$| $$  | $$                #
                        #            | $$$$$$$/| $$$$$$$/|  $$$$$$/                #
                        #            |_______/ |_______/  \______/                 #
                        #                                                          #
                        #                   EZ EXAM DOWNLOADER                     #
                        #                                                          #
                        #       *******************************************        #
                        #                                                          #
                        ############################################################\033[0m\033[s
'''

import os
import datetime
import subprocess
import sys
import threading

#################################################################################

error_str           = "[X] "
success_str         = "[+] "
notification_str    = "[*] "
prompt_str          = "[#] "
padding_tabs        = '        '
error_color         = "\033[1;31;40m"
success_color       = "\033[1;32;40m"
notification_color  = "\033[1;36;40m"
prompt_color        = "\033[1;33;40m"
base_color          = "\033[1;{x};40m"
moed_colors         = [33, 35, 37]
semester_colors     = [34, 36, 32]
msclrfrmt_arrays    = [moed_colors, semester_colors]
msclrfrmt_strings   = ["Moed ", "Semester ", "Exam Grade: ", "Final Grade: "]
excelent_color      = "\033[1;34;40m"
perfect_color       = "\033[1;33;40m"
color_terminator    = "\033[0m\033[s"
col_num             = 140
row_num             = 38

def my_print(s):
    x = s.strip().split('\n')
    for x in s.split('\n'):
        string = ""
        for i in range(len(x)):
            if i == 0:
                string += padding_tabs
            elif i % (col_num-len(padding_tabs)) == 0: 
                string = string[:(len(string)-string[::-1].index(' ')-1):] \
                        + '\n' + padding_tabs + '    ' + string[(len(string)-string[::-1].index(' '))::]
            string += x[i]
        print(string.replace('\r',''))

def any_key(s):
    my_print(prompt_color + prompt_str + s + color_terminator)
    input()

def my_input(s):
    my_print(prompt_color + prompt_str + s + color_terminator)
    return str(input(padding_tabs + "    " + prompt_color + ">>>  " + color_terminator))

def print_success(s):
    my_print(success_color+success_str+s+color_terminator)

def print_error(s):
    my_print(error_color+error_str+s+color_terminator)

def print_notification(s):
    my_print(notification_color+notification_str+s+color_terminator)    

#################################################################################  

os.system("mode con cols={0} lines={1}".format(col_num,row_num))
print(color_terminator+welcome_str+color_terminator)
print_notification("Checking for dependencies...")

# Get dependencies automatically
dependency_flag = False
try:
    import requests
    print_success("REQUESTS dependency imported.")
except:
    print_error("Module REQUESTS not found. Attempting to run pip install openpyxl in order to install...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print_success("REQUESTS dependency installed successfully. Running program...")
    dependency_flag = True
try:
    import time
    print_success("TIME dependency imported.")
except:
    print_error("Module TIME not found. Attempting to run pip install openpyxl in order to install...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "time"])
    print_success("TIME dependency installed successfully. Running program...")
    dependency_flag = True
try:
    import base64
    print_success("BASE64 dependency imported.")
except:
    print_error("Module BASE64 not found. Attempting to run pip install openpyxl in order to install...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "base64"])
    print_success("BASE64 dependency installed successfully. Running program...")
    dependency_flag = True

if dependency_flag:
    subprocess.Popen([os.path.basename(__file__)],shell=True)
import base64
import time
import requests

#################################################################################

def msclrfrmt(string,flag):
    string = string.replace("00","100")
    if len(string) == 2:
        string = " " + string
    if flag < 2:
        try:
            if string == "K":
                return excelent_color+"Quiz"+notification_color
            return base_color.format(x=msclrfrmt_arrays[flag][ord(string)-ord('A')])+msclrfrmt_strings[flag]+str(string)+notification_color
        except:
            return error_color+str(string)+notification_color
    else:
        try:
            color = base_color.format(x=str(31+int(int(string)>=56 and int(string)<90)+3*int(int(string)>=90 and int(string)<100)+2*int(int(string)>=100)))
            return " " + color+msclrfrmt_strings[flag]+str(string)+notification_color
        except:
            return " " + base_color.format(x=str(39))+msclrfrmt_strings[flag]+str(string)+notification_color

def get_moed_str(moed):
    if 1 <= moed <= 4:
        return chr(ord('A')+moed-1)
    else:
        return 'QUIZ'

def async_exam_downloader(s, data, filename, course_id, moed, semester, year, site, download_page, pre_download_page, agent):
    r = s.post(site + download_page, data=data, timeout=100, headers={'User-Agent': agent, 'Content-Type': 'application/x-www-form-urlencoded', 'Referer': site + pre_download_page})
    if 'firewall' in r.text or 'cant open' in str(r.content):
        print_error("The following exam was not found in the database: Course ID {0}, Moed {1}, Semester {2} {3}.".format(course_id, moed, semester, year))
        raise
    elif 'No connection to database' in str(r.content):
        print_error("The exam database is currently offline. Please try downloading your exam later.")
        raise
    try:
        with open(filename, 'wb') as f:
            f.write(r.content)
        print('\n')
        print_success("Succesfully downloaded exam: Course ID {0}, Moed {1}, Semester {2} {3}.".format(course_id, moed, semester, year))
        subprocess.Popen(["firefox " + filename],shell=True)
        print_notification("You may task more exams to download from the list. Press any key to continue.")
    except:
        print_error("Failed to write exam to filesystem.")
        raise

def token_creator(s, il_id, course_id, moed, semester, year, site, download_page, pre_download_page, agent, token_template, file_template, found_scanned_exam):
    while len(course_id) != len("20119631"):
        course_id  = my_input("Please enter a valid Course ID (for example - 20119631):").strip()
    while moed not in ["1","2","3","4","11"]:
        moed       = my_input("Enter number of Moed (1/2/3/4, or 11 for Quiz (Bohan)):").strip()
    while semester not in ["1", "2", "3"]:
        semester   = my_input("Enter the number of Semester (1 = Fall / 2 = Spring / 3 = Summer):").strip()
    while len(year) != 4:    
        year       = my_input("Please enter the year of the exam/quiz:")
    try:
        # Perform download
        bohan_parameter = int(semester) * (int(moed) != 11 and int(moed) != 4 and int(moed) != 3) + 4 * (int(moed) == 11 or int(moed) == 4 or int(moed) == 3)
        token_str = token_template.format(student_id=il_id, course_id=course_id, semester=semester, year=year, moed=moed, bohan_parameter=bohan_parameter)
        filename = file_template.format(student_id=il_id, course_id=course_id, moed=moed)
        token = (base64.b64encode(token_str.encode('utf-8'))).decode('utf-8')
        data = {"toopen:2:1": "Download as PDF", "expars": token}
        print_notification("Using generated token {token}".format(token=token))
        print_notification("Downloading exam {0} ...".format(filename))
        print_notification("Starting exam download thread: Course ID {0}, {1}, {2} {3}.".format(course_id, msclrfrmt(moed,0), msclrfrmt(semester,1), year))
        t = threading.Thread(target=async_exam_downloader, \
            kwargs={'s':s, 'data': data, 'filename': filename, 'course_id': course_id, 'moed': moed, 'semester': semester, 'year': year, \
            'site':site, 'download_page':download_page, 'pre_download_page':pre_download_page, 'agent':agent})
        t.start()
        if not found_scanned_exam:
            print_notification("The download will run in the background and the exam will open automatically when it's done downloading. Please wait patiently and do not close this program yet!")
            print_notification("You may task more exams to download from the list while waiting.")
    except Exception as e:
        print_error("Failed to download exam: Course ID {0}, {1}, {2} {3}.".format(course_id, msclrfrmt(moed,0), msclrfrmt(semester,1), year))

def main():
    # Global variables
    max_login_attempts = 3
    site = "https://gezer1.bgu.ac.il/meser/"
    login_page = "login.php"
    pre_download_page = "tiflink.php"
    download_page = "exam.php"
    main_page = "main.php"
    token_template = "{student_id}:{year}:{semester}:0:{bohan_parameter}:{course_id}:1:{moed}"
    file_template = "{student_id}_{course_id}_{moed}.pdf"
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.41"
    exam_scanned_string = "appear after grades"
    bgu_creds_filename = "BGU_downloader.ini"
    course_list = []
    username, password = "", ""
    course, moed, semester, year = "", "", "", ""
    proper_course_list = []
    login_attempts = 0
    sub_list = ['<tr>','</tr>','</td>','<div>','</div>','<span>','</span>','<th>','</th>','<th scope="row" dir=ltr>','<div class="myBreak">','<span class="engText">','<td dir=ltr>','<div class="BR">','&nbsp;']
    found_scanned_exam, auto_login_answer, auto_download_answer = False, False, False
    never_ask_again = False # AMNESIA PARAMETER
    exam_id = -1
    data = {}
    
    # Gezer login
    s = requests.Session()
    while True:
        # Credentials (Don't worry I won't sell them :D)
        username, password, il_id = "","", ""
        if not os.path.isfile(bgu_creds_filename) or never_ask_again:
            auto_login_answer = False
            while len(username) == 0 or len(username) > 9999:
                username = my_input("Please enter your BGU username: ")
            while len(password) == 0 or len(password) > 9999:    
                password = my_input("Please enter your BGU password: ")
            while len(il_id) != 9:
                il_id = my_input("Please enter your Israeli ID number (9 digits): ")
        else:
            try:
                with open(bgu_creds_filename, 'r') as f:
                    username, password, il_id = [base64.b64decode(c.encode('utf-8')).decode('utf-8') for c in str(f.read()).split('&')]
                print_success("Succesfully read credentials from file " + bgu_creds_filename)
            except:
                print_error("Failed to read credentials from file " + bgu_creds_filename)    
        login_attempts += 1    
        # Login request to Gezer handling
        print_notification("Logging into Gezer system...")
        data = {'username': username, 'pass': password, 'id': il_id, 'ok': 'Next', 'isheb': 0}
        try:
            r = s.get(site + login_page, headers={'User-Agent': agent, 'Content-Type': 'application/x-www-form-urlencoded', 'Referer': 'https://gezer1.bgu.ac.il/meser/tiflink.php'})
            r = s.post(site + main_page, data=data, timeout=100)
        except:
            print_error("Login request timed out. Retrying...")
            continue
        if "entrance".lower() in r.text.lower():
            print_error("Failed to login.")
            try:
                with open(bgu_creds_filename, 'r') as f:
                    pass
                os.remove(bgu_creds_filename)
            except:
                pass
            # Prevent excessive login attempts (might crash site)
            if login_attempts == max_login_attempts:
                print_error("Failed to login {0} times, exiting...".format(max_login_attempts))
                any_key("Press any key to exit.")
                return
            continue
        print_success("Logged in to Gezer system successfully!")
        # Check if user is interested to ease his access at the expense of data security
        if not os.path.isfile(bgu_creds_filename) and not never_ask_again:
            print_notification("This program allows for saving your login credentials in a seperate file which will contain your information in base64 plaintext.")
            print_notification("This step is optional and might pose a security risk, so you should agree to it at your own discretion.")
            while auto_login_answer not in ['y','n']:
                auto_login_answer = my_input("Would you like to save your login credentials? [Y/N]").strip().lower()
            if auto_login_answer == 'y':
                auto_login_answer = ''
                while auto_login_answer not in ['y','n']:
                    auto_login_answer = my_input("Are you really sure you want to save your login credentials? [Y/N]").strip().lower()
            if auto_login_answer == 'y':
                try:
                    with open(bgu_creds_filename, 'w') as f:
                        f.write('&'.join([base64.b64encode(c.encode('utf-8')).decode('utf-8') for c in [username, password, il_id]]))
                    print_notification("Credentials saved to file " + bgu_creds_filename)
                except:
                    print_error("Failed to save credentials to file BGU_Scanned_Exam_Downloader_init.txt.")
            else:
                auto_login_answer = "" # Locked Distribution does not support amnesia behavior
                while auto_login_answer not in ['y','n']:
                    auto_login_answer = my_input("Would you like the program to never ask this again? [Y/N]").strip().lower()
                if auto_login_answer == 'y':
                    try:
                        file_code = ""
                        with open(os.path.basename(__file__), 'r') as f:
                            file_code = f.read()
                        file_code_list = file_code.split('# AMNESIA PARAMETER')
                        file_code_updated = file_code_list[0].replace('never_ask_again = False','never_ask_again = True') + '# AMNESIA PARAMETER' + '# AMNESIA PARAMETER'.join(file_code_list[1::])
                        with open(os.path.basename(__file__), 'w') as f:
                            f.write(file_code_updated)
                        print_success("Succesfully updated code to amnesia version. I will not ask you to save your credentials again!")
                    except:
                        print_error("Failed to update code to amnesia version.")
        break
        
    # Check to see if there are any scanned exams
    io_flag = False
    course_list = []
    for string in str(r.content,"ISO-8859-1").split('\n'):
        string = string.replace('<th scope="row" dir="ltr">','')
        if '<tr>' in string:
            io_flag = True
            temp_arr = []
        elif '</tr>' in string:
            io_flag = False
            course_list.append(temp_arr)
            continue
        if io_flag:
            temp = string
            for c in sub_list:
                temp = temp.replace(c,'').strip()
            temp_arr.extend([x for x in temp.split('<td>') if ('input' not in x and len(x)>=5)])
    response_str = "Scanned exams in gezer: "
    for course in course_list:
        if exam_scanned_string in course[5].lower() or (len(course) == 7 and ord('0')<=ord(course[6][-1::])<=ord('9')) or (len(course) == 6 and ord('0')<=ord(course[4][-1::])<=ord('9')):
        
            if exam_scanned_string in course[5].lower():
                found_scanned_exam = True
            
            course_id       = course[0].strip()
            course_name     = course[1].strip()
            semester        = course[2].lower().strip()
            moed            = course[3].lower().strip()
            year            = course[4][-4::].strip()
            
            # Format Semester, Year and Moed
            if not year.isnumeric():
                year = ""

            if "fall" in semester:
                semester = 1
            elif "spring" in semester:
                semester = 2
            elif "summer" in semester:
                semester = 3
            elif "irregular" in semester:
                semester = proper_course_list[-1]['Semester']
            else:
                semester = 0
                
            if "first" in moed:
                moed = 1
            elif "second" in moed:
                moed = 2
            elif "special" in moed:
                moed = 3
            elif "quiz" in moed:
                moed = 11
            else:
                moed = 0
            
            proper_course = {'Name': str(course_name), 'ID': str(course_id), 'Moed': str(moed), 'Semester': str(semester), 'Year': str(year), 'Exam Grade': 'XXX', 'Final Grade': 'XXX', 'Unpublished': False}
            proper_course['Unpublished'] = exam_scanned_string in course[5].lower()
            
            # Generate response and save to array
            if len(course) == 6 or len(course) == 7:
                proper_course['Exam Grade']  = str(course[5][-2::])
                try:
                    assert 0<=int(proper_course['Exam Grade'])<=150
                except:
                    proper_course['Exam Grade'] = 'XXX'
            if len(course) == 7:
                proper_course['Final Grade'] = str(course[6][-2::])
                try:
                    assert 0<=int(proper_course['Final Grade'])<=150
                except:
                    proper_course['Final Grade'] = 'XXX'
            if proper_course['Unpublished']:
                response_str += "\n    * {0}.{1}.{2} - {3}, Moed {4}, Semester {5} {6}".format(course_id[:3],course_id[3],course_id[4::], course_name, get_moed_str(moed), chr(ord('A')+semester-1), year)
            proper_course_list.append(proper_course)

    if not found_scanned_exam:
        response_str += "No unpublished scanned exams located."
    print_notification(response_str)
    if found_scanned_exam:  
        auto_download_answer = ''
        while auto_download_answer not in ['y','n']:
            auto_download_answer = my_input("Would you like the program to automatically download the new scanned exams? [Y/N]").strip().lower()
        if auto_download_answer == 'n':
            found_scanned_exam = False
        
    # Gezer download exam using course ID provided by student
    while True:
        course_id, moed, semester, year = "", "", "", ""
        if found_scanned_exam:
            exam_id += 1
            if exam_id >= len(proper_course_list):
                print_notification("Finished tasking automatic exam downloads. The downloads will run in the background and the exam will open automatically when it's done downloading.")
                any_key("Please wait patiently and do not close this program yet! When done, you may press any key to continue downloading exams manually.")
                found_scanned_exam = False
                exam_id = 0
                continue
            elif not proper_course_list[exam_id]['Unpublished']:
                continue
        else:
            if len(proper_course_list) != 0 and proper_course_list[0] != "":
                course_list_str = "Current year's graded or scanned exams in system: "
                for i in range(len(proper_course_list)):
                    course_name,course_id,moed,semester,year,grade,grade_final,unpublished = [proper_course_list[i][j] for j in ["Name", "ID", "Moed", "Semester", "Year", "Exam Grade", "Final Grade", "Unpublished"]]
                    course_list_str += "\n    ({9}) {0}.{1}.{2} - {3}, {4}, {5} {6}\n     | {7} | {8} |".format(course_id[:3],course_id[3],course_id[4::], course_name, msclrfrmt(chr(ord('A')+int(moed)-1),0), msclrfrmt(chr(ord('A')+int(semester)-1),1), year,msclrfrmt(grade,2),msclrfrmt(grade_final,3),i+1)
                print_notification(course_list_str)
                while True:
                    try:
                        exam_id  = my_input("Please enter the number of the exam to download [1-{0}/$=manual/*=ALL]:".format(len(proper_course_list))).strip()
                        if exam_id == '$':
                            break
                        if exam_id == '*':
                            break
                        if 0 <= int(exam_id)-1 < len(proper_course_list):
                            exam_id = int(exam_id)-1
                            break
                    except KeyboardInterrupt:
                        exit()
                    except Exception as e:
                        continue
            else:
                print_notification("No scanned exams found from this year. Switching to manual mode.")
                proper_course_list = [{'Name': "", 'ID': "", 'Moed': "", 'Semester': "", 'Year': "", 'Exam Grade': "", 'Final Grade': "", 'Unpublished': False}]
        if exam_id == '*':
            for exam_id in range(len(proper_course_list)):
                course_id = proper_course_list[exam_id]["ID"]
                moed = proper_course_list[exam_id]["Moed"]
                semester = proper_course_list[exam_id]["Semester"]
                year = proper_course_list[exam_id]["Year"]
                found_scanned_exam = True
                try:
                    t = threading.Thread(target=token_creator, kwargs={'s':s, 'il_id': il_id, 'course_id': course_id, 'moed': moed, 'semester': semester, 'year': year, 'site':site, 'download_page':download_page, 'pre_download_page':pre_download_page, 'agent':agent, 'token_template': token_template, 'file_template': file_template, 'found_scanned_exam': found_scanned_exam})
                    t.start()
                except:
                    pass
                found_scanned_exam = False
        elif exam_id == '$':
            course_id, moed, semester, year = "", "","",""
            try:
                token_creator(s, il_id, course_id, moed, semester, year, site, download_page, pre_download_page, agent, token_template, file_template, found_scanned_exam)
            except:
                pass
        else:
            course_id = proper_course_list[exam_id]["ID"]
            moed = proper_course_list[exam_id]["Moed"]
            semester = proper_course_list[exam_id]["Semester"]
            year = proper_course_list[exam_id]["Year"]
            try:
                t = threading.Thread(target=token_creator, kwargs={'s':s, 'il_id': il_id, 'course_id': course_id, 'moed': moed, 'semester': semester, 'year': year, 'site':site, 'download_page':download_page, 'pre_download_page':pre_download_page, 'agent':agent, 'token_template': token_template, 'file_template': file_template, 'found_scanned_exam': found_scanned_exam})
                t.start()
                time.sleep(1)
            except:
                pass
    return True

[print_error(base64.b64decode("SUYgWU9VIFBBSUQgTU9ORVkgRk9SIFRISVMgUFJPR1JBTSwgWU9VIEhBVkUgQkVFTiBTQ0FNTUVEIQ==".encode('utf-8')).decode('utf-8')) for i in range(3)]
main()

#################################################################################
