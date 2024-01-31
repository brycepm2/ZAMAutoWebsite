from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from datetime import date
import sys
import os
import json

tgrwaURL = 'https://mybidmatch.outreachsystems.com/go?sub=0F7D0F07-33E5-427C-95F8-8C7F014C8924'

# reportNum: position of myBidMatch report to query (starts at 1 with most recent)
# rfpRange: list of rfp's to probe within the report does not need to be ordered
def getRFPReport(reportNum, rfpNumStart, rfpNumEnd):
    print('Scraping Text!!!')
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=service, options=options)
    # Open webPage from myBidMatch
    driver.get(tgrwaURL)
    # get first entry in table of reports
    reportTable = driver.find_element(By.CSS_SELECTOR,'body > table.data')
    myBidMatchReport = reportTable.find_element(By.CSS_SELECTOR,
                                              'tbody > tr:nth-child('+str(reportNum)+') > td:nth-child(1) > a')
    tabText = myBidMatchReport.text
    print(tabText)

    numRFPs = reportTable.find_element(By.CSS_SELECTOR,
                                       'tbody > tr:nth-child('+str(reportNum)+') > td:nth-child(2)').text

    if numRFPs == '0':
        print("No opportunities for this report!!!")
        driver.quit()
        return False, -1, -1
    else:
        # click on the table
        myBidMatchReport.click()

        rfpText = []
        # if no range specified do all rfps
        print("Setting rfpRange")
        # Case1: range is longer than number of RFPs
        if int(numRFPs) < (rfpNumEnd - rfpNumStart) + 1:
            rfpRange = [iRFP for iRFP in range(1,int(numRFPs)+1)]
        elif rfpNumStart == -1 and rfpNumEnd == -1:
            # run all RFPs from this report
            rfpRange = [iRFP for iRFP in range(1,int(numRFPs)+1)]
        else:
            # case 3: range works as is
            rfpRange = [iRFP for iRFP in range(rfpNumStart,rfpNumEnd+1)]
        rfpNumStart = rfpRange[0]
        rfpNumEnd = rfpRange[-1]

        for rfpNum in rfpRange:
            rfpTitle, rfpBody, rfpKeyWord, rfpLink = scrapeRFP(driver, rfpNum)
            rfpText.append([rfpTitle, rfpBody, rfpKeyWord, rfpLink])
            # need to go back to report page
            driver.back()

        driver.quit()
        print("Done textScraping!!!")
        return rfpText, rfpNumStart, rfpNumEnd

def scrapeRFP(driver, rfpNum):
    # get desired entry of table of RFPs
    rfpTable = driver.find_element(By.CSS_SELECTOR,'body > table.data')
    RFPEnt = rfpTable.find_element(By.CSS_SELECTOR,
                                        'tbody > tr:nth-child('+str(rfpNum)+') > td:nth-child(5) > a')
    rfpText = RFPEnt.text
    print(rfpText)

    # Click on the first rfp link
    RFPEnt.click()

    # Get link to rfp
    rfpLink = driver.current_url

    # get to rfp text
    rfpText = driver.find_element(By.CSS_SELECTOR, 'body > div.art-box')

    # Grab Full title of RFP
    rfpTitle = rfpText.find_element(By.CSS_SELECTOR, 'h4').text
    # Grab rfpText
    # NOTE: Top disclaimer text is also name <p>,
    # so I need to use full path here. That is annoying
    rfpBodyElems = driver.find_elements(By.CSS_SELECTOR, 'body > div.art-box > p')
    rfpBody = ''
    for iRfp in rfpBodyElems:
        rfpBody += iRfp.text
    # grab rfp keywords
    rfpKeyWordElem = rfpText.find_elements(By.CSS_SELECTOR, 'i')
    rfpKeyWord = []
    for iRfp in rfpKeyWordElem:
        rfpKeyWord.append(iRfp.text)

    print("Done with this RFP!!!")
    return rfpTitle, rfpBody, rfpKeyWord, rfpLink

from openai import OpenAI

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=os.getenv("OPENAI_API_KEY"),
)

def callGPT(prompt, model):
    today = date.today()
    d1 = today.strftime("%m/%d/%Y")
    sysPrompt = "You are a helpful assisstant. The current date is: "
    sysPrompt += d1
    response = client.chat.completions.create(
    messages=[
        {
          "role": "system",
          "content": sysPrompt,
        },
        {
          "role": "user",
          "content": prompt,
        }
    ],
    model=model,
    )
    return response

