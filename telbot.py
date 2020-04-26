""" A Telegram bot to retrieve stats from the covid19india.org site  Codes are customised for my personal use"""
from sys import version_info
import requests
import json
import operator
from telegram.ext import Updater, Filters, MessageHandler
from telegram import ParseMode
import os
# Bot details

Token = os.environ['Token']

webPageLink = 'https://www.covid19india.org'

_stateNameCodeDict = {}


def _getSiteData(statewise=False):
    """ Retrieves data from api link """
    if statewise == False:
        link = 'https://api.covid19india.org/data.json'
    else:
        link = 'https://api.covid19india.org/v2/state_district_wise.json'
    try:
        data = requests.get(link).json()

        return data
    except:

        return None


def _getSortedStatewise(data):
    """ Returns ordered statewise data on the basis of max confirmed"""
    stateConfirmed = {}
    for state in data:
        totalConfirmed = 0
        for district in state['districtData']:
            totalConfirmed = totalConfirmed + int(district['confirmed'])
        stateConfirmed[state['state']] = totalConfirmed
    sortedData = sorted(stateConfirmed.items(), key=operator.itemgetter(1),
                        reverse=True)
    return(sortedData)


def _getSortedNational(data, keyBasis='active'):
    """ Returns ordered national data on the basis of max confirmed"""
    stateValue = {}
    for state in data['statewise']:
        stateName = str(state['state'])
        value = int(state[keyBasis])
        stateValue[stateName] = value
    orderedData = sorted(stateValue.items(), key=operator.itemgetter(1),
                         reverse=True)
    return(orderedData)


def _getMessageNational():
    """ Returns formatted data for printing """
    data = _getSiteData()
    orderedData = _getSortedNational(data)
    chars = 5  # Character spacing per column
    message = '\n' \
    + webPageLink \
    + '\n\n' \
    + 'REGION'.ljust(5, '.') + '|'\
    + 'CONF'.ljust(5, '.') + '|'\
    + 'RECO'.ljust(5, '.') + '|'\
    + 'DECE'.ljust(5, '.') + '|'\
    + 'ACTI'.ljust(5, '.') + '\n'\
    + '------|-----|-----|-----|-----\n'

    for state in orderedData:
        stateName = state[0]
        # Find rest of the values from dataset
        for stateDict in data['statewise']:
            if stateName == stateDict['state']:
                if stateName.strip() != 'Total':
                    stateName = stateName[0:6].ljust(6, ' ')
                else:
                    stateName = 'INDIA.'
                code = stateDict["statecode"].ljust(chars, ' ')
                active = stateDict["active"].ljust(chars, ' ')
                confirmed = stateDict["confirmed"].ljust(chars, ' ')
                deaths = stateDict["deaths"].ljust(chars, ' ')
                recovered = stateDict["recovered"].ljust(chars, ' ')
                # deltaconfirmed = state["deltaconfirmed"]
                # deltadeaths    = state["deltadeaths"]
                # deltarecovered = state["deltarecovered"]
        message = message + stateName + '|' \
            + confirmed + '|' + recovered + '|' \
            + deaths + '|' + active + '\n'
    message = '```' + message + '```'
    return message


def _getMessageStatewise(stateName):
    data = _getSiteData(statewise=True)
    chars = 8
    totalConfirmed = 0
    for stateDict in data:
        if stateName == stateDict['state']:
            message = webPageLink + '\n' +  \
                'District'.ljust(14,' ') + '|Total Confirmed'.ljust(14,' ') + '\n'
            for district in stateDict['districtData']:
                totalConfirmed = totalConfirmed + int(district['confirmed'])
                districtName = district['district']
                confirmed = str(district['confirmed']).ljust(chars, ' ')
                delta = str(district['delta']['confirmed']).ljust(chars, ' ')
                message = message + districtName[0:10].ljust(14, '.') \
                    + '|' + confirmed + '\n'
            break
    message =str(stateName)+' Total Cases : '+ str(totalConfirmed)+'\n' +'```' +  message + '```'
    return message

def _initStateCodes(filename):
    global _stateNameCodeDict
    with open(filename, 'r') as scFile:
        _stateNameCodeDict = json.load(scFile)


def start(update, context):
    """ start command """

    message = 'Use /help for a list of commands.'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def statecodes(update, context):
    """ Displays state codes """
    global _stateNameCodeDict
    message = ''
    for stateName in _stateNameCodeDict:
        if len(stateName) == 2:
            message = message + stateName + ': ' + \
                _stateNameCodeDict[stateName] + '\n'

    message = webPageLink + '```'+ '\n\nState codes\n\n' + message + '```'

    context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                             parse_mode=ParseMode.MARKDOWN,
                             disable_web_page_preview=True)


def state(update,context):
    """ Main command that retrieves and sends data """
    user_data = update.message.text.upper()

    if user_data != 'INDIA':
        try:
            stateName = _stateNameCodeDict[user_data]
            message = _getMessageStatewise(stateName)
        except KeyError:
            message = "Please enter INDIA or any two digit state codes \n For Exmple /SATATECODES...."
    else:
        message = _getMessageNational()
        
    context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                                 parse_mode=ParseMode.MARKDOWN,
                                 disable_web_page_preview=True)



def main():
    print('Code Testing')
    _initStateCodes('statecodes.json')
    updater = Updater(token=Token, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(Filters.command, statecodes))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, state, pass_user_data=True) )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

