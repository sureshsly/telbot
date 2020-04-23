""" A Telegram bot to retrieve stats from the covid19india.org site """
from sys import version_info
# if version_info.major > 2:
#     raise Exception('This code does not work with Python 3. Use Python 2')
import requests
import json
import operator
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

# Bot details


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
    for stateDict in data:
        if stateName == stateDict['state']:
            message = webPageLink + '\n' +  \
                'District'.ljust(14,' ') + '|Total Confirmed'.ljust(14,' ') + '\n'
            for district in stateDict['districtData']:
                districtName = district['district']
                confirmed = str(district['confirmed']).ljust(chars, ' ')
                delta = str(district['delta']['confirmed']).ljust(chars, ' ')
                message = message + districtName[0:10].ljust(14, '.') \
                    + '|' + confirmed + '\n'
            break
    message = '```' +  message + '```'
    return message


def _initStateCodes(filename):
    global _stateNameCodeDict
    with open(filename, 'r') as scFile:
        _stateNameCodeDict = json.load(scFile)


def start(update, context):
    """ start command """

    message = 'Use /help for a list of commands.'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def help(update, context):
    """ help command """

    message = "/India - Displays stats of all states\n" + \
              "/India <statecodes> - Displays stats of a <state>\n" + \
              "/statecodes - Displays codes of states that can be used as <state>\n" + \
              "/Overview - Displays stats of India \n"
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


def covid19india(update, context):
    """ Main command that retrieves and sends data """
    # Check for arguments
    stateName = "".join(context.args).strip().upper()
    if len(stateName) > 1:  # State data requested
        try:
            stateName = _stateNameCodeDict[stateName]
            message = _getMessageStatewise(stateName)
        except KeyError:
            message = 'Invalid state name. Use /statecodes to display codes.'
    else:  # National data requested
        message = _getMessageNational()

    context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                             parse_mode=ParseMode.MARKDOWN,
                             disable_web_page_preview=True)


def main():
    _initStateCodes('statecodes.json')
    updater = Updater(token='1113259481:', use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('India', covid19india))
    updater.dispatcher.add_handler(CommandHandler('statecodes', statecodes))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