def callGPT_JSON(prompt, model):
    today = date.today()
    d1 = today.strftime("%m/%d/%Y")
    sysPrompt = "You are a helpful assisstant. The current date is: "
    sysPrompt += d1
    response = client.chat.completions.create(
    messages=[
        {
          "role": "system",
          "content": sysPrompt,
        },
        {
          "role": "user",
          "content": prompt,
        }
    ],
    model=model,
    response_format = {"type":"json_object"}
    )
    return response

# taken from openai.com on 11/17/2023
costInDic = {
      'gpt-4' : 0.03/1000,
      'gpt-4-1106-preview' : 0.01/1000,
      'gpt-3.5-turbo' : 0.0015/1000,
      'gpt-3.5-turbo-1106' : 0.0010/1000
}
costOutDic = {
      'gpt-4' : 0.06/1000,
      'gpt-4-1106-preview' : 0.03/1000,
      'gpt-3.5-turbo' : 0.002/1000,
      'gpt-3.5-turbo-1106' : 0.0020/1000
}

def calcCost(tokens, isPrompt, model):
    if isPrompt:
      costPerToken = costInDic[model]
    else:
      costPerToken = costOutDic[model]
    return costPerToken*tokens


from pylatex import Document, Section, Hyperref, Package
from pylatex.utils import escape_latex, NoEscape, bold

def hyperlink(url,text):
    text = escape_latex(text)
    return NoEscape(r'\href{' + url + '}{' + text + '}')

def writeOutput(doc, rfpTitle, output, rfpLink=None):
    with doc.create(Section(rfpTitle)):
        doc.append(output)
        if (rfpLink != None):
            doc.append("\n")
            doc.append("\n")
            doc.append(hyperlink(rfpLink, "Link to RFP"))

def writeOutputJSON(doc, rfpTitle, outputJSON, rfpLink=None):
    with doc.create(Section(rfpTitle)):
        for key in outputJSON:
            if key == "DueDate":
                doc.append(bold(key + ": " + str(outputJSON[key])))
            else:
                doc.append(key + ": " + str(outputJSON[key]))
            doc.append("\n")
            doc.append("\n")
        if (rfpLink != None):
            doc.append("\n")
            doc.append(hyperlink(rfpLink, "Link to RFP"))

def probeRFPs(rfpTexts, basePrompt, model, outPdfFullPath):
    # make latex doc to store output
    print("Probing RFPs")
    geometryOptions = {"tmargin" : "1cm", "lmargin": "1cm"}
    doc = Document(geometry_options = geometryOptions)
    doc.packages.append(Package('hyperref'))
    allRFPCost = 0.0
    for iRFP in rfpTexts:
        title = iRFP[0]
        body = iRFP[1]
        keyWords = iRFP[2][-1]
        link = iRFP[3]
        print(title)
        # print(keyWords)

        promptEnd = """\nThe RFP text is given below between
        the <<< >>> brackets

        <<<\n""" + body + "\n>>>"
        prompt = basePrompt + promptEnd
        response = callGPT(prompt, model)
        out = response.choices[0].message.content
        tokens = response.usage
        print("TokensIn: ", tokens.prompt_tokens)
        promptCost = calcCost(tokens.prompt_tokens, True, model)
        print("CostIn: ", promptCost)
        print("TokensOut: ", tokens.completion_tokens)
        responseCost = calcCost(tokens.completion_tokens, False, model)
        print("CostOut: ", responseCost)
        print('totalCost = ', promptCost + responseCost)
        allRFPCost += promptCost + responseCost
        print("Writing to output")
        writeOutput(doc, title, out, link)
    # add prompt to end of pdf
    writeOutput(doc, "Prompt", basePrompt)
    writeOutput(doc, "Model", model)
    # generate pdf output
    doc.generate_pdf(outPdfFullPath, clean_tex=False)
    print('Cost for all RFPs: ', allRFPCost)
    print('Done with analysis!!!')
    return allRFPCost

def sortAndWriteOutput(doc, allRFPData):
    # allRFPData - [title, JSON, link, costIn, costOut]
    # for each rfp
    # 1 - sort data by rating in JSON member
    # sorts by rating from lowest to highest
    sortedRFPs = sorted(allRFPData, key=lambda x: int(x[1]["Rating"]))
    print("Writing sorted output!!!")
    for iRFP in reversed(sortedRFPs):
        writeOutputJSON(doc, iRFP[0], iRFP[1], iRFP[2])

