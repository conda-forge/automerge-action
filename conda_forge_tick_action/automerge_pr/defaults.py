"""
default parameters for the action
"""

# action always ignores itself
# github actions use the check_run API
IGNORED_CHECKS = ['regro-cf-autotick-bot-action']

# sets of states that indicate good / bad / neutral in the github API
NEUTRAL_STATES = ['pending']
BAD_STATES = ['failure', 'error']
