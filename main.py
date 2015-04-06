import smtplib
import os
import re
import csv
import mailSender
import argparse

"""
Run Example:
For a dry run (no email sent):
    python main.py -f "mock" -t "mockTable.csv" -a "pfiteraubrostean@science.ru.nl" --dry 
For an actual run:
    python main.py -f "mock" -t "mockTable.csv" -a "pfiteraubrostean@science.ru.nl"
    
Where mock is the directory with corrected assignments, mockTable.csv is a students table and
my email is the sender email.
"""

warnMsgs = []
studEntries = []
sendQueue = []

def prompt(prompt):
    return raw_input(prompt).strip()

def warn(warnMsg):
    global warnMsgs
    warnMsgs.append(warnMsg)
    
def log(logMsg):
    print logMsg 

def printWarnings():
    global warnMsgs
    for warnMsg in warnMsgs:
        print warnMsg

def parseGradingFolder(folderPath):
    for _, _, fileNames in os.walk(folderPath):
        for fileName in fileNames:
            studentInfos = re.findall("(s\d{7})",fileName)
            if len(studentInfos) == 0:
                warn("File name " + fileName +" cannot be split")
                continue
            for studentInfo in studentInfos:
                studentEmail = lookupStudentEmail(studentInfo)
                if studentEmail is not None:
                    queue(studentEmail, os.path.join(folderPath, fileName))
                else:
                    warn("Failed lookup for: " + studentInfo + ", assignment name:" + fileName)
                    
def queue(studentEmail, filePath):
    global sendQueue
    sendQueue.append([studentEmail, filePath])
                    
def lookupStudentEmail(sInfo):
    global studEntries
    retEmail = None
    for row in studEntries:
        matches = matchFilenamePartWithStudent(sInfo, row)
        studEmail = None
        if matches == True:
            studEmail = row["Email"]
            if retEmail is None:
                retEmail = studEmail
            else:
                warn("Double match for: " + sInfo) # + ", assignment name:" + fileName)
                retEmail = None
                break
    return retEmail  

def matchFilenamePartWithStudent(filePart, row):
    filePart = filePart.strip().lower()
   # print row
    if row["Role"] != "Student":
        return False
        
    # heuristics to match row with the name part
    matches = filePart == row["Username"]
#   matches = matches or (filePart in row["First Name"].lower())
#   matches = matches or (filePart in row["Last Name"].lower())
    return matches
        
    
def parseStudentTable(tablePath):
    with open(tablePath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            addEntry(row)
            
def addEntry(row):
    global studEntries
    studEntries.append(row)

def sendEmail(sender, fromAddress, studentEmail, subject, filePath, dry = True):
    log("Sending file " + filePath+ " to " +studentEmail)
    if dry == False:
        sender.setHeader(fromAddress, studentEmail, content = "", subject = subject)
        sender.sendPDF(filePath)
    
def sendAssignments(fromAddress, subject, dry = True):
    sender = None
    if dry == False:
        sender = mailSender.MailSender("smtp.science.ru.nl",25)
        sender.initSMTPSession()
    for studEmail, studAssignment in sendQueue:
        sendEmail(sender, fromAddress, studEmail, subject, studAssignment, dry)
    if dry == False:
        sender.closeSMTPSession()
     
def main():     
    parser = argparse.ArgumentParser(prog="Computer Network Aide", description="Tool that "
    "distributes corrected assignments in an assignment folder to students based on a csv containing "
    "the student contact details ")
    parser.add_argument("-f", "--folder", type=str, help="The path of the folder with corrected assignments", required=True)
    parser.add_argument("-t", "--table", type=str, help="The path to the csv file containing student records", default="cnTable.csv")
    parser.add_argument("-a", "--address", type=str, help="The email address of the sender", required=True)
    parser.add_argument("-s", "--subject", type=str, help="The title of the assignment mail", default="Your corrected assignment")
    parser.add_argument("-d", "--dry", help="Run it dry (without sending anything)", action="store_true")
    args = parser.parse_args()
    
    parseStudentTable(args.table)
    parseGradingFolder(args.folder)
    if len(warnMsgs) > 0:
        printWarnings()
        log("not sending until all warnings are fixed")
    else:
        sendAssignments(args.address, args.subject, args.dry)
        log("sent successfully")

if __name__ == "__main__":
    main()