def probeRFPs_JSON(rfpTexts, basePrompt, model, outPdfFullPath):
    # make latex doc to store output
    print("Probing RFPs")
    geometryOptions = {"tmargin" : "1cm", "lmargin": "1cm"}
    doc = Document(geometry_options = geometryOptions)
    doc.packages.append(Package('hyperref'))
    allRFPCost = 0.0
    allRFPData = []
    for iRFP in rfpTexts:
        title = iRFP[0]
        body = iRFP[1]
        keyWords = iRFP[2][-1]
        link = iRFP[3]
        print(title)
        # print(keyWords)

        promptEnd = """\nThe RFP text is given below between
        the <<< >>> brackets

        <<<\n""" + body + "\n>>>"
        prompt = basePrompt + promptEnd
        response = callGPT_JSON(prompt, model)
        out = json.loads(response.choices[0].message.content)
        tokens = response.usage
        print("TokensIn: ", tokens.prompt_tokens)
        promptCost = calcCost(tokens.prompt_tokens, True, model)
        print("CostIn: ", promptCost)
        print("TokensOut: ", tokens.completion_tokens)
        responseCost = calcCost(tokens.completion_tokens, False, model)
        print("CostOut: ", responseCost)
        print('totalCost = ', promptCost + responseCost)
        allRFPCost += promptCost + responseCost
        print("Writing to output")
        allRFPData.append([title, out, link, promptCost, responseCost])
    sortAndWriteOutput(doc, allRFPData)
    # add prompt to end of pdf
    writeOutput(doc, "Prompt", basePrompt)
    writeOutput(doc, "Model", model)
    # generate pdf output
    doc.generate_pdf(outPdfFullPath, clean_tex=False)
    print('Cost for all RFPs: ', allRFPCost)
    print('Done with analysis!!!')
    return allRFPCost

def main():
    sTime = time.time()
    rfpStart = 1
    rfpEnd = 75 
    outPdfFullPath = '/home/brycepm2/ZAMAutoWebsite/Test/RFPReport_Test'
    rfpText, rfpStart, rfpEnd = getRFPReport(1, rfpStart, rfpEnd)

    model = 'gpt-4-1106-preview'

    basePrompt = """You are a structural engineer assessing posts for potential work. Posts can include requests for proposals (RFP), indefinite delivery indefinite quantity (IDIQ), requests for qualifications (RFQ), or other categories. The following pieces of information in the numbered list will help you assess if you should consider responding to the posts:

1. Your company specializes in structural engineering, structural analysis, and structural design of new buildings and renovation of existing buildings.

2. Your company does not provide construction or fabrication services. However, your company would still be interested in the post if it also includes work within the scope of your company's services.

3. Design-build or design-bid-build contracts are included in your company's services.

4. One of your specialties is design to mitigate Progressive Collapse.

5. One additional specialty of your company is performing ASCE 41 seismic evaluations of existing buildings, which includes the seismic evaluation and seismic risk analysis of buildings.

6. Your company is a structural engineering company for buildings and therefore does not provide design services for dams, harbors, flood risk structures, or other structures pertaining to bodies of water. However, your company would still be interested in the post if it also includes work within the scope of your company's services.

7. Your company is a small business that would be interested in work set aside for small businesses.

8. Your company is not a woman owned or veteran owned firm and would not be qualify for work set aside for woman or veteran owned businesses.

 

You need to summarize a post and output it in JSON format. The JSON must follow the rules set forth in the following lettered list:

a. Note the date when the response to the post is due. Return this as the value for "DueDate" in the JSON.

b. Note whether the post pertains to a IDIQ, RFP, RFQ, or something outside of these categories. Return this as the value for "Category" in the JSON.

c. Provide a 80 word summary of the work to be completed as part of the post. Return this as the value for "Summary" in the JSON.

d. Include a rating on a scale of 1 to 10 on how strongly you recommend that the company respond, where 1 indicates that the company should very likely not respond and 10 indicates that the company should very likely respond. Return this as a single integer in the value spot for "Rating" in the JSON. You MUST return a value from 1 to 10 for rating, if it is unknown report 1.

e. If the post does not have enough information to determine what kinds of services are being solicited, the summary should consist only of a recommendation for the user to manually view the post.     

Output the due date, category, summary, and rating of the post in JSON format. If you do not know the due date or category put "unknown" in the entry value. Make sure your response is only the text required for the JSON. Make the output JSON of your assessment as a JSON have the following format:
    {
    "DueDate" : "mm/dd/yyy",
    "Category": "string",
    "Summary": "string",
    "Rating": "int"
    }
"""
    allRFPCost = probeRFPs_JSON(rfpText, basePrompt, model, outPdfFullPath)
    eTime = time.time()
    print("Total time = ", (eTime - sTime))


if __name__ == '__main__':
    inputs = sys.argv
    main()
