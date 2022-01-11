import discord
from discord.ext import commands
import re
from discord.ext.commands import has_permissions, CheckFailure

# .       - Any Character Except New Line
# \d      - Digit (0-9)
# \D      - Not a Digit (0-9)
# \w      - Word Character (a-z, A-Z, 0-9, _)
# \W      - Not a Word Character
# \s      - Whitespace (space, tab, newline)
# \S      - Not Whitespace (space, tab, newline)
#
# \b      - Word Boundary
# \B      - Not a Word Boundary
# ^       - Beginning of a String
# $       - End of a String
#
# []      - Matches Characters in brackets
# [^ ]    - Matches Characters NOT in brackets
# |       - Either Or
# ( )     - Group
#
# Quantifiers:
# *       - 0 or More
# +       - 1 or More
# ?       - 0 or One
# {3}     - Exact Number
# {3,4}   - Range of Numbers (Minimum, Maximum)
#
#
# #### Sample Regexs ####
#
# [a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+


class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client

    def check_bad_words(self, content):
        curses = []
        for word in curses:
            pattern = re.compile(fr"\s{word[0]}{word[1:-1]}{word[-1]}")
            matches = pattern.findall(content)
            if matches:
                return matches

    def all_caps_check(self, contents):
        if contents == contents.upper():
            return True

    def check_links(self, content):
        pattern = re.compile(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
        )
        matches = pattern.findall(content)
        if matches:
            return True

    def check_invites(self, content):
        pattern = re.compile(r"(http|ftp|https)://[d][i][s][c][o][r][d]\.[g][g]/")
        mathces = pattern.findall(content)
        if mathces:
            return True
        else:
            return False


def setup(client):
    client.add_cog(Moderation(client))